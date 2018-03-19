import os
import sys
import pathlib
import logging
import traceback

from ats import log
from ats.utils import sig_handlers

from .parser import Parser
from .manager import TimedManager
from .utils import escape

# easypy defaults to using fork
multiprocessing = __import__('multiprocessing').get_context('fork')

# module logger
logger = logging.getLogger(__name__)

__LOG_FILE__ = 'telemetry.log'
__BUFF_SIZE__ = 5000

class GenieTelemetry(object):

    def __init__(self):
        '''Built-in __init__

        Initializes GenieTelemetry object with default values required for the
        parser.
        '''

        # configure screen logger
        # -----------------------
        # (this does nothing if screen hander is there already)
        logging.root.addHandler(log.managed_handlers.screen)

        # enable double ctrl-c SIGINT handler
        # -----------------------------------
        sig_handlers.enable_double_ctrl_c()

        # multiprocessing manager
        # -----------------------
        self.synchro = multiprocessing.Manager()

        # create command-line argv parser
        # -------------------------------
        self.parser = Parser()

    def main(self, testbed={},
                   testbed_file = None,
                   loglevel = None,
                   configuration={},
                   configuration_file=None,
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
        logger.setLevel(loglevel)

        self.pdb = pdb or '-pdb' in sys.argv
        self.uid = uid or args.uid
        self.timeout = timeout or args.timeout
        self.callback_notify = callback_notify or args.callback_notify

        if not runinfo_dir:
            runinfo_dir = os.path.join(os.getcwd(), 'logs', self.uid)
            if not os.path.exists(runinfo_dir):
                try:
                    pathlib.Path(runinfo_dir).mkdir(parents=True)
                except FileExistsError:
                    pass

        self.runinfo_dir = runinfo_dir
        self.logfile = os.path.join(self.runinfo_dir, __LOG_FILE__)

        file_handler = logging.FileHandler(self.logfile, mode='a')
        formatter = logging.Formatter('%(asctime)s: %(name)s: %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler) 

        self.liveview = self.load_liveview()
        self.manager = TimedManager(instance=self,
                                    testbed=testbed,
                                    testbed_file=testbed_file,
                                    configuration=configuration,
                                    configuration_file=configuration_file,
                                    results=self.synchro.dict(),
                                    timeout=self.timeout
                                    )

        self.start()

        self.stop()

    def post_plugin_call(self, results):

        if not self.liveview:
            return
        # push over websocket
        self.liveview.server.emit('liveview',
                                  dict(services=dict(results=results)))

    def stream_log(self):
        try:
            with open(self.logfile, 'r') as f:
                f.seek(self.log_index)
                line = escape(f.read(__BUFF_SIZE__))

                self.liveview.server.emit('liveview',
                                          dict(services=dict(stream=line)))

                self.log_index += __BUFF_SIZE__
        except Exception as e:
            logger.error(e)

        return ''

    def load_liveview(self):
        if not self.callback_notify:
            return

        try:

            cls = __import__('ats').liveview.base.Feed

        except (ImportError, AttributeError):
            return

        liveview = cls(self, uid=self.uid, runinfo_dir=self.runinfo_dir)
        liveview.essentials.append(('stream', self.stream_log, []))

        return liveview

    def start(self):

        if self.liveview:
            logger.info('Starting Liveview Manager ... ')
            self.log_index = 0
            self.liveview.start()

        if self.manager:
            logger.info('Starting TimedManager ... ')
            devices = self.manager.setup()

            for device in list(self.manager.testbed.devices.keys()):
                if device not in devices:
                    self.manager.testbed.devices.pop(device, None)

            if not self.manager.testbed.devices:
                logger.warning('unable to reach any of the testbed devices')
                return

            self.manager.start()

    def stop(self):

        if self.manager:
            logger.info('Stopping TimedManager ... ')
            self.manager.takedown()

        if self.liveview:
            logger.info('Stopping Liveview Manager ... ')
            self.liveview.stop()

def main():
    '''command line entry point

    command-line entry point. Uses the default runtime and checks for whether a 
    jobfile is parsed from command line, if not, exist with parser error.

    strictly used for setuptools.load_entry_point/console_script. 
    '''

    try:

        GenieTelemetry().main()

    except Exception as e:

        print(''.join(traceback.format_exception(*sys.exc_info())).strip(),
              file = sys.stderr)

        # and exiting with error code
        sys.exit(1)

    sys.exit(0)


