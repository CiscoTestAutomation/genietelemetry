import yaml
import traceback
from ats.datastructures import OrderableDict

# declare module as infra
__genietelemetry_infra__ = True

ESCAPE_STD = (("&", "&amp;"),
              ("<", "&lt;"),
              (">", "&gt;"),
              ("\"", "&quot;"),
              ("\n", "\u000A"))

def escape(stdinput):

    for esc in ESCAPE_STD:
        stdinput = stdinput.replace(*esc)

    return stdinput

def str_or_list(value):
    '''check_file

    translates str/list into list.
    '''

    if isinstance(value, str):
        # convert string to list
        value = [value, ]

    return value


def filter_exception(exc_type, exc_value, tb):
    '''filter_exception

    Filters an exception's traceback stack and removes GenieTelemetry stack frames
    from it to make it more apparent that the error came from a script. Should
    be only used on user-script errors, and must not be used when an error is
    caught from ats.genietelemetry infra itself.

    Any frame with __genietelemetry_infra__ flag set is considered genietelemetry
    infra stack.

    Returns
    -------
        properly formatted exception message with stack trace, with genietelemetry
        stacks removed

    '''

    # Skip GenieTelemetry traceback levels
    while tb and tb.tb_frame.f_globals.get('__genietelemetry_infra__', False):
        tb = tb.tb_next

    # return the formatted exception
    return ''.join(traceback.format_exception(exc_type, exc_value, tb)).strip()

def ordered_yaml_load(stream,
                      Loader=yaml.SafeLoader,
                      object_pairs_hook=OrderableDict):

    class OrderedYamlLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))

    OrderedYamlLoader.add_constructor(
                    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                    construct_mapping)

    return yaml.load(stream, OrderedYamlLoader)

def ordered_yaml_dump(data,
                      stream=None,
                      Dumper=yaml.SafeDumper,
                      **kwds):

    class OrderedYamlDumper(Dumper):
        pass

    def _dict_representer(dumper, data):
        return dumper.represent_mapping(
                        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                        data.items())

    OrderedYamlDumper.add_representer(OrderableDict, _dict_representer)

    return yaml.dump(data, stream, OrderedYamlDumper, **kwds)
