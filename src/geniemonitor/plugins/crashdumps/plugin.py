'''
GenieMonitor Crashdumps Plugin
'''

# ATS
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
        # upload_via
        # ----------
        parser.add_argument('-upload_via',
                            action="store",
                            default='ftp',
                            help = 'Specify upload protocol\ndefault to TFTP')
        # upload_server
        # -------------
        parser.add_argument('-upload_server',
                            action="store",
                            default=None,
                            help = 'Specify upload Server\ndefault uses '
                                   'servers information from yaml file')
        # upload_port
        # -----------
        parser.add_argument('-upload_port',
                            action="store",
                            default=None,
                            help = 'Specify upload Port\ndefault uses '
                                   'servers information from yaml file')
        # upload_username
        # ---------------
        parser.add_argument('-upload_username',
                            action="store",
                            default=None,
                            help = 'Specify upload username credentials')
        # upload_password
        # ---------------
        parser.add_argument('-upload_password',
                            action="store",
                            default=None,
                            help = 'Specify upload password credentials')
        # upload_folder
        # -------------
        parser.add_argument('-upload_folder',
                            action="store",
                            default=None,
                            help = "Specify destination folder at remote "
                                   "server\ndefault to '/'")
        # upload_timeout
        # --------------
        parser.add_argument('-upload_timeout',
                            action="store",
                            default=300,
                            help = "Specify upload timeout value\ndefault "
                                   "to 300 seconds")
        return parser


    def execution(self, device, execution_time):

        # Init
        status = OK
        upload_status = False

        # Execute command to check for cores
        status += self.check_and_upload_cores(device, execution_time)

        # User requested upload cores to server
        if self.args.upload:
            status_ += upload_to_server(self, device, self.core_list)

        # User requested clean up of cores
        if self.args.clean_up and status == CRITICAL:
            status += self.clear_cores(device)

        # Final status
        return status
