''' 
GenieMonitor Template Plugin for IOS-XR.
'''
import logging

# GenieMonitor
from ..plugin import Plugin as BasePlugin
from geniemonitor.results import OK, ERRORED

# module logger
logger = logging.getLogger(__name__)

class Plugin(BasePlugin):

    def execution(self, device, datetime):

        if not device.is_connected():
            return ERRORED

        result = device.execute('show version')
        if not result:
            return ERRORED

        data = dict(object = device.name, status = OK, result = result)
        self.generate_result_meta(now = datetime, **data)
        return OK