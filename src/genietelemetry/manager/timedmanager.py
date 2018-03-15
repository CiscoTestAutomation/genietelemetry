# python
import os
import sys
import time
import logging
import traceback
import multiprocessing
from datetime import datetime

from ats.topology import loader
from ats.utils.dicts import recursive_update

from genietelemetry.config import (
    Configuration,
    PluginManager as BaseManager,
    DEFAULT_CONFIGURATION
)
from genietelemetry.manager import Manager

logger = logging.getLogger(__name__)

class PluginManager(BaseManager):
    '''Plugin Manager class

    In any given process, there is only a single instance of PluginManager.
    '''

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # dictionary of interval-plugins pair
        self._plugin_interval = dict()

        # list of plugin intervals
        self._intervals = list()

    def load(self, data):

        super().load(data)

        for name, plugin in self._plugins.items():
            interval = plugin.get('interval', 30)
            self._plugin_interval.setdefault(interval, [])

        # init plugin interval dictionary
        self._intervals = sorted(self._plugin_interval.keys())
        for name, plugin in self._plugins.items():

            interval = plugin.get('interval', 30)
            for i in self._intervals:

                if interval % i != 0 or name in self._plugin_interval[i]:
                    continue

                self._plugin_interval[i].append(name)


class TimedManager(Manager):

    def __init__(self,
                 instance = None,
                 testbed={},
                 testbed_file=None,
                 configuration={},
                 configuration_file=None,
                 **kwargs):

        if not testbed and not testbed_file:
            raise FileNotFoundError('Did you forget to provide a testbed file?')

        super().__init__(testbed or self.load_testbed(testbed_file),
                         configuration=(configuration or \
                                        configuration_file or \
                                        DEFAULT_CONFIGURATION),
                         plugins=PluginManager,
                         **kwargs)

        self.instance = instance


    def load_testbed(self, testbed_file):

        if not testbed_file:
            raise FileNotFoundError('Did you forget to provide a testbed file?')

        elif not os.path.isfile(testbed_file):
            raise FileNotFoundError("The provided testbed_file '%s' does not "
                                    "exist." % testbed_file)

        elif not os.access(testbed_file, os.R_OK):
            raise PermissionError("Testbed file '%s' is not accessible"
                                  % testbed_file)

        return loader.load(os.path.abspath(testbed_file))


    def get_device_plugins(self, device, interval):

        plugin_runs = []

        # get list of plugin to be executed at this interval
        for plugin in self.plugins._plugin_interval[interval]:
            device_plugin = self.plugins._cache[plugin].get(device.name, {})
            if not device_plugin:
                continue
            plugin = device_plugin.get('instance', None)
            if not plugin:
                continue
            plugin_runs.append(plugin)

        return plugin_runs

    def start(self):
        try:
            interval = 0
            while True:

                interval += 1
                time_now = datetime.utcnow().isoformat()
                self.run(time_now, interval)
                time.sleep(1)

        except SystemExit:
            logger.warning('System Exit detected...')
            logger.warning('Aborting run & cleaning up '
                           'as fast as possible...')

        except KeyboardInterrupt:
            # ctrl+c handle
            # -------------
            logger.warning('Ctrl+C keyboard interrupt detected...')
            logger.warning('Aborting run & cleaning up '
                           'as fast as possible...')

        except Exception as e:
            message= ''.join(traceback.format_exception(*sys.exc_info()))
            logger.error('exception occurred {}'.format(message.strip()))


    def run(self, tag, interval):
        '''run plugins

        Arguments
        ---------
            device (device): current executing device
            interval (integer): current execution interval

        '''

        for i in self.plugins._intervals:

            # skip if not it's turn
            if interval % i != 0:
                continue

            super().run(tag, i)


    def call_plugin(self, device, *plugins):

        results = dict()
        # skip if device isn't connected
        if not self.is_connected(device.name, device):
            for plugin in plugins:
                execution = results.setdefault(plugin.name,
                                              {}).setdefault(device.name, {})
                execution['status'] = 'critical'
                execution['result'] = {}
            return results

        for plugin in plugins:
            result = super().call_plugin(device, plugin)

            recursive_update(results, result)

            if hasattr(self.instance, 'post_call_plugin'):
                self.instance.post_plugin_call(result)

        return results