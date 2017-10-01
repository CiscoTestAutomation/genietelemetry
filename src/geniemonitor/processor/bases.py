import logging
from enum import Enum
from datetime import datetime

from ats.datastructures import MetaClassFactory
from geniemonitor.results import ERRORED

logger = logging.getLogger(__name__)

class MonitorStage(Enum):
    Testbed = 1
    Testbed_Monitoring = 2
    Device = 3
    Device_Monitoring = 4
    Plugin = 5
    Plugin_Monitoring = 6


class Consumer(object, metaclass = MetaClassFactory):

    def __init__(self, runtime):
        self.runtime = runtime

    def start(self):
        pass

    def stop(self):
        pass

    def consume_from_steam(self, *args, **kwargs):
        raise NotImplementedError

    def peek_datetime_range(self, datetime, delta):
        raise NotImplementedError

    def minute_report(self, **kwargs):
        return self._report(minutes = 1, **kwargs)

    def hourly_report(self, **kwargs):
        return self._report(hours = 1, **kwargs)
    @property
    def health_summary(self):
        return self._report()

    def _report(self, datetime_ = None, **kwargs):
        raise NotImplementedError

    def get_detail_results(self, **kwargs):
        raise NotImplementedError

    def get_summary_detail(self, **kwargs):
        raise NotImplementedError

class Producer(object, metaclass = MetaClassFactory):

    def __init__(self, runtime, *args, **kwargs):
        self.runtime = runtime
        self.context = []

    def start(self):
        pass

    def stop(self):
        pass

    def push_to_steam(self, data):
        raise NotImplementedError

    def push_to_context(self, context):
        self.context.append(context)

    def pop_from_context(self, context):
        if not self.context[-1]:
            raise Exception("no context to pop")
        if context != self.context[-1]:
            raise Exception("wrong context type to pop")
        return self.context.pop()

    def monitor_testbed(self, name):
        logger.debug('Start monitoring testbed : %s'%name)
        self.push_to_context(MonitorStage.Testbed)

    def start_monitoring(self):
        logger.debug('Start connecting to devices')
        self.push_to_context(MonitorStage.Testbed_Monitoring)

    def stop_open_contexts(self):
        if len(self.context) > 2:
            logger.debug('Wrapping up monitoring')
            for x in self.context[2:]:
                logger.debug('Stop collecting status on : %s' % x.tag)
            self.context = self.context[:2]

    def stop_monitoring(self):
        logger.debug('Stop connecting to devices')
        self.pop_from_context(MonitorStage.Testbed_Monitoring)

    def release_testbed(self, name):
        logger.debug('Releasing testbed : %s'%name)
        self.pop_from_context(MonitorStage.Testbed)

    #---------------------

    def monitor_device(self, name):
        logger.debug('Start monitoring device : %s'%name)
        self.push_to_context(MonitorStage.Device)

    def start_collecting(self, name):
        logger.debug('Start collecting health status on device : %s'%name)
        self.push_to_context(MonitorStage.Device_Monitoring)

    def stop_collecting(self, name):
        logger.debug('Stop collecting health status on device : %s'%name)
        self.pop_from_context(MonitorStage.Device_Monitoring)

    def release_device(self, name):
        logger.debug('Releasing device : %s'%name)
        self.pop_from_context(MonitorStage.Device)

    #---------------------

    def execute_plugin(self, name):
        logger.debug('Start monitoring plugin : %s'%name)
        self.push_to_context(MonitorStage.Plugin)

    def start_collecting_status(self, name):
        logger.debug('Start collecting health status on plugin : %s'%name)
        self.push_to_context(MonitorStage.Plugin_Monitoring)

    def stop_collecting_status(self, name):
        logger.debug('Stop collecting health status on plugin : %s'%name)
        self.pop_from_context(MonitorStage.Plugin_Monitoring)

    def cleanup_plugin(self, name):
        logger.debug('Releasing plugin : %s'%name)
        self.pop_from_context(MonitorStage.Plugin)

    def produce(self, object_, result = ERRORED, **kwargs):
        self.push_to_steam(dict(datetime = datetime.now(), object = object_,
                                content = result, context = kwargs))