''' 
GenieMonitor Traceback Check Plugin for NXOS.
'''

# Python
import time
import logging
from datetime import datetime

# GenieMonitor
from ..plugin import Plugin as BasePlugin
from geniemonitor.utils import is_hitting_threshold
from geniemonitor.results import OK, WARNING, ERRORED, PARTIAL

from parsergen import oper_fill_tabular

# module logger
logger = logging.getLogger(__name__)

class Plugin(BasePlugin):

    def execution(self, device, execution_time):

        # Check device is connected
        if not device.is_connected():
            return ERRORED

        # Init
        status_= OK
        traceback_found = False
        # Default keywords: 'Traceback', 'ERROR' & 'WARNING'
        default_include = ['Traceback', 'ERROR', 'WARNING']

        # Increase timeout buffer incase of large output

        # Execute 'show logging logfile'
        output = device.execute('show logging logfile')
        if not output:
            return ERRORED

        # Parse 'show logging logfile' output for keywords in include_pattern
        # Omit keywords specified in exclude_pattern
        include = self.args.include_pattern + default_include

        # Final list of keywords to check
        for item in include:
            if item in self.args.exclude_pattern:
                include.remove(item)

        # Parse each line for keywords
        for line in output.splitlines():
            for pattern in include:
                if pattern in line.strip():
                    traceback_found = True
                    logger.error("\nFound pattern '{pattern}' in"
                                 " 'show logging logfile' output".\
                                 format(pattern=pattern))

        # Log message to user
        if not traceback_found:
            logger.info("\n\n***** No traceback patterns matched *****\n\n")

        # Clear logging (if user specified)
        if self.args.clean_up:
            try:
                device.execute('clear logging logfile')
            except Exception as e:
                logger.error("\nClear logging execution failed")
                status_ += ERRORED

        # Reset timeout buffer

        # Final status
        data = dict(object = device.name, status = status_, result = output)
        self.generate_result_meta(now = execution_time, **data)
        return status_