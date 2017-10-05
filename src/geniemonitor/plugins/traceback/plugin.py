'''
GenieMonitor Traceback Plugin.
'''

# ATS
from ats.utils import parser as argparse
from ats.datastructures import classproperty

# GenieMonitor
from geniemonitor.plugins.bases import BasePlugin

class Plugin(BasePlugin):

    __plugin_name__ = 'Traceback Plugin'

    @classproperty
    def parser(cls):
        parser = argparse.ArgsPropagationParser(add_help = False)
        parser.title = 'Traceback'
        
        # include_pattern args
        # --------------------
        parser.add_argument('-include_pattern',
                            action="store_true",
                            default='Traceback',
                            help='Specify which patterns to include when '
                                 'checking tracebacks')

        # exclude_pattern args
        # --------------------
        parser.add_argument('-include_pattern',
                            action="store_true",
                            default='Warning',
                            help='Specify which patterns to exclude when '
                                 'checking tracebacks')

        # clean_up
        # --------
        parser.add_argument('-clean_up',
                            action="store_true",
                            default=False,
                            help='Specify whether to clear all warnings and '
                                 'tracebacks after reporting error')

        return parser
