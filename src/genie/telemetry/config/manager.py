from ats.datastructures import AttrDict
from ats.utils.dicts import recursive_update

from .loader import ConfigLoader
from .plugins import PluginManager

# default configuration for GenieTelemetry
# (removed file loading for simplicity)
DEFAULT_CONFIGURATION = '''
plugins:
    crashdumps:
        interval: 60
        enabled: True
        module: genietelemetry_libs.plugins.crashdumps
    tracebackcheck:
        interval: 60
        enabled: True
        module: genietelemetry_libs.plugins.tracebackcheck

'''

class Configuration(object):
    '''Configuration

    GenieTelemetry configuration object. Core concept that allows genietelemetry
    to load configuration for user plugins, and as well allows manager
    to be swapped with different subclasses.

    '''

    def __init__(self, plugins = None):
        self._plugins = AttrDict()
        self.connections = AttrDict()
        self._loader = ConfigLoader()
        self.plugins = (plugins or PluginManager)()

    def load(self, config = None, devices = {}):

        # finally, load configuration provided via input argument
        if isinstance(config, (dict, str)):
            self.update(self._loader.load(config))

        else:            
            # start with the default configuration as basis
            self.update(self._loader.load(DEFAULT_CONFIGURATION))

        self.plugins.load(self._plugins)

        for name, device in devices.items():
            self.plugins.init_plugins(name, device)

    def update(self, config):
        recursive_update(self._plugins, config.get('plugins', {}))
        recursive_update(self.connections, config.get('connections', {}))