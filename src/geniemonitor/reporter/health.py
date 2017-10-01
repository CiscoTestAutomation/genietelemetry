import logging
from datetime import datetime, timedelta

from .context import ContextReporter
from .bases import Reporter

logger = logging.getLogger(__name__)

class HealthReporter(Reporter):

    def __init__(self, consumer = None, producer = None, *args, **kwargs):

        # init base reporter
        super().__init__(*args, **kwargs)

        # consumer/producer
        self.consumer = consumer
        self.producer = producer

        
    def start(self):
        logger.debug("Creating instance to HealthReport runner")
        self.consumer.start()
        self.producer.start()

    def stop(self, *args, **kwargs):
        self.consumer.stop()
        self.producer.stop()
        logger.info(self.consumer.final_report())

    def child(self, job):

        name = job.name
        if not self.children_.get(name, None):
            self.children_[name] = HealthJobReporter(parent = self, job = job)

        return self.children_[name]

class HealthJobReporter(ContextReporter):

    def __init__(self, job, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.job = job
        self.minute_report_at = None

    def start(self):

        self.producer.monitor_testbed(name = self.job.name)

        self.producer.start_monitoring()

    def stop(self, *args, **kwargs):
        # stop all the open contexts of the child clients
        self.producer.stop_open_contexts()

        # Stop jobexecution
        self.producer.stop_monitoring()

        # update job results
        #self.job.results.update(self.client.get_summary_detail())

        self.producer.release_testbed(self.job.name)

    def child(self, device):
        name = device.name

        if not self.children_.get(name, None):
            self.children_[name] = DeviceHealthStatusReporter(parent = self,
                                                              device = device)

        return self.children_[name]

class DeviceHealthStatusReporter(ContextReporter):

    def __init__(self, device, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device = device
        self.minute_report_at = None

    def start(self):

        self.producer.monitor_device(name = self.device.name)

        self.producer.start_collecting(self.device.name)

    def nop(self, now):
        delta = timedelta(minutes=1)

        if not self.minute_report_at:
            self.minute_report_at = now

        if now - self.minute_report_at >= delta:
            self.minute_report_at = now
            logger.info(self.consumer.minute_report(device = self.device.name,
                                                    datetime_ = now))

    def stop(self, *args, **kwargs):

        # Stop jobexecution
        self.producer.stop_collecting(self.device.name)

        # update job results
        #elf.task.results.update(self.task.get_summary_detail())

        # Get AEreport results summary
        #self.job.results['summary'] = self.client.get_summary_test()

        # generate the report before suite context dies
        #self.job.diags_report = self.client.generate_diagnostics_report()

        self.producer.release_device(self.device.name)

        # write diags report
        #self.job.write_diags_report()

    def child(self, plugin):

        name = plugin.name
        if not self.children_.get(name, None):
            self.children_[name] = PluginReporter(parent = self,
                                                  plugin = plugin)

        return self.children_[name]

class PluginReporter(ContextReporter):

    def __init__(self, plugin, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plugin = plugin

    def start(self):
        self.producer.execute_plugin(name = self.plugin.name)

        self.producer.start_collecting_status(self.plugin.name)

    def report(self, object_, now, result, error = None):
        context = self.plugin.results_meta.get(now, None)
        self.producer.produce(result = result,
                              object_ = object_.name,
                              plugin = self.plugin.name,
                              context = context,
                              error = error)

    def stop(self, *args, **kwargs):

        # Stop jobexecution
        self.producer.stop_collecting_status(self.plugin.name)

        # update job results
        #self.plugin.results.update(self.plugin.get_summary_detail())

        # Get AEreport results summary
        #self.job.results['summary'] = self.client.get_summary_test()

        # generate the report before suite context dies
        #self.job.diags_report = self.client.generate_diagnostics_report()

        self.producer.cleanup_plugin(self.plugin.name)

        # write diags report
        #self.job.write_diags_report()
