import sys

from ats.utils import parser as argparse
from ats.easypy.plugins.bases import BasePlugin
from ats.utils.import_utils import import_from_name
from ats.log import managed_handlers

from .main import monitor, TelemetryRuntime

class Procesor(object):
    """Telemetry Processor

    This context manager based Processor class designed to allow user to invoke
    list of Telemetry plugin from their pyATS test script.

    Example:

        import logging
        from ats import aetest
        from telemetry.runner import TelemetryRunner

        logger = logging.getLogger(__name__)

        class HelloWorldTestcase(aetest.Testcase):

            @aetest.processors.pre(TelemetryRunner.processor_pre)
            @aetest.test
            def Hello(self):
                pass

            @aetest.test
            def Hello_with_Direct_Call(self):
                monitor = TelemetryRunner.processor_pre()
                status = monitor.result['testbed']['status']
                logger.info('monitoring result %s ' % status)

            @aetest.test
            def Hello_with_Context_Manager(self):
                with TelemetryRunner.processor_pre as processor:
                    status = processor.result['testbed']['status']
                    logger.info('monitoring result %s ' % status)

            @aetest.test
            def Hello_From_Execution(self):
                result = TelemetryRunner.processor_pre.execute():
                status = result['testbed']['status']
                logger.info('monitoring result %s ' % status)

    """

    def __init__(self, runner, pdb = False, runinfo_dir = None, plugins = {}):
        self.runner = runner
        self.plugins = plugins
        self.result = None
        self.pdb = pdb
        self.runinfo_dir = runinfo_dir

    def __call__(self):
        '''dunder __call__ method

            This method is to be automatically invoked by AEtest Harness if it's
            defined as pre/post/exception processor for AEtest.

        '''
        self.execute()
        return self

    def __enter__(self):
        # kick off an on-demand monitoring
        self.execute()

        return self

    def __exit__(self, ex_type, exc_value, tb):
        # re-raise the exception if there is any exception from telemetry
        # or context manager call
        exception = exc_value or self._get_exception_or_none()

        return True if not exception else False

    def _get_exception_or_none(self):
        if not self.result:
            return 'No monitor result was provided.'

        status = self.result.get('testbed', {}).get('status', 'errored')
        if str(status) != 'errored':
            return

        devices = self.result.get('devices', {})
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
            raise Exception('TelemetryRunner instance is missing')

        self.plugins = plugins or self.plugins or {}

        self.tasklog_handler = managed_handlers.tasklog
        self.current_log_file = managed_handlers.tasklog.logfile

        # kick off an on-demand monitoring
        self.result = monitor(runtime = TelemetryRuntime(
                                   configuration = self.runner.args.telemetry
                                   ),
                              plugins = self.plugins,
                              testbed_file = self.runner.testbed_file,
                              no_mail = self.runner.args.telemetry_no_mail,
                              pdb = self.pdb,
                              runinfo_dir = self.runinfo_dir)

        self.tasklog_handler.changeFile(self.current_log_file)

        exception = self._get_exception_or_none()
        if exception:
            raise Exception(exception)

        return self.result


class TelemetryRunner(BasePlugin):
    '''base TelemetryRunner Plugin

    Loads Telemetry Configuration file and populate pre/post processors for
    Easypy Job.

    Example:

        # Easypy config file

        plugins:
            TelemetryRunner:
              enabled: True
              module: telemetry.runner
              order: 1.0


        # Telemetry configuration file

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
                             --telemetry /path/to/telemetry/config.yaml
                             --telemetry_processor <python.import.path>
                             --telemetry_no_mail

    '''

    name = 'TelemetryRunner'
    parser = argparse.ArgumentParser(add_help = False)

    runner_grp = parser.add_argument_group('Telemetry Runner')

    runner_grp.add_argument('--telemetry', action = 'store', default = None)
    runner_grp.add_argument('--telemetry_processor', action = 'store',
                                                        default = Procesor)
    runner_grp.add_argument('--telemetry_no_mail', action = 'store_true',
                                                      default = False)

    def pre_task(self, task):

        # looks for telemetry configuration file and testbed instance
        if not self.args.telemetry or not task.runtime.testbed:
            return

        # initialize TelemetryRuntime
        self.telemetry_runtime = TelemetryRuntime(
                                         configuration = self.args.telemetry)

        plugins = self.telemetry_runtime.configuration.plugins
        processors = self.telemetry_runtime.configuration.processors

        # looks for testbed file, list of plugins and list of processors
        self.testbed_file = task.runtime.job.testbed_file
        if not plugins or not processors or not self.testbed_file:
            return

        # load processor class if customized
        self.processor_cls = self.args.telemetry_processor
        if isinstance(self.processor_cls, str):
            self.processor_cls = import_from_name(self.processor_cls)

        # get runinfo_dir information
        runinfo_dir = task.runtime.runinfo.runinfo_dir
        # get pdb information
        pdb = task.kwargs.get('pdb', False) or '-pdb' in sys.argv

        # load plugin list into processor and associate it with Runner class
        for processor_name, plugin_list in processors.items():
            monitor_plugins = {}
            for plugin_name, plugin_config in plugins.items():
                if plugin_name in plugin_list:
                    monitor_plugins.update({plugin_name : plugin_config})
            # initialize processor
            processor = self.processor_cls(self,
                                           pdb = pdb,
                                           runinfo_dir = runinfo_dir,
                                           plugins = monitor_plugins)
            setattr(self.__class__, processor_name, processor)
