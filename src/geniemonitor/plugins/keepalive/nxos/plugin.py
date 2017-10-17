''' 
GenieMonitor KeepAlive Plugin for NXOS.
'''
import logging
from random import randint

# GenieMonitor
from ..plugin import Plugin as BasePlugin
from geniemonitor.results import OK, HealthStatus

# module logger
logger = logging.getLogger(__name__)

class Plugin(BasePlugin):

    def execution(self, device, datetime):

        device.execute('\x0D', timeout=self.interval)
        rid = randint(1, 4)
        return HealthStatus(status = OK, meta = "randomized value %s"%rid)