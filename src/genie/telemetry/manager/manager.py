# python
import os
import yaml
import logging
from datetime import datetime

# pcall
from ats.async import Pcall

# ATS
from ats.log.utils import banner
from ats.utils import parser as argparse
from ats.utils.dicts import recursive_update
from ats.datastructures import OrderableDict, classproperty

# configuration loader
from genie.telemetry.config.manager import Configuration
from genie.telemetry.status import OK, ERRORED
from genie.telemetry.utils import ordered_yaml_dump

# declare module as infra
__genietelemetry_infra__ = True

logger = logging.getLogger(__name__)

STATUS_KEYS = ('ok', 'warning', 'critical', 'errored', 'partial')

class Manager(object):

    report_file = 'telemetry.yaml'

    def __init__(self,
                 testbed,
                 instance = None,
                 runinfo_dir = None,
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

        self.instance = instance
        # load the configuration file
        self.testbed = testbed
        self.devices = testbed.devices

        # Instantiate configuration loader
        self.configuration = Configuration(plugins=plugins)
        self.configuration.load(config=configuration, devices=self.devices)

        self.results = OrderableDict()
        self.timeout = timeout
        self.runinfo_dir = runinfo_dir
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

    def get_device_plugins_status(self, device):

        return self.plugins.get_device_plugins_status(device.name)

    def set_device_plugin_status(self, device, plugin, status):

        plugin_name = getattr(plugin, 'name', getattr(plugin, '__plugin_name__',
                                                      str(plugin)))
        return self.plugins.set_device_plugin_status(device.name,
                                                     plugin_name,
                                                     status)

    def setup(self):
        for name, device in self.devices.items():
            connection = self.connections.get(name, {})
            timeout = connection.pop('timeout', self.connection_timeout)
            logger.info('Setting up connection to device ({})'.format(name))
            if not device.is_connected(alias=connection.get('alias', None)):
                # best effort, attempt to connect at least once.
                try:
                    device.connect(timeout=timeout,
                                   **connection)
                except Exception as e:
                    raise

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

        logger.info(banner('Telemetry Task ({})'.format(tag)))

        iargs = []

        for name, device in self.devices.items():

            plugins = self.get_device_plugins(device, *args, **kwargs)
            if not plugins:
                continue
            iargs.append((device, plugins))

        if not iargs:
            return

        # Pass device and corresponding plugins to Pcall
        #   child 1: args=(device object, plugin1)
        #   child 2: args=(device object, plugin2)
        self.p = Pcall(self.call_plugin,
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
            for name, devices in result.items():
                logger.info(banner(name))
                for device_name, device in devices.items():
                    status = device.get('status', OK)
                    p_status = str(status).capitalize()
                    p_result = ordered_yaml_dump(device.get('result', {}),
                                               default_flow_style=False)
                    logger.info(' - device ({})\n      - Status : {}\n'
                                '      - Result : \n{}'.format(device_name,
                                                               p_status,
                                                               p_result))

                    self.plugins.set_device_plugin_status(device_name,
                                                          name,
                                                          status)
                    if hasattr(self.instance, 'post_run'):
                        self.instance.post_run(device_name, name, device)

            recursive_update(results, result)

    def call_plugin(self, device, plugins):

        plugin_result = dict()

        for plugin in plugins:
            results = dict()
            plugin_name = getattr(plugin, 'name',
                                  getattr(plugin, '__plugin_name__',
                                          str(plugin)))

            execution = results.setdefault(plugin_name,
                                          {}).setdefault(device.name, {})

            try:

                call_result = plugin.execution(device)

            except Exception as e:
                status = ERRORED
                result = { datetime.utcnow().isoformat(): str(e) }
            else:
                status = call_result
                result = getattr(call_result, 'meta', {})

            # Example
            # {'crashdumps':{'N95_2':{'status': 'ok',
            #                         'result': { '2018-03-08T17:02:27.837458Z':
            #                                   '***** No patterns matched *****'}}}

            execution['status'] = status
            execution['result'] = result

            recursive_update(plugin_result, results)

        return plugin_result

    def _roll_up_status(self):

        statuses = []
        # rollup status
        for name in self.devices.keys():
            status = OK
            for item in self.plugins.get_device_plugins_status(name).values():
                if item is not None:
                    status += item
            statuses.append(status)
        return statuses

    @property
    def statuses(self):

        statuses = { k:0 for k in STATUS_KEYS }

        for health_status in self._roll_up_status():
            health_status = str(health_status).lower()

            statuses[health_status] += 1

        return statuses

    @property
    def status(self):
        return sum([OK] + self._roll_up_status())

    def finalize_report(self, runinfo_dir=None):
        for plugins in self.results.values():
            for devices in plugins.values():
                for device in devices.values():
                    device['status'] = str(device.get('status',
                                                      'OK')).capitalize()
        runinfo_dir = runinfo_dir or self.runinfo_dir
        if not runinfo_dir or not os.path.exists(runinfo_dir):
            logger.error('Unable to write yaml result to {}'.format(
                                                            self.report_file))
        else:
            report_file = os.path.join(runinfo_dir, self.report_file)
            with open(report_file, 'w') as yaml_file:
                ordered_yaml_dump(self.results,
                                  stream=yaml_file,
                                  default_flow_style=False)

        return ordered_yaml_dump(self.results,
                                 default_flow_style=False, default_style='')