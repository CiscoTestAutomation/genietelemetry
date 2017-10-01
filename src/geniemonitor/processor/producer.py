import logging
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
          object: device
          content: health status
          context: plugin meta data }'''

        datetime_ = data.get('datetime', datetime.now())

        obj = dict(datetime = datetime_.isoformat(),
                   object = data.get('object', None),
                   content = data.get('content', ERRORED),
                   context = data.get('context', {}))

        self.runtime.context[datetime_] = obj