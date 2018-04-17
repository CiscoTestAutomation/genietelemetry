''' 
genie telemetry Template Plugin for NXOS.
'''
import logging

# genie telemetry
from ..plugin import Plugin as BasePlugin
from genie.telemetry.status import OK, ERRORED

# module logger
logger = logging.getLogger(__name__)

class Plugin(BasePlugin):

    def execution(self, device):

        result = device.execute('show version')
        if not result:
            return ERRORED("'show version' returns no result")

        return OK(result)