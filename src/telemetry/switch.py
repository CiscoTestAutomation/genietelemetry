import os
import time
import logging

from pathlib import Path

from ats.datastructures import MetaClassFactory, classproperty
from ats.utils import parser as argparse
from .config.schema import import_threshold

# module logger
logger = logging.getLogger(__name__)

SECONDS_PER_DAY = 24*60*60

class Switch(object, metaclass = MetaClassFactory):

    @classproperty
    def parser(cls):
        '''
        base parser serving all switch implementations.
        '''

        parser = argparse.ArgsPropagationParser(add_help = False)
        parser.title = 'Monitor'
        
        parser.add_argument('-no_meta',
                                 action = "store_true",
                                 default = False,
                                 help = 'Specify to hide plugin result meta')

        parser.add_argument('-length',
                            action = "store",
                            default = '1s',
                            help = 'Specify monitor length, in XwYdZhPmQs '
                                   'format,\nX Weeks, Y Days, Z Hours, '
                                   'P Minutes, Q Seconds. \n'
                                   'ie: 5m20s, default to on demand request')

        parser.add_argument('-keep_alive',
                            action = "store_true",
                            default = False,
                            help = 'Specify keep monitoring alive\n'
                                   'Stop with Ctrl + C')
        return parser

    def __init__(self, runtime, length = None, no_meta = False,
                 keep_alive = False):

        # save input arguments
        self.runtime = runtime

        # parse arguments into self
        # (overwrite any of the above)
        self.parser.parse_args(namespace = self)

        self._length = length or self.length

        threshold = import_threshold(self._length)
        self.length = threshold.days * SECONDS_PER_DAY + threshold.seconds

        self.meta = not (no_meta or self.no_meta)

        self.keep_alive = keep_alive or self.keep_alive

    def monitor(self, device, plugin = None):
        return True

    def on(self, device, timer = 0):
        return self.length > timer or self.keep_alive