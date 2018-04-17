import logging
from io import TextIOBase

from ats.datastructures import AttrDict
from ats.utils.dicts import recursive_update

from .loader import ConfigLoader
from .plugins import PluginManager

# declare module as infra
__genietelemetry_infra__ = True

# module logger
logger = logging.getLogger(__name__)

class Configuration(object):
    '''Configuration

    genie telemetry configuration object. Core concept that allows genie
    telemetry to load configuration for user plugins, and as well allows device
    connections to be swapped with different port.

    '''

    def __init__(self, plugins = None):
        self._plugins = AttrDict()
        self.connections = AttrDict()
        self._loader = ConfigLoader()
        self.plugins = (plugins or PluginManager)()

    def load(self, config = None, devices = {}):
        logger.info('Loading genie.telemetry Configuration')
        # load configuration provided via input argument
        # -----------------------------
        if isinstance(config, (dict, str, TextIOBase)):
            self.update(self._loader.load(config))

        logger.info('Loading genie.telemetry Plugins')
        self.plugins.load(self._plugins)

        logger.info('Initializing genie.telemetry Plugins for Testbed Devices')
        for name, device in devices.items():
            self.plugins.init_plugins(name, device)

    def update(self, config):
        recursive_update(self._plugins, config.get('plugins', {}))
        recursive_update(self.connections, config.get('connections', {}))