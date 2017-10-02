import os
import re
import sys
import importlib
from datetime import timedelta
from ats.utils.schemaengine import Or, Any, Use, Optional
from ats.utils.exceptions import SchemaError
from ats.utils.import_utils import import_from_name

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

            # build the plugin arguments
            # If user given any arg not defined in the yaml file,
            # it is passes as kwargs to the __init__ of the plugins
            kwargs = {}

            for key, value in list(config.items()):
                if key in ('enabled', 'module'): 
                    continue

                kwargs[key] = config.pop(key)

            # Basically, plugin name = class name.
            # let's find it inside the loaded module
            extension = os.path.splitext(os.path.basename(config['module']))[1]
            if extension not in ('.zip', '.whl', '.plugin'):
                module = config['module']
                config['module'] = import_from_name(module)
                config['basecls'] = import_from_name('%s.Plugin' % module)
            config['kwargs'] = kwargs

    except Exception as e:
        raise SchemaError("Invalid geniemonitor_config.yaml input for "
                          "plugins") from e
    return data

def import_threshold(data):

    if not isinstance(data, (str, int)):
        raise SchemaError("Invalid threshold input %s " % data)

    if isinstance(data, int):
        return timedelta(seconds = data)

    m = re.match(r'((\d+)w)?((\d+)d)?((\d+)h)?((\d+)m)?((\d+)s)?', data)
    _, weeks, _, days, _, hours, _, minutes, _, seconds = m.groups()
    if not weeks and not days and not hours and not minutes and not seconds:
        raise SchemaError("Invalid threshold input %s " % data)

    delta = {'weeks' : int(weeks) if weeks else 0,
             'days' : int(days) if days else 0,
             'hours' : int(hours) if hours else 0,
             'minutes' : int(minutes) if minutes else 0,
             'seconds' : int(seconds) if seconds else 0,}

    return timedelta(**delta)

def import_thresholds(data):

    try:
        assert type(data) is dict

        for status, delta in data.items():
            data[status] = import_threshold(delta)

        if not data['OK'] > data['Warning'] > data['Critical']:
            raise SchemaError("Invalid threshold order %s " % data)

    except Exception as e:
        raise SchemaError("Invalid geniemonitor_config.yaml input for "
                          "thresholds") from e
    return data

config_schema = {
    Optional("plugins"): Use(validate_plugins),
    Optional("core"): {
        Or('runinfo', 'job', 'reporter', 'mailbot', 'connection',
           'consumer', 'producer'): {
            Optional('class'): Use(import_from_name),
            Any(): Any(),
        },
        Optional("thresholds"): Use(import_thresholds),
    },
}