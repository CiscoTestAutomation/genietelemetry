''' 
GenieTelemetry HelloWorld Plugin for IOSXE.
'''
import logging
from datetime import datetime

# GenieTelemetry
from ..plugin import Plugin as BasePlugin
from genie.telemetry.status import OK, ERRORED

logger = logging.getLogger(__name__)

class Plugin(BasePlugin):

    # Define your plugin's core execution logic in this method.
    # If 'device' is specified as a function argument, the current device
    # object is provided as input to this action method when called.
    # Similar idea when 'execution_datetime' is specified as a function
    # argument, the plugin execution datetime is provided as input to this
    # action method.
    def execution(self, device):

        # Plugin parser results are always stored as 'self.args'
        if self.args.print_timestamp:
            self.execution_start = datetime.datetime.now()
            logger.info('Current time is: %s' % self.execution_start)

        logger.info('Execution %s: Hello World!' % device.name)

        return OK("Plugin completed")