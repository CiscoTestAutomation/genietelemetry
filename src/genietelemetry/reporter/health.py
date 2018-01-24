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
        pass

    def stop(self, *args, **kwargs):
        # update job results
        self.job.results.update(self.consumer.get_summary_detail())

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
        pass

    def stop(self, *args, **kwargs):
        pass

    def nop(self, now):
        delta = timedelta(minutes=1)

        if not self.minute_report_at:
            self.minute_report_at = now

        if now - self.minute_report_at >= delta:
            self.minute_report_at = now
            logger.info(self.consumer.minute_report(device = self.device.name,
                                                    datetime_ = now))
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
        pass

    def stop(self, *args, **kwargs):
        pass

    def report(self, device, now, result, error = None):
        self.producer.produce(result = result,
                              device = device.name,
                              plugin = self.plugin.name,
                              error = error)