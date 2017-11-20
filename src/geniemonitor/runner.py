
from ats.utils import parser as argparse
from ats.easypy.plugins.bases import BasePlugin
from ats.utils.import_utils import import_from_name

from .main import monitor, GenieMonitorRuntime

class Procesor(object):
    """GenieMonitor Processor

    This context manager based Processor class designed to allow user to invoke
    list of GenieMonitor plugin from their pyATS test script.

    Example:

        import logging
        from ats import aetest
        from geniemonitor.runner import GenieMonitorRunner

        logger = logging.getLogger(__name__)

        class HelloWorldTestcase(aetest.Testcase):

            @aetest.processors.pre(GenieMonitorRunner.processor_pre)
            @aetest.test
            def Hello(self):
                pass

            @aetest.test
            def Hello_with_Context_Manager(self):
                with GenieMonitorRunner.processor_pre() as processor:
                    status = processor.result['testbed']['status']
                    logger.info('monitoring result %s ' % status)

            @aetest.test
            def Hello_From_Execution(self):
                result = GenieMonitorRunner.processor_pre.execute():
                status = result['testbed']['status']
                logger.info('monitoring result %s ' % status)

    """

    def __init__(self, runner, plugins = {}):
        self.runner = runner
        self.plugins = plugins
        self.result = None

    def __call__(self):
        '''dunder __call__ method

            This method is to be automatically invoked by AEtest Harness

        '''
        return self.execute()

    def __enter__(self):
        # kick off an on-demand monitoring
        self.execute()

        return self

    def __exit__(self, ex_type, exc_value, tb):
        # re-raise the exception if there is any exception from geniemonitor
        # or context manager call
        exception = exc_value or self._get_exception_or_none()

        return True if not exception else False

    def _get_exception_or_none(self):

        if not self.result:
            return 'No monitor result was provided.'

        status = self.result.get('testbed', {}).get('status', 'errored')
        if status != 'ok':
            return 'Testbed status apparently to be %s' % status

        devices = self.result.get('devices', {}):
        if not devices:
            return

        errors = []
        for device, content in devices.items():
            for plugin, context in content.get('plugins', {}).items():
                error = context.get('error', None)
                if error:
                    timestamp, error = error
                    errors.append(error)

        return '\n'.join(errors)


    def execute(self, runner = None, plugins = {}):

        self.runner = runner or self.runner
        if not self.runner:
            raise Exception('GenieMonitorRunner instance is missing')

        self.plugins = plugins or self.plugins or {}

        # kick off an on-demand monitoring
        self.result = monitor(runtime = self.runner.geniemonitor_runtime,
                              plugins = self.plugins,
                              testbed_file = self.runner.testbed_file,
                              no_mail = self.runner.args.geniemonitor_no_email)

        exception = self._get_exception_or_none():
        if exception:
            raise Exception(exception)

        return self.result


class GenieMonitorRunner(BasePlugin):
    '''base GenieMonitorRunner Plugin

    Loads GenieMonitor Configuration file and populate pre/post processors for
    Easypy Job.

    Example:

        # Easypy config file

        plugins:
            GenieMonitorRunner:
              enabled: True
              module: geniemonitor.runner
              order: 1.0


        # GenieMonitor configuration file

        plugin:
            <your plugin name>:
                enable: <flag, optional, default True>
                interval: <interval in seconds, optional, default in 30seconds>
                module: <plugin.python.import.path>
                devices: [<list of allowed devices>]

        processors:
            <your processor name>: [<list of plugin name>]

        # easypy command

        bash$> easypy job.py -configuration /path/to/easypy/config.yaml
                             --geniemonitor /path/to/geniemonitor/config.yaml
                             --geniemonitor_processor <python.import.path>
                             --geniemonitor_no_mail

    '''

    name = 'GenieMonitorRunner'
    parser = argparse.ArgumentParser(add_help = False)

    runner_grp = parser.add_argument_group('GenieMonitor Runner')

    runner_grp.add_argument('--geniemonitor', action = 'store', default = None)
    runner_grp.add_argument('--geniemonitor_processor', action = 'store',
                                                        default = Procesor)
    runner_grp.add_argument('--geniemonitor_no_mail', action = 'store_true',
                                                      default = False)

    def pre_task(self, task):
        # looks for geniemonitor configuration file and testbed instance
        if not self.args.geniemonitor or not task.runtime.testbed:
            return

        # initialize GenieMonitorRuntime
        self.geniemonitor_runtime = GenieMonitorRuntime(
                                         configuration = self.args.geniemonitor)

        plugins = self.geniemonitor_runtime.configuration.plugins
        processors = self.geniemonitor_runtime.configuration.processors

        # looks for testbed file, list of plugins and list of processors
        self.testbed_file = task.runtime.job.testbed_file
        if not plugins or not processors or not self.testbed_file:
            return

        # load processor class if customized
        self.processor_cls = self.args.geniemonitor_processor
        if isinstance(self.processor_cls, str):
            self.processor_cls = import_from_name(self.processor_cls)

        # load plugin list into processor and associate it with Runner class
        for processor_name, plugin_list in processors.items():
            monitor_plugins = {}
            for plugin_name, plugin_config in plugins.items():
                if plugin_name in plugin_list:
                    monitor_plugins.update({plugin_name : plugin_config})
            # initialize processor
            processor = self.processor_cls(self, plugins = monitor_plugins)
            setattr(self.__class__, processor_name, processor)
