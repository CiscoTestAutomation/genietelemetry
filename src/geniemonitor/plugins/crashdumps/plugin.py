'''
GenieMonitor Crashdumps Plugin
'''

# ATS
from ats.utils import parser as argparse
from ats.datastructures import classproperty

# GenieMonitor
from geniemonitor.plugins.bases import BasePlugin
from geniemonitor.results import OK, WARNING, ERRORED, PARTIAL, CRITICAL
from geniemonitor.plugins.utils import check_cores, upload_to_server,\
                                           clear_cores


class Plugin(BasePlugin):

    __plugin_name__ = 'Crash Dumps Plugin'

    @classproperty
    def parser(cls):
        parser = argparse.ArgsPropagationParser(add_help = False)
        parser.title = 'Crash Dumps'

        # upload
        # ------
        parser.add_argument('-upload',
                            action="store",
                            default=False,
                            help='Specify whether upload core dumps')
        # clean_up
        # --------
        parser.add_argument('-clean_up',
                            action="store",
                            default=False,
                            help='Specify whether clear core after upload')
        # protocol
        # --------
        parser.add_argument('-protocol',
                            action="store",
                            default='tftp',
                            help = 'Specify upload protocol\ndefault to TFTP')
        # server
        # ------
        parser.add_argument('-server',
                            action="store",
                            default=None,
                            help = 'Specify upload Server\ndefault uses '
                                   'servers information from yaml file')
        # port
        # ----
        parser.add_argument('-port',
                            action="store",
                            default=None,
                            help = 'Specify upload Port\ndefault uses '
                                   'servers information from yaml file')
        # username
        # --------
        parser.add_argument('-username',
                            action="store",
                            default=None,
                            help = 'Specify upload username credentials')
        # password
        # --------
        parser.add_argument('-password',
                            action="store",
                            default=None,
                            help = 'Specify upload password credentials')
        # destination
        # -----------
        parser.add_argument('-destination',
                            action="store",
                            default=None,
                            help = "Specify destination folder at remote "
                                   "server\ndefault to '/'")
        # timeout
        # -------
        parser.add_argument('-timeout',
                            action="store",
                            default=300,
                            help = "Specify upload timeout value\ndefault "
                                   "to 300 seconds")
        return parser


    def execution(self, device, execution_time):

        # Init
        status = OK

        # List to hold cores
        self.core_list = []

        # Execute command to check for cores
        status += check_cores(device, execution_time)

        # User requested upload cores to server
        if self.args.upload and status == CRITICAL:
            kwargs = {'protocol': self.args.protocol, 
                      'server': self.args.server, 
                      'port': self.args.port, 
                      'username': self.args.username,
                      'password': self.args.password, 
                      'destination': self.args.destination,
                      'timeout': self.args.timeout}
            status += upload_to_server(device, **kwargs)

        # User requested clean up of cores
        if self.args.clean_up and status == CRITICAL:
            status += clear_cores(device)

        # Final status
        return status
