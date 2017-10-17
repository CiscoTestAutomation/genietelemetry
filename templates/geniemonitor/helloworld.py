
# Example
# --------
#
#   hello-world plugin

import logging
import argparse
import datetime

from geniemonitor.plugins.bases import BasePlugin

logger = logging.getLogger(__name__)

class Plugin(BasePlugin):
    '''HelloWorld Plugin

    Saluting the world and printing the device name and runtime if a custom
    flag is used.
    '''

    # each plugin may have a unique name
    # set it by setting the 'name' class variable.
    # (defaults to the current class name)
    __plugin_name__ = 'HelloWorld'

    # each plugin may have a parser to parse its own command line arguments.
    # these parsers are invoked automatically by the parser engine during
    # easypy startup. (always use add_help=False)
    parser = argparse.ArgumentParser(add_help = False)

    # always create a plugin's own parser group
    # and add arguments to that group instead
    hello_world_grp = parser.add_argument_group('Hello World')

    # custom arguments shall always use -- as prefix
    # positional custom arguments are NOT allowed.
    hello_world_grp.add_argument('--print_timestamp',
                                 action = 'store_true',
                                 default = False)

    # plugins may define its own class constructor __init__, though, it
    # must respect the parent __init__, so super() needs to be called.
    # any additional arguments defined in the plugin config file would be
    # passed to here as keyword arguments
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # define your plugin's core execution logic as method.

    # define the execution action
    # if 'device' is specified as a function argument, the current device
    # object is provided as input to this action method when called.
    # same idea when 'execution_datetime' is specified as a function
    # argument, the plugin execution datetime is provided as input to this
    # action method.
    def execution(self, device, execution_datetime):

        # plugin parser results are always stored as 'self.args'
        if self.args.print_timestamp:
            self.execution_start = datetime.datetime.now()
            logger.info('Current time is: %s' % self.execution_start)

        logger.info('Execution %s: Hello World!' % device.name)