'''
GenieMonitor Traceback Check Plugin.
'''

# Python
import re
import time
import logging
from datetime import datetime

# ATS
from ats.utils import parser as argparse
from ats.datastructures import classproperty

# GenieMonitor
#from ..plugin import Plugin as BasePlugin
from geniemonitor.plugins.bases import BasePlugin
from geniemonitor.results import OK, WARNING, ERRORED, PARTIAL

# module logger
logger = logging.getLogger(__name__)


class Plugin(BasePlugin):

    __plugin_name__ = 'Traceback Check Plugin'

    @classproperty
    def parser(cls):
        parser = argparse.ArgsPropagationParser(add_help = False)
        parser.title = 'Traceback Check'
        
        # include_pattern args
        # --------------------
        parser.add_argument('-include_pattern',
                            action="store",
                            default=[],
                            help='Specify which patterns to include when '
                                 'checking tracebacks')

        # exclude_pattern args
        # --------------------
        parser.add_argument('-exclude_pattern',
                            action="store",
                            default=[],
                            help='Specify which patterns to exclude when '
                                 'checking tracebacks')

        # clean_up
        # --------
        parser.add_argument('-clean_up',
                            action="store_true",
                            default=True,
                            help='Specify whether to clear all warnings and '
                                 'tracebacks after reporting error')

        return parser


    def execution(self, device, execution_time):

        # Check device is connected
        if not device.is_connected():
            return ERRORED

        # Init
        status_= OK
        traceback_found = False
        # Default keywords
        default_include = ['Traceback', 'ERROR', 'WARNING']

        # Execute command to check for tracebacks - timeout set to 5 mins
        output = device.execute(self.show_cmd, timeout=300)
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
                if re.search(pattern, line.strip(), re.IGNORECASE):
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
                device.execute(self.clear_cmd)
            except Exception as e:
                logger.error("\nClear logging execution failed")
                status_ += ERRORED

        # Final status
        data = dict(object = device.name, status = status_, result = output)
        self.generate_result_meta(now = execution_time, **data)
        return status_