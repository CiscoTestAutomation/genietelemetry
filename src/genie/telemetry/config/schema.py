
from ats.utils.schemaengine import Or, Any, Use, Optional
from ats.utils.exceptions import SchemaError
from ats.utils.import_utils import import_from_name

# declare module as infra
__genietelemetry_infra__ = True

def validate_plugins(data):
    try:
        assert type(data) is dict

        for plugin, config in data.items():
            assert type(config) is dict

            assert 'module' in config

            assert type(config['module']) is str

            # by default all plugins are always enabled and 30 seconds interval
            config.setdefault('enabled', True)
            config.setdefault('interval', 30)
            config.setdefault('devices', []) # plugin device filter

            assert type(config['devices']) is list

            # build the plugin arguments
            # If user given any arg not defined in the yaml file,
            # it is passes as kwargs to the __init__ of the plugins
            kwargs = {}

            for key, value in list(config.items()):
                if key in ('enabled', 'module', 'interval', 'devices'):
                    continue

                kwargs[key] = config.pop(key)

            # Basically, plugin name = class name.
            # let's find it inside the loaded module
            config['module'] = import_from_name(config['module'])
            config['kwargs'] = kwargs
            config['name'] = plugin

    except Exception as e:
        raise SchemaError("Invalid genietelemetry_config.yaml input for "
                          "plugins") from e
    return data

config_schema = {
    Optional("plugins"): Use(validate_plugins),
    Optional('connections'): {
        Any(): {
            Optional('via'): str,
            Optional('alias'): str,
        },
    },
    Any(): Any(),
}