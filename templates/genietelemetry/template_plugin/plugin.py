'''
GenieTelemetry Plugin Template.
'''

from ats.utils import parser as argparse
from ats.datastructures import classproperty

# GenieTelemetry
from genietelemetry.plugins.bases import BasePlugin

class Plugin(BasePlugin):

    __plugin_name__ = 'Template Plugin'

    @classproperty
    def parser(cls):
        parser = argparse.ArgsPropagationParser(add_help = False)
        parser.add_argument('--argument_a',
                            help='example argument a',
                            default = None)
        parser.add_argument('--argument_b',
                            help='example argument b',
                            default = None)
        return parser