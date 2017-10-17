import json
import logging
from pathlib import Path
from datetime import datetime

from .bases import Producer
from geniemonitor.results import ERRORED

# declare module as infra
__genie_monitor_infra__ = True

logger = logging.getLogger(__name__)

class DataProducer(Producer):

    def push_to_steam(self, data):

        if not isinstance(data, dict):
            return
        '''
        { datetime: datetime
          device: device
          status: health status
          context: plugin meta data }'''

        datetime_ = data.get('datetime', datetime.now())
        device = data.get('device', None)
        obj = dict(datetime = datetime_.isoformat(),
                   device = device,
                   status = data.get('status', ERRORED),
                   context = data.get('context', {}))
        self.runtime.context[datetime_] = obj

        file = Path(self.runtime.runinfo.runinfo_dir)
        file /= "Device.%s.meta.%s" % (device, datetime_.timestamp())
        with open(str(file), "a+") as yaml_file:
            json.dump(obj, yaml_file,
                      default = lambda o: o.__dict__,
                      indent = 4, sort_keys = True)
