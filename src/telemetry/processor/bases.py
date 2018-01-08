import logging
from enum import Enum
from datetime import datetime

from ats.datastructures import MetaClassFactory
from telemetry.results import ERRORED, HealthStatus

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

    def start(self):
        pass

    def stop(self):
        pass

    def push_to_steam(self, data):
        raise NotImplementedError

    def produce(self, device, result = ERRORED, **kwargs):
        self.push_to_steam(dict(datetime = datetime.now(), device = device,
                                status = result, context = kwargs))
