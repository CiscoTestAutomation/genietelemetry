# python
import logging
from datetime import datetime

# pcall
from ats.async import Pcall

# ATS
from ats.utils import parser as argparse
from ats.datastructures import classproperty
from ats.utils.dicts import recursive_update

# configuration loader
from genie.telemetry.config.manager import Configuration

logger = logging.getLogger(__name__)

class Manager(object):

    def __init__(self,
                 testbed,
                 results = dict(),
                 configuration = None,
                 plugins = None,
                 timeout = 300,
                 connection_timeout = 10):
        '''
        initialize the manager class by loading the plugin configuration file
        and initiating the corresponding plugins.
        '''

        # parse configuration file
        configuration = configuration or self.parser.parse_args().configuration

        if not configuration:
            raise AttributeError("'--genietelemetry <path to config_file.yaml>"
                " is missing.")

        # load the configuration file
        self.testbed = testbed
        self.devices = testbed.devices

        # Instantiate configuration loader
        self.configuration = Configuration(plugins=plugins)
        self.configuration.load(config=configuration, devices=self.devices)

        self.results = results
        self.timeout = timeout        
        self.connection_timeout = connection_timeout
        self.p = None

    @classproperty
    def parser(cls):
        '''
        store the module corresponding arguments.
        '''
        parser = argparse.ArgsPropagationParser(add_help = False)
        parser.title = 'Genie Telemetry'

        # GenieTelemetry config file
        # --------------------------
        parser.add_argument('--genietelemetry',
                            type = argparse.FileType('r'),
                            metavar = 'FILE',
                            dest='configuration',
                            help='GenieTelemetry configuration file')
        return parser

    @property
    def plugins(self):
        return self.configuration.plugins

    @property
    def connections(self):
        return self.configuration.connections

    def get_device_plugins(self, device, *args, **kwargs):

        return self.plugins.get_device_plugins(device.name)

    def setup(self):

        devices = []
        for name, device in self.devices.items():
            connection = self.connections.get(name, {})
            timeout = connection.pop('timeout', self.connection_timeout)
            logger.info('setting up connection to device {}'.format(name))
            if not device.is_connected(alias=connection.get('alias', None)):
                # best effort, attempt to connect at least once.
                try:
                    device.connect(timeout=timeout,
                                   **connection)
                except Exception as e:
                    logger.error('failed to connect to device {}'.format(name))
                else:
                    logger.info('connection established')
                    devices.append(name)
        return devices

    def is_connected(self, name, device):
        connection = self.connections.get(name, {})
        return device.is_connected(alias=connection.get('alias', None))

    def terminate(self):

        if self.p and any(self.p.livings):
            self.p.terminate()


    def takedown(self):

        self.terminate()

        for name, device in self.devices.items():
            connection = self.connections.get(name, {})
            alias = connection.get('alias', None)
            if not device.is_connected(alias=alias):
                continue
            try:
                device.disconnect(alias=alias)
            except Exception as e:
                logger.error('failed to disconnect from device {} {}'
                             ''.format(name, connection))


    def run(self, tag, *args, **kwargs):
        '''run

        use pcall to run parallel device/plugins run and return back the result
        as a dictionary of testcase and the corresponding plugin/device result.
        '''

        cargs = []
        iargs = []

        for name, device in self.devices.items():

            plugins = self.get_device_plugins(device, *args, **kwargs)
            if not plugins:
                continue

            cargs.append(device)
            iargs.append(plugins)

        # Pass device and corresponding plugins to Pcall
        #   child 1: args=(device object, plugin1)
        #   child 2: args=(device object, plugin2)
        self.p = Pcall(self.call_plugin,
                       cargs=cargs,
                       iargs=iargs,
                       timeout=self.timeout)
        try:

            self.p.start()
            self.p.join()

        except:
            self.terminate()

        # Associate testcase name with the plugin results
        # Example
        # {'TriggerSleep.uut':
        #     {'crashdumps':
        #         {'N95_2': {'status': 'ok',
        #                    'result':{'2018-03-01T21:17:00.631819Z':
        #                                 'No cores found!'}},
        #          'N95_1': {'status': 'critical',
        #                    'result':{'2018-03-01T21:25:28.699888Z':
        #                                 "Core dump generated for process "
        #                                 "'m6rib' at 2018-03-01 21:23:00"}}},
        #      'tracebackcheck':
        #         {'N95_2': {'status': 'ok',
        #                    'result':{'2018-03-01T21:17:02.985530Z':
        #                                 '***** No patterns matched *****'}},
        #          'N95_1': {'status': 'ok',
        #                    'result':{'2018-03-01T21:17:02.461916Z':
        #                                 '***** No patterns matched *****'}}}
        #     },
        #  'common_setup':
        #     {'crashdumps':
        #         {'N95_2': {'status': 'ok',
        #                    'result':{'2018-03-01T21:16:13.206079Z':
        #                                 'No cores found!'}},
        #          'N95_1': {'status': 'critical',
        #                    'result':{'2018-03-01T21:25:28.699888Z':
        #                                 "Core dump generated for process "
        #                                 "'m6rib' at 2018-03-01 21:23:00"}}},
        #      'tracebackcheck':
        #         {'N95_2': {'status': 'ok',
        #                    'result':{'2018-03-01T21:16:15.538308Z':
        #                                 '***** No patterns matched *****'}},
        #          'N95_1': {'status': 'ok',
        #                    'result':{'2018-03-01T21:16:14.981929Z':
        #                                 '***** No patterns matched *****'}}}}
        # }

        key = getattr(tag, 'uid', tag)
        results = self.results.setdefault(key, {})

        for result in getattr(self.p, 'results', []) or []:
            if not isinstance(result, dict):
                continue
            recursive_update(results, result)

    def call_plugin(self, device, plugin):

        plugin_name = getattr(plugin, 'name',
                              getattr(plugin, '__plugin_name__', str(plugin)))

        result = dict()

        execution = result.setdefault(plugin_name,
                                      {}).setdefault(device.name, {})

        try:

            call_result = plugin.execution(device)

        except Exception as e:
            status = 'errored'
            result = { datetime.utcnow().isoformat(): str(e) }
        else:
            status = getattr(call_result, 'name', 'ok')
            result = getattr(call_result, 'meta', {})

        # Example
        # {'crashdumps':{'N95_2':{'status': 'ok',
        #                         'result': { '2018-03-08T17:02:27.837458Z':
        #                                   '***** No patterns matched *****'}}}

        execution['status'] = status
        execution['result'] = result

        return result