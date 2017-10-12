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
from geniemonitor.results import OK, WARNING, ERRORED, PARTIAL, CRITICAL

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
                            default='',
                            help='Specify which patterns to include when '
                                 'checking tracebacks')

        # exclude_pattern args
        # --------------------
        parser.add_argument('-exclude_pattern',
                            action="store",
                            default='',
                            help='Specify which patterns to exclude when '
                                 'checking tracebacks')

        # clean_up
        # --------
        parser.add_argument('-clean_up',
                            action="store",
                            default=False,
                            help='Specify whether to clear all warnings and '
                                 'tracebacks after reporting error')

        return parser


    def execution(self, device, execution_time):

        # Check device is connected
        if not device.is_connected():
            return ERRORED

        # Init
        status_= OK
        matched_patterns_dict = {}
        # Default keywords
        default_include = ['Traceback', 'ERROR', 'WARNING']

        # Execute command to check for tracebacks - timeout set to 5 mins
        output = device.execute(self.show_cmd, timeout=300)
        if not output:
            return ERRORED

        # Parse 'show logging logfile' output for keywords in include_pattern
        # Omit keywords specified in exclude_pattern
        include = self.args.include_pattern.split(', ') + default_include

        # Final list of keywords to check
        for item in include:
            if item in self.args.exclude_pattern.split(', '):
                include.remove(item)

        # Parse each line for keywords
        for pattern in include:
            matched_lines = []
            for line in output.splitlines():
                if re.search(pattern, line.strip(), re.IGNORECASE):
                    if 'patterns' not in matched_patterns_dict:
                        matched_patterns_dict['patterns'] = {}
                    if pattern not in matched_patterns_dict:
                        matched_patterns_dict['patterns'][pattern] = {}
                    matched_lines.append(line)
                    matched_patterns_dict['patterns'][pattern] = matched_lines
                    status_ += CRITICAL
                    logger.error("\nMatched pattern '{pattern}' in line:\n'{line}'".\
                                 format(pattern=pattern, line=line))

        # Log message to user
        if not matched_patterns_dict:
            logger.info("\n\n***** No traceback patterns matched *****\n\n")

        # Clear logging (if user specified)
        if self.args.clean_up:
            try:
                device.execute(self.clear_cmd)
            except Exception as e:
                logger.error("\nClear logging execution failed")
                status_ += ERRORED

        # Final status
        data = dict(object = device.name, status = status_, result = matched_patterns_dict)
        self.generate_result_meta(now = execution_time, **data)
        return status_