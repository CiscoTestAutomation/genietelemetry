import logging

from ats.datastructures import classproperty

from genie.telemetry.status import OK

# declare module as infra
__genietelemetry_infra__ = True

logger = logging.getLogger(__name__)

class BasePlugin(object):
    ''' Base class for all plugin'''

    def __init__(self, interval = None):
        '''__init__

        initializes basic information about a plugin
        '''

        # stores the plugin's parsed argument results
        self.args = None

        self.interval = interval

    @property
    def name(self):
        '''name

        The name of a plugin defaults to its class name. This is also used to
        start the plugin's command-line parser section when available.
        '''
        return getattr(self, '__plugin_name__',
                       getattr(self, '__module__', type(self).__name__))

    @classproperty
    def parser(cls):
        '''parser

        The parser associated with this plugin.

        Set this attribute in the class definition to overwrite the default
        None behavior.
        '''
        return None

    def parse_args(self, argv):
        '''parse_args

        parse arguments if available, store results to self.args. This follows
        the easypy argument propagation scheme, where any unknown arguments to
        this plugin is then stored back into sys.argv and untouched.

        Does nothing if a plugin doesn't come with a built-in parser.
        '''

        # do nothing when there's no parser
        if not self.parser:
            return

        # avoid parsing unknowns
        self.args, _ = self.parser.parse_known_args(argv)


    def execution(self, device):
        raise NotImplementedError("To be implemented")