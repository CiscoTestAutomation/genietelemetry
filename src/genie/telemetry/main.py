import os
import sys
import time
import pathlib
import logging
import getpass
import platform
import traceback

from ats import log
from ats.utils import sig_handlers
from ats.datastructures import AttrDict
from ats.utils.import_utils import import_from_name

from .parser import Parser
from .manager import TimedManager
from .email import MailBot, TextEmailReport
from .utils import escape, filter_exception, ordered_yaml_dump

# module logger
logger = logging.getLogger('genie.telemetry')

__LOG_FILE__ = 'telemetry.log'
__BUFF_SIZE__ = 5000

class TelemetryLogHandler(logging.StreamHandler):
    """
    A handler class which allows the cursor to stay on
    one line for selected messages
    """
    publisher = None

    def emit(self, record):
        try:
            msg = self.format(record)
            if self.publisher:
                self.publisher.put(dict(stream=msg))
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

class GenieTelemetry(object):

    def __init__(self):
        '''Built-in __init__

        Initializes GenieTelemetry object with default values required for the
        parser.
        '''

        # collect environment information
        # -------------------------------
        self.env = AttrDict(
            argv = ' '.join(sys.argv),
            prefix = sys.prefix,
            user = getpass.getuser(),
            host = platform.node()
        )
        # configure screen logger
        # -----------------------
        # (this does nothing if screen hander is there already)
        logging.root.addHandler(log.managed_handlers.screen)
        self.telemetry_view = TelemetryLogHandler()
        logging.root.addHandler(self.telemetry_view)

        # enable double ctrl-c SIGINT handler
        # -----------------------------------
        sig_handlers.enable_double_ctrl_c()

        # create command-line argv parser
        # -------------------------------
        self.parser = Parser()

    def main(self, testbed={},
                   testbed_file = None,
                   loglevel = None,
                   configuration={},
                   configuration_file=None,
                   no_mail = False,
                   no_notify = False,
                   mailto = None,
                   mail_subject = None,
                   notify_subject = None,
                   runinfo_dir = None,
                   uid = None,
                   callback_notify = None,
                   timeout = None,
                   pdb = False):

        '''run

        Business logic, runs everything
        '''
        # parse core arguments
        # --------------------
        args = self.parser.parse_args()

        # set defaults arguments
        # ----------------------
        testbed_file = testbed_file or args.testbedfile
        loglevel = loglevel or args.loglevel
        configuration_file = configuration_file or args.configuration

        # configure logging level
        # ------------------------------
        logger.addHandler(log.managed_handlers.tasklog)
        logger.setLevel(loglevel)

        self.testbed_file = testbed_file
        self.pdb = pdb or '-pdb' in sys.argv
        self.uid = uid or args.uid
        self.timeout = timeout or args.timeout
        self.callback_notify = callback_notify or args.callback_notify

        if not runinfo_dir:
            runinfo_dir = os.path.join(os.getcwd(), 'telemetry', self.uid)
            if not os.path.exists(runinfo_dir):
                try:
                    pathlib.Path(runinfo_dir).mkdir(parents=True)
                except FileExistsError:
                    pass

        self.runinfo_dir = runinfo_dir
        self.logfile = os.path.join(self.runinfo_dir, __LOG_FILE__)

        log.managed_handlers.tasklog.changeFile(self.logfile)

        self.mailbot = MailBot(instance = self,
                               from_addrs = self.env.user,
                               to_addrs = mailto or self.env.user,
                               subject = mail_subject,
                               notify_subject = notify_subject,
                               nomail = no_mail,
                               nonotify = no_notify)

        self.report = TextEmailReport(instance = self)

        with self.mailbot:
            self.liveview = self.load_liveview()
            self.manager = TimedManager(instance=self,
                                        testbed=testbed,
                                        runinfo_dir= self.runinfo_dir,
                                        testbed_file=testbed_file,
                                        configuration=configuration,
                                        configuration_file=configuration_file,
                                        timeout=self.timeout)

            self.start()

        self.stop()

    def post_call_plugin(self, device, results):

        if self.liveview:
            websocket_data = []
            for p, res in results.items():
                for device, data in res.items():
                    status = data.get('status')
                    # to nanoseconds
                    timestamp = int(time.time()*1000000000)
                    websocket_data.append(dict(status=str(status).upper(),
                                               value=status.code,
                                               device=device,
                                               plugin=p,
                                               result=data.get('result'),
                                               timestamp=timestamp))
            self.publisher.put(dict(results=websocket_data))
            # # push over websocket
            # self.liveview.server.emit('liveview',
            #                           dict(services=dict(results=results)))

    def post_run(self, device, plugin, result):

        status = str(result.get('status', 'Ok')).capitalize()
        # verify whether we should send notify
        if status == 'Ok':
            return

        snapshots = []
        for n,s in self.get_status_snapshot(device, plugin).items():
            snapshots.append('   - {} : {}'.format(n,s))

        self.mailbot.send_notify(device=device,
                                 plugin=plugin,
                                 status=status,
                                 result=result.get('result', {}),
                                 snapshots='\n'.join(snapshots))

    # def stream_log(self):
    #     try:
    #         with open(self.logfile, 'r') as f:
    #             f.seek(self.log_index)
    #             line = escape(f.read(__BUFF_SIZE__))

    #             self.publisher
    #             self.liveview.server.emit('liveview',
    #                                       dict(services=dict(stream=line)))

    #             self.log_index += __BUFF_SIZE__
    #     except Exception as e:
    #         logger.error(e)

    #     return ''

    def load_liveview(self):
        if not self.callback_notify:
            return

        try:

            cls = import_from_name('ats_liveview.base.Feed')

        except (ImportError, AttributeError):
            return

        telemetryview = cls(self,
                       uid=self.uid,
                       runinfo_dir=self.runinfo_dir,
                       feed_type='telemetryviews',
                       events=('telemetryview',
                               'telemetryview-subscribe',
                               'telemetryview-unsubscribe',
                               'telemetryview-error'))
        # liveview.essentials.append(('stream', self.stream_log, []))
        self.telemetry_view.publisher = self.publisher = telemetryview.publisher

        return telemetryview

    def start(self):

        if self.liveview:
            logger.info('Starting Liveview Manager ... ')
            self.log_index = 0
            self.liveview.start()

        if self.manager:
            logger.info('Starting TimedManager ... ')
            devices = self.manager.setup()

            self.manager.start()

    def stop(self):
        if self.manager:
            logger.info('Stopping TimedManager ... ')
            self.manager.takedown()

        if self.liveview:
            logger.info('Stopping Liveview Manager ... ')
            self.liveview.stop()

    @property
    def name(self):
        return self.manager.testbed.name

    @property
    def devices(self):
        return ','.join(self.manager.devices.keys())

    @property
    def status(self):
        return str(self.manager.status).upper()

    @property
    def statuses(self):
        return self.manager.statuses

    @property
    def summary(self):
        return self.manager.finalize_report()

    def get_status_snapshot(self, device, plugin):
        snapshot = self.manager.plugins.get_device_plugins_status(device,
                                                                  label=True)
        snapshot.pop(plugin, None)
        return snapshot

def main():
    '''command line entry point

    command-line entry point. Uses the default runtime and checks for whether a 
    jobfile is parsed from command line, if not, exist with parser error.

    strictly used for setuptools.load_entry_point/console_script. 
    '''

    try:

        GenieTelemetry().main()

    except Exception as e:

        print(filter_exception(*sys.exc_info()), file = sys.stderr)

        # and exiting with error code
        sys.exit(1)

    sys.exit(0)


