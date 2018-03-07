import os
import sys
import zipfile
import logging
from copy import copy
from operator import attrgetter
from abstract.magic import Lookup

from ats.utils.import_utils import import_from_name

# To be deleted after fixing plugins abstraction
from genietelemetry_libs.plugins.crashdumps import Plugin as crashdump_pluign
from genietelemetry_libs.plugins.tracebackcheck import Plugin as tracebackcheck_pluign

# module logger
logger = logging.getLogger(__name__)


class PluginManager(object):
    '''Plugin Manager class

    Instanciates, configures, manages and runs all easypy plugins. This is the
    main driver behind the easypy plugin system. Do not mock: may blow up.

    In any given process, there is only a single instance of PluginManager.
    '''

    def __init__(self):

        # list of plugin class instances
        self._plugins = dict()

        # dictionary of plugin-device abstraction cache pair
        self._cache = dict()

    def has_device_plugins(self, device):
        return any(device in c for c in self._cache.values())

    def get_device_plugins(self, device):
        return [c.get(device).get('instance',
            None) for c in self._cache.values() if device in c]

    def init_plugins(self, device):
        '''init_plugins

        initializing plugins for device
        '''

        device_name = getattr(device, 'name', device)
        logger.info('initializing plugins for %s' % device_name)

        for plugin_name, plugin in self._plugins.items():

            devices = plugin.get('devices', [])
            if devices and device_name not in devices:
                logger.debug('Skipping plugin %s for device %s' % (plugin_name,
                                                                   device_name))
                continue

            self._cache[plugin_name].setdefault(device_name, {})

            argv = copy(sys.argv[1:])
            plugin = self.load_plugin(device, **plugin)
            self._cache[plugin_name][device_name]['instance'] = plugin

            # parse plugin arguments
            # ----------------------
            # (saves arguments to plugin.args)
            plugin.parse_args(argv)
            self._cache[plugin_name][device_name]['args'] = plugin.args


    def load_plugin_cls(self, device, name=None, module=None):
        '''load_plugin_cls

        return loaded plugin abstraction class
        '''

        device_name = getattr(device, 'name', device)

        mod = getattr(module, '__abstract_pkg', None)
        if mod:
            if not getattr(device, 'os', None):
                raise AttributeError('%s attribute [os] is not defined'
                                                                % device_name)
            if not getattr(device, 'custom', None):
                raise AttributeError('%s custom abstraction is missing'
                                                                % device_name)
            try:
                module = Lookup.from_device(device, packages=dict(name=mod))
            except Exception:
                raise
        else:
            module = module

        # import pdb; pdb.set_trace()
        # Wei to fix abstarction call and that workaround to be deleted
        if name == 'tracebackcheck':
            plugin_cls = tracebackcheck_pluign
        elif name == 'crashdumps':
            plugin_cls = crashdump_pluign
        # try:
        #     plugin_cls = attrgetter('{}.Plugin'.format(name))(module)
        # except AttributeError:
        #     plugin_cls = attrgetter('Plugin')(module)

        # caching the plugin cls returned from abstraction magic
        self._cache[name][device_name]['cls'] = plugin_cls

        return plugin_cls


    def load_plugin(self, device, name=None, module=None, kwargs={}, **kw):
        '''load_plugin

        return loaded plugin
        '''
        logger.info(' - loading plugin %s' % name)

        plugin_kwargs = dict(**kwargs)

        plugin_cls = self.load_plugin_cls(device, name=name, module=module)

        return plugin_cls(**plugin_kwargs)


    def load(self, directory, data):
        '''loads plugins from dictionary data

        this api loads plugins defined in a specific dictionary format (same as
        that defined in load_from_yaml). It does the heavy-lifting of actual
        plugin module loading and instanciatation.

        Arguments
        ---------
            data (dict): dictionary data format, same as yaml schema

        Example
        -------
            PluginManater().load({'KeepAlive': {
                                         'enabled': True,
                                         'module': 'genietelemetry_libs.plugins',
                                         'interval': 60})

        Returns
        -------
            list of discovered and loaded plugins
        '''

        # sort plugin by order into list
        plugins = sorted(data.items())

        # loop over plugin configs and init interval dictionary
        for name, plugin in plugins:
            # Do we want to execute this plugins ?
            # If not enable, do not execute it
            if not plugin.get('enabled', False):
                logger.debug('Plugin %s is not enabled' % name)
                continue

            module = plugin.get('module', None)

            if os.path.isfile(module):
                extension = os.path.splitext(os.path.basename(module))
                fname, extension = extension
                working_path = os.path.join(directory, fname)
                # unzip it
                with zipfile.ZipFile(module, 'r') as zip_ref:
                    zip_ref.extractall(working_path)

                module = fname

            plugin['module'] = import_from_name(module)

            self._plugins[name] = plugin
            self._cache.setdefault(name, {})