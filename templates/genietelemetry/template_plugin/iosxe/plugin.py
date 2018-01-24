''' 
GenieTelemetry Template Plugin for IOS-XE.
'''
import logging

# GenieTelemetry
from ..plugin import Plugin as BasePlugin
from genietelemetry.results import OK, ERRORED, HealthStatus

# module logger
logger = logging.getLogger(__name__)

class Plugin(BasePlugin):

    def execution(self, device, datetime):

        result = device.execute('show version')
        if not result:
            return ERRORED

        return HealthStatus(status = OK, meta = result)