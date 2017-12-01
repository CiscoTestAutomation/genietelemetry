import os
import sys
import copy
import time
import logging

from operator import attrgetter
from datetime import datetime, timedelta

from multiprocessing import Process, Queue

from abstract.magic import Lookup

from .stages import PluginStage, Scope
from .bases import BasePlugin
from ..utils import unzip_and_import

from geniemonitor.results import ERRORED, OK, HealthStatus
from ats.utils.import_utils import import_from_name

# declare module as infra
__genie_monitor_infra__ = True

# module logger
logger = logging.getLogger(__name__)

def pmqueuer(execution_list, plugin = None, stage = None):

    if execution_list is None or not plugin:
        return

    if not stage:
        stage = PluginStage.execution

    execution_list.append([stage, plugin])

def pmprocessor(execution_list, task, plugins, pdb):

    # workaround for enabling pdb under child process
    if pdb:
        sys.stdin = open('/dev/stdin')

    while task.runtime.switch.on(task.device):
        try:
            task.device.connect()

            if not execution_list:
                continue

            stage, plugin_name = execution_list.pop(0)
            if stage == PluginStage.finished:
                return

            for plugin in plugins:
                if plugin.name != plugin_name:
                    continue
                logger.info('Executing plugin : %s - interval [%s]s' % 
                                                 (plugin.name, plugin.interval))
                if not task.device.is_connected():
                    plugin.status = HealthStatus(status = ERRORED)
                    logger.info(' - Device Not Connected [ Skipping ]')
                    continue
                plugin.status = HealthStatus(status = OK)
                try:
                    # run the plugin
                    plugin.run(obj = task.device, stage = stage)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except Exception as e:
                    # handle error
                    task.error_handler(e)
                    task.runtime.producer.push_to_steam(
                                        dict(datetime = datetime.now(),
                                             object = task.device.name,
                                             content = ERRORED,
                                             plugin = plugin.name,
                                             context = { 'error': task.error }))
                    continue

        except (KeyboardInterrupt, SystemExit):
            # stop execution, clear up the list
            while execution_list:
                execution_list.pop(0)
            return
        except Exception as e:
            # handle error
            task.error_handler(e)
            task.runtime.producer.push_to_steam(
                                        dict(datetime = datetime.now(),
                                             object = task.device.name,
                                             content = ERRORED,
                                             context = { 'error': task.error }))

            continue


