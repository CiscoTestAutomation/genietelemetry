# python
import os
import sys
import time
import getpass
import logging
import traceback
import multiprocessing
from datetime import datetime
from ipaddress import IPv4Interface, IPv6Interface, ip_address

from ats.topology import loader
from ats.utils.dicts import recursive_update
from ats.utils.schemaengine import Schema, Optional, Any, Or
from ats.utils.schemaengine import Use, And, Default, Fallback
from ats.utils.import_utils import import_from_name, translate_host

from genie.telemetry.config import (
    Configuration,
    PluginManager as BaseManager,
    DEFAULT_CONFIGURATION
)
from genie.telemetry.manager import Manager
from genie.telemetry.status import CRITICAL
from genie.telemetry.utils import str_or_list

# declare module as infra
__genietelemetry_infra__ = True

logger = logging.getLogger(__name__)

testbed_schema = {
    Optional('extends'): Use(str_or_list), # extends file or list of files

    'testbed': {
        Optional('name'): str,
        Optional('alias'): str,
        Optional('class'): Use(import_from_name),
        'tacacs': {
            'login_prompt': Default(str, 'login:'),
            'password_prompt': Default(str, 'Password:'),
            'username': Default(str, getpass.getuser()),
        },
        'passwords': {
            'tacacs': Default(str, 'lab'),
            'enable': Default(str, 'lab'),
            'line': Default(str, 'lab'),
            'linux': Default(str, 'lab'),
        },
        Optional('custom'): dict,
        Optional('servers'): {
            Any(): {
                Optional('server'): str,
                Optional('type'): str,
                Optional('address'): str,
                Optional('path'): str,
                Optional('username'): str,
                Optional('password'): str,
                Optional('laas'): {
                    Optional('port'): int,
                    Optional('notification_port'): int,
                    Optional('image_dir'): str,
                },
                Optional('custom'): dict,
            },
        },
        Optional('network'): Any(),
        Optional('iou'): {
            Optional('iou_flags'): str,
            Optional('iou'): str,
        },
        Optional('bringup'): {
            Optional('xrut'): {
                'sim_dir': str,
                'base_dir': str,
            },
        },
        Optional('testbed_file'): str, # not to be filled by hand
    },

    'devices': {
        Any() : {
            'type': str,
            Optional('class'): Use(import_from_name),
            Optional('alias'): str,
            Optional('region'): str,
            Optional('role'): str,
            Optional('os'): str,
            Optional('series'): str,
            Optional('model'): str,
            Optional('power'): str,
            Optional('hardware'): Any(),
            'tacacs': {
                'login_prompt': Fallback(str, 'testbed.tacacs.login_prompt'),
                'password_prompt':
                                Fallback(str, 'testbed.tacacs.password_prompt'),
                'username': Fallback(str, 'testbed.tacacs.username'),
            },
            'passwords': {
                'tacacs': Fallback(str, 'testbed.passwords.tacacs'),
                'enable': Fallback(str, 'testbed.passwords.enable'),
                'line': Fallback(str, 'testbed.passwords.line'),
                'linux': Fallback(str, 'testbed.passwords.linux'),
            },
            'connections': {
                Optional('defaults'): {
                    Optional('class'): Use(import_from_name),
                    Optional('alias'): str,
                    Optional('via'): str,
                },
                Any(): {
                    Optional('class'): Use(import_from_name),
                    Optional('protocol'): str,
                    Optional('ip'): And(Use(translate_host), ip_address),
                    Any(): Any(),
                },
            },
            Optional('clean'): dict,
            Optional('auto_bringup'): dict,
            Optional('custom'): dict,
            Any(): Any(),
        },
    },

    Optional('topology'): {
        Optional('links'): {
            Any(): {
                Optional('class'): Use(import_from_name),
                Optional('alias'): str,
                Any(): Any(),
            }
        },
        Any(): {
            'interfaces': {
                Any(): {
                    'type': str,
                    Optional('alias'): str,
                    Optional('class'): Use(import_from_name),
                    Optional('link'): str,
                    Optional('ipv4'): IPv4Interface,
                    Optional('ipv6'): IPv6Interface,
                    Any(): Any(),
                },
            },
        },
    },
}

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

        # init plugin interval dictionary
        for name, plugin in self._plugins.items():
            interval = plugin.get('interval', 30)
            self._plugin_interval.setdefault(interval, [])
            if name not in self._plugin_interval[interval]:
                self._plugin_interval[interval].append(name)

        # init plugin interval dictionary
        self._intervals = sorted(self._plugin_interval.keys())

class TimedManager(Manager):

    def __init__(self,
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


    def load_testbed(self, testbed_file):

        if not testbed_file:
            raise FileNotFoundError('Did you forget to provide a testbed file?')

        elif not os.path.isfile(testbed_file):
            raise FileNotFoundError("The provided testbed_file '%s' does not "
                                    "exist." % testbed_file)

        elif not os.access(testbed_file, os.R_OK):
            raise PermissionError("Testbed file '%s' is not accessible"
                                  % testbed_file)

        loader.schema = testbed_schema
        return loader.load(os.path.abspath(testbed_file))


    def get_device_plugins(self, device, interval):

        plugin_runs = {}

        # get list of plugin to be executed at this interval
        for plugin_name in self.plugins._plugin_interval[interval]:
            device_plugin = self.plugins._cache[plugin_name].get(device.name,
                                                                 {})
            if not device_plugin:
                continue
            plugin = device_plugin.get('instance', None)
            if not plugin:
                continue
            plugin_runs[plugin_name] = plugin

        return plugin_runs

    def start(self):
        try:
            interval = 0
            while True:

                interval += 1
                time_now = datetime.utcnow().strftime("%b %d %H:%M:%S UTC %Y")
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
            if interval % i:
                continue

            super().run('{} ({})'.format(tag, i), i)


    def call_plugin(self, device, plugins):

        is_connected = self.is_connected(device.name, device)
        if not is_connected:            
            connection = self.connections.get(device.name, {})
            timeout = connection.pop('timeout', self.connection_timeout)
            logger.info('Lost Connection - Attempt to Recover Connection '
                        'with Device ({})'.format(device.name))
            # best effort, attempt to connect at least once.
            try:
                device.connect(timeout=timeout,
                               **connection)
            except Exception as e:
                connection_failed = ('Lost Connection, failed to '
                                     'recover. exception: ({})'.format(str(e)))
            else:
                connection_failed = 'Lost Connection, failed to recover'
                is_connected = self.is_connected(device.name, device)
                logger.info('Connection Re-Established for '
                            'Device ({})'.format(device.name))

        results = dict()
        for plugin in plugins:
            # skip plugin execution if device isn't connected
            if is_connected:
                result = super().call_plugin(device, [plugin])
            else:
                # bad connection
                result = dict()
                plugin_name = getattr(plugin, 'name',
                                      getattr(plugin, '__plugin_name__',
                                              str(plugin)))

                execution = result.setdefault(plugin_name,
                                              {}).setdefault(device.name,{})
                execution['status'] = CRITICAL
                execution['result'] = {
                                        datetime.utcnow().isoformat():
                                        connection_failed
                                      }

            recursive_update(results, result)

            if hasattr(self.instance, 'post_call_plugin'):
                self.instance.post_call_plugin(device, result)

        return results