import os, sys
from ats.utils import parser as argparse
from ats.utils.dicts import recursive_update
from ats.datastructures import AttrDict, classproperty

from .loader import ConfigLoader
from .schema import validate_plugins
from .defaults import DEFAULT_CONFIGURATION

# declare module as infra
__genietelemetry_infra__ = True

# static vars
genietelemetry_GLOBAL_CONFIG = os.path.join(sys.prefix,
                                            'genietelemetry_config.yaml')

class Configuration(object):
    '''Configuration

    GenieTelemetry configuration object. Core concept that allows easypy to load 
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
        self.components = AttrDict()
        self.plugins = AttrDict()
        self._loader = ConfigLoader()
        
    def load(self, config = None):

        # start with the default configuration as basis
        self.update(self._loader.load(DEFAULT_CONFIGURATION))

        # load the global configuration
        # -----------------------------
        if os.path.exists(genietelemetry_GLOBAL_CONFIG):
            # load the global instance level configuration file
            self.update(self._loader.load(genietelemetry_GLOBAL_CONFIG))

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
        recursive_update(self.components, config.get('components', {}))
        recursive_update(self.plugins, config.get('plugins', {}))