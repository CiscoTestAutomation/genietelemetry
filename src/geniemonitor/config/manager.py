
from ats.utils import parser as argparse
from ats.datastructures import AttrDict, classproperty

from .loader import ConfigLoader
from .defaults import DEFAULT_CONFIGURATION
from .schema import validate_plugins
from ats.utils.dicts import recursive_update

# declare module as infra
__genie_monitor_infra__ = True

class Configuration(object):
    '''Configuration

    GenieMonitor configuration object. Core concept that allows easypy to load 
    configuration for user plugins, and as well allows core components to 
    be swapped with different subclasses.

    '''

    @classproperty
    def parser(cls):
        parser = argparse.ArgsPropagationParser(add_help = False)
        parser.title = 'Configuration'

        # configuration args
        # ------------------
        parser.add_argument('-configuration',
                            type = argparse.FileType('r'),
                            metavar = 'FILE',
                            help = 'configuration yaml file for plugins and '
                                   'settings')

        return parser

    def __init__(self):
        self.core = AttrDict()
        self.plugins = AttrDict()
        self.connection = AttrDict()
        self.thresholds = AttrDict()

        self._loader = ConfigLoader()
        
    def load(self, config = None):

        # start with the default configuration as basis
        self.update(self._loader.load(DEFAULT_CONFIGURATION))

        # load dynamic runtime configuration
        # ----------------------------------
        args = self.parser.parse_args()

        if args.configuration:
            # load this run's configuration file
            self.update(self._loader.load(args.configuration))

        # finally, load configuration provided via input argument
        if config:
            self.update(self._loader.load(config))

    def update(self, config):
        recursive_update(self.core, config.get('core', {}))
        recursive_update(self.plugins, config.get('plugins', {}))
        recursive_update(self.connection, self.core.get('connection', {}))
        recursive_update(self.thresholds, self.core.get('thresholds', {}))

    def update_plugins(self, plugins = {}):
        self.plugins = AttrDict(validate_plugins(plugins))