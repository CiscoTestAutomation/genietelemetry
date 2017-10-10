'''
GenieMonitor Traceback Check Plugin.
'''

# ATS
from ats.utils import parser as argparse
from ats.datastructures import classproperty

# GenieMonitor
from geniemonitor.plugins.bases import BasePlugin

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
