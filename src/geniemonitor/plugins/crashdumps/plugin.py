'''
GenieMonitor Crashdumps Plugin.
'''

from ats.utils import parser as argparse
from ats.datastructures import classproperty

# GenieMonitor
from geniemonitor.plugins.bases import BasePlugin

class Plugin(BasePlugin):

    __plugin_name__ = 'Crash Dumps Plugin'

    @classproperty
    def parser(cls):
        parser = argparse.ArgsPropagationParser(add_help = False)
        parser.title = 'Crash Dumps'
        parser.add_argument('-upload',
                            action="store_true",
                            default=False,
                            help='Specify whether upload core dumps')

        parser.add_argument('-clean_up',
                            action="store_true",
                            default=False,
                            help='Specify whether clear core after upload')

        # upload_via args
        # ------------------
        parser.add_argument('-upload_via',
                            action="store",
                            default='tftp',
                            help = 'Specify upload protocol\ndefault to TFTP')

        # tftp_server args
        # ------------------
        parser.add_argument('-upload_server',
                            action="store",
                            default=None,
                            help = 'Specify upload Server\ndefault uses '
                                   'servers information from yaml file')
        # tftp_port args
        # ------------------
        parser.add_argument('-upload_port',
                            action="store",
                            default=None,
                            help = 'Specify upload Port\ndefault uses '
                                   'servers information from yaml file')
        # destination args
        # ------------------
        parser.add_argument('-upload_folder',
                            action="store",
                            default=None,
                            help = "Specify destination folder at remote "
                                   "server\ndefault to '/'")
        # upload_timeout args
        # ------------------
        parser.add_argument('-upload_timeout',
                            action="store",
                            default=300,
                            help = "Specify upload timeout value\ndefault "
                                   "to 300 seconds")
        return parser