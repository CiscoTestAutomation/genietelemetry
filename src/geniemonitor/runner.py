import sys
import functools

from ats.utils import parser as argparse
from ats.easypy.plugins.bases import BasePlugin

from .main import monitor, GenieMonitorRuntime
from .config.manager import Configuration

class GenieMonitorRunner(BasePlugin):
    '''GenieMonitorRunner Plugin

    Loads GenieMonitor Configuration file and populate pre/post processors for
    Easypy Job.

    '''

    name = 'GenieMonitorRunner'
    parser = argparse.ArgumentParser(add_help = False)

    runner_grp = parser.add_argument_group('GenieMonitor Runner')

    runner_grp.add_argument('--geniemonitor',
                            action = 'store',
                            default = None)
    runner_grp.add_argument('--geniemonitor_no_email',
                            action = 'store_true',
                            default = False)

    def pre_task(self, task):
        if not self.args.geniemonitor or not task.runtime.testbed:
            return
        self.geniemonitor_runtime = GenieMonitorRuntime(
                                         configuration = self.args.geniemonitor)
        plugins = self.geniemonitor_runtime.configuration.plugins
        processors = self.geniemonitor_runtime.configuration.processors

        self.testbed_file = task.runtime.job.testbed_file
        if not plugins or not processors or not self.testbed_file:
            return

        for processor_name, plugin_list in processors.items():
            monitor_plugins = {}
            for plugin_name, plugin_config in plugins.items():
                if plugin_name in plugin_list:
                    monitor_plugins.update({plugin_name : plugin_config})
            processor = self.wrap_method(monitor_plugins)
            setattr(GenieMonitorRunner, processor_name, processor)

    def wrap_method(self, plugins):
        def call_processor():
            return monitor(runtime = self.geniemonitor_runtime,
                           plugins = plugins,
                           testbed_file = self.testbed_file,
                           no_mail = self.args.geniemonitor_no_email)
        return functools.update_wrapper(call_processor, monitor)