class PluginManager(object):
    '''Plugin Manager class

    Instanciates, configures, manages and runs all easypy plugins. This is the
    main driver behind the easypy plugin system. Do not mock: may blow up.

    In any given process, there is only a single instance of PluginManager.
    '''

    def __init__(self, runtime):
        self._runtime = runtime

        # list of plugin class instances
        self._plugins = list()

        # dictionary of parsed known argument/values
        self.plugin_args = {}

        # list of plugin instances
        self._stacks = {}

        # list of plugin device filter
        self._plugin_device_filter = {}


    def __iter__(self):
        '''PluginManager iterator

        makes PluginManager object instances iterable: looping over all
        instanciated internal plugins. 
        '''
        return iter(self._plugins)

    def __len__(self):
        return len(self._plugins)

    def __getitem__(self, key):
        '''
        Access a plugin by name or by position
        '''

        # integer/slice -> list.__getitem__
        if isinstance(key, int) or isinstance(key, slice):
            return self._plugins.__getitem__(key)

        # try dict.__getitem__ style using key as name
        for plugin in self.get_plugins():
            if plugin.name == key:
                return plugin
        else:
            raise ValueError('No such plugin known: %s' % key)

    def run(self, obj, stage, now):
        '''run plugin stage

        main function called by executions to run all plugins in order, for any
        given stage.

        The PluginManager.run() controls the execution order of plugins. When
        any errors are encountered during a plugin's PRE-stage run, the 
        corresponding POST-stage section of all plugin ran so far will be 
        run, and the plugin engine will raise exception and error out.

        This ensures proper clean-up behavior of plugins, and as well make sure
        nothing is run execution in case a plugin is not running correctly.

        If a plugin action method has "execution" argument, the current
        executing execution object will be automatically provided as function
        argument.

        Arguments
        ---------
            obj (device): current executing execution object
            stage (str): plugin stage to be run

        '''
        # catch any bad-stages
        stage = PluginStage(stage)

        # execution stage -> run in order of definition
        plugins = self._stacks.get(obj.name, [])
        
        queue = obj.task.plugin_executions

        # run plugin one by one
        for plugin in plugins:
            if not plugin.last_execution:
                plugin.last_execution = now
            else:
                interval = timedelta(seconds=plugin.interval)
                if now - plugin.last_execution < interval:
                    continue
                plugin.last_execution = now

            # queue up plugin execution
            pmqueuer(queue, plugin.name, stage)


    def prepare_plugins(self):

        logger.info('Unpacking and importing plugins')
        logger.info('-' * 80)

        working_dir = self._runtime.runinfo.runinfo_dir
        for index, plugin in enumerate(self._plugins):

            name, module, plugin_kwargs, basecls = plugin

            if isinstance(module, str) and '/' in module:

                logger.info(' - unpacked plugin file : %s' % module)
                name, module, basecls = unzip_and_import(working_dir, module)
                self._plugins[index] = (name, module, plugin_kwargs, basecls)

            logger.info(' - imported module : %s' % name)

        logger.info('-' * 80)

    def init_plugins(self, obj):

        name = getattr(obj, 'name', obj)
        logger.info('initializing plugins for %s' % name)

        plugins = self._plugins
        self._stacks[name] = []

        argv = copy.copy(sys.argv[1:])

        for plugin in plugins:

            plugin_name = plugin[0]
            devices = self._plugin_device_filter.get(plugin_name, [])
            # if devices filter exists, skip such device is not included, skip
            if devices and name not in devices:
                logger.info('Skipping plugin %s for device %s' % (plugin_name,
                                                                  name))
                continue

            plugin = self.load_plugin(obj, plugin)

            # parse plugin arguments
            # ----------------------
            # (saves arguments to plugin.args)
            plugin.parse_args(argv)

            if plugin.args:
                # update plugin manager arguments
                # ----------------------
                # (saves arguments to plugin_args)
                self.plugin_args.update(vars(plugin.args))

            self._stacks[obj.name].append(plugin)

    def load_plugin(self, obj, plugin):
        '''load_plugin
            
        return loaded plugin
        '''
        name, plugin_module, plugin_kwargs, _ = plugin
        
        logger.info(' - loading plugin %s' % name)

        plugin_kwargs['module'] = plugin_module
        mod = getattr(plugin_module, '__abstract_pkg', None)
        if mod:
            if not getattr(obj, 'os', None):
                raise AttributeError('%s attribute [os] is missing in yaml'
                                                                          % obj)
            if not getattr(obj, 'custom', None): 
                raise AttributeError('%s custom abstraction is missing in '
                                     'yaml' % obj)
            try:
                module = Lookup.from_device(obj, packages={ name: mod })
            except Exception:
                raise
        else:
            module = plugin_module
        try:
            plugin_cls = attrgetter('{}.Plugin'.format(name))(module)
        except AttributeError:
            plugin_cls = attrgetter('Plugin')(module)

        return plugin_cls(runtime = self._runtime, **plugin_kwargs)

    def get_device_plugins(self, device = None):
        if not device:
            return []
        return self._stacks.get(device.name, [])

    def get_plugins(self, stage = None):
        if not stage:
            plugins = [item for sub in self._stacks.values() for item in sub]
        else:
            stage_name = BasePlugin.fmt_stage_name(stage)
            plugins = self._stacks.get(stage_name, [])
        return plugins

    def errored_plugins(self, stage = None):
        '''errored_plugins
            
        return list of plugins that errored out when they ran.
        '''
        if not stage:
            plugins = [item for sub in self._stacks.values() for item in sub]
        else:
            stage_name = BasePlugin.fmt_stage_name(stage)
            plugins = self._stacks.get(stage_name, [])
        return [p for p in set(plugins) if p.has_errors(stage)]

    def has_errors(self, stage = None):
        '''errors
        
        True/False for if any plugin errored out
        '''
        if not stage:
            plugins = [item for sub in self._stacks.values() for item in sub]
        else:
            stage_name = BasePlugin.fmt_stage_name(stage)
            plugins = self._stacks.get(stage_name, [])
        return any(plugin.has_errors(stage) for plugin in plugins)

    def load(self, data):
        '''loads plugins from dictionary data

        this api loads plugins defined in a specific dictionary format (same as
        that defined in load_from_yaml). It does the heavy-lifting of actual
        plugin module loading and instanciatation.

        Arguments
        ---------
            data (dict): dictionary data format, same as yaml schema

        Example
        -------
            PluginManater().load({'CESMonitoringPlugin': {
                                         'enabled': True,
                                         'module': 'ats.easypy.plugins',
                                         'order': 60})

        Returns
        -------
            list of discovered and loaded plugins
        '''

        self._plugins = []
        self._stacks = {}

        # sort plugin by order into list
        plugins = sorted(data.items())

        # loop over config and instantiate
        for name, config in plugins:
            # Do we want to execute this plugins ?
            # If not enable, do not execute it
            if not config['enabled']:
                logger.debug('Plugin %s is not enabled' % name)
                continue

            # get the plugin module
            plugin_module = config['module']

            # get the plugin kwargs
            plugin_kwargs = config['kwargs']

            # get the plugin basecls
            base_cls = config.get('basecls', None)

            plugin = (name, plugin_module, plugin_kwargs, base_cls)

            # store plugin in order
            self._plugins.append(plugin)

            self._plugin_device_filter[name] = config.get('devices', [])

        logger.debug('Instantiated the following plugins: %s' % plugins)
