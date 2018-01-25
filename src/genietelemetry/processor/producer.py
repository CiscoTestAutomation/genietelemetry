import json
import logging
from pathlib import Path
from datetime import datetime

from .bases import Producer
from genietelemetry.results import ERRORED

# declare module as infra
__genietelemetry_infra__ = True

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
        context = data.get('context', {})
        status = data.get('status', ERRORED)
        obj = dict(datetime = datetime_.isoformat(),
                   device = device,
                   status = status,
                   context = context)
        self.runtime.context[datetime_] = obj
        # get plugin name
        plugin = context.get('plugin', 'Task').replace(" ", "_")
        # create meta filename
        filename = '.'.join(map(str,[device, plugin, str(status).upper(),
                                     datetime_.timestamp()]))
        # filter invalid filename
        filename = ''.join( x for x in filename if (x.isalnum() or x in '._-'))
        file = Path(self.runtime.runinfo.runinfo_dir)
        file /= filename
        with open(str(file), "a+") as yaml_file:
            json.dump(obj, yaml_file, default = lambda o: o.__dict__,
                      indent = 4, sort_keys = True)
