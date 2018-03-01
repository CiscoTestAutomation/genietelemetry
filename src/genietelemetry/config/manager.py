import os, sys
from ats.utils import parser as argparse
from ats.utils.dicts import recursive_update
from ats.datastructures import AttrDict, classproperty

from .loader import ConfigLoader
from .schema import validate_plugins
from .defaults import DEFAULT_CONFIGURATION
from .plugins import PluginManager

# declare module as infra
__genietelemetry_infra__ = True

# static vars
GLOBAL_CONFIG = os.path.join(sys.prefix, 'genietelemetry_config.yaml')

class Configuration(object):
    '''Configuration

    GenieTelemetry configuration object. Core concept that allows genietelemetry
    to load configuration for user plugins, and as well allows manager
    to be swapped with different subclasses.

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

    def __init__(self, plugins = None):
        self.manager = AttrDict()
        self._plugins = AttrDict()
        self._loader = ConfigLoader()
        self.plugins = (plugins or PluginManager)()
        
    def load(self, config = None):

        # start with the default configuration as basis
        self.update(self._loader.load(DEFAULT_CONFIGURATION))

        # load the global configuration
        # -----------------------------
        if os.path.exists(GLOBAL_CONFIG):
            # load the global instance level configuration file
            self.update(self._loader.load(GLOBAL_CONFIG))

        # load dynamic runtime configuration
        # ----------------------------------
        args = self.parser.parse_args()

        if args.configuration:
            # load this run's configuration file
            self.update(self._loader.load(args.configuration))

        # finally, load configuration provided via input argument
        if config:
            self.update(self._loader.load(config))

    def init_plugins(self, directory, plugins_dir=None, devices=[]):

        if not self.plugins:
            return

        if plugins_dir:
            directory = os.path.join(directory, plugins_dir)

        # append to sys path for module importing
        sys.path.append(directory)

        self.plugins.load(directory, self._plugins)

        for device in devices:
            self.plugins.init_plugins(device)

    def update(self, config):
        recursive_update(self.manager, config.get('manager', {}))
        recursive_update(self._plugins, config.get('plugins', {}))