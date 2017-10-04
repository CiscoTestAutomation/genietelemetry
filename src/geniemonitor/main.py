import os
import sys
import copy
import getpass
import logging
import weakref
import platform
import tempfile

from ats.datastructures import AttrDict

from ats import log
from ats.utils import sig_handlers
from ats.utils.import_utils import import_from_name

from .job import Job
from .email import MailBot
from .runinfo import RunInfo
from .reporter import Reporter
from .switch import Switch
from .processor import Producer, Consumer
from .parser import GenieMonitorParser
from .config.manager import Configuration
from .plugins.manager import PluginManager
from .tasks import TaskManager
from .utils import filter_exception

from ascii_graph import Pyasciigraph

# easypy defaults to using fork
multiprocessing = __import__('multiprocessing').get_context('fork')

# declare module as infra
__genie_monitor_infra__ = True

# module logger
logger = logging.getLogger(__name__)


class GenieMonitorRuntime(object):

    def __init__(self, configuration = None, uid = None):
        '''Built-in __init__

        Initializes GenieMonitor object with default values required for the
        parser.
        '''

        # runtime object
        # --------------
        # essentially a weakref proxy that gets passed to 
        # all modules that require access to runtime information
        # without getting circular reference
        self.runtime = weakref.proxy(self)

        # collect environment information
        # -------------------------------
        self.env = AttrDict(
            argv = ' '.join(sys.argv),
            prefix = sys.prefix,
            python = AttrDict(
                tag = sys.implementation.cache_tag,
                name = sys.implementation.name,
                version = platform.python_version(),
                architecture = platform.architecture()[0],
            ),
            user = getpass.getuser(),
            host = AttrDict(
                name = platform.node(),
                distro = ' '.join(platform.linux_distribution()),
                kernel = platform.release(),
                architecture = platform.machine(),
            ),
        )
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
        self.context = self.synchro.dict()

        # create command-line argv parser
        # -------------------------------
        self.parser = GenieMonitorParser(self.runtime)

        # GenieMonitor configuration
        # --------------------
        self.configuration = Configuration()
        self.configuration.load(configuration)

        # plugin manager
        # --------------
        self.plugins = PluginManager(self.runtime)

        # load plugins from configuration
        self.plugins.load(self.configuration.plugins)

        # start task manager
        # ------------------
        self.tasks = TaskManager(self.runtime)

        # setup placeholders
        # ------------------
        self.job = None
        self.runinfo = None
        self.reporter = None

        self.mailbot = None
        self.switch = None

        self.connection = self.configuration.connection
        self.thresholds = self.configuration.thresholds

        self.graph = Pyasciigraph()
        self.keep_alive = False
        self.uid = uid

    def main(self, *args, **kwargs):
        '''run
        
        Business logic, runs everything
        '''
        self._monitor(*args, **kwargs)
        # base return code is 0 if no errors & all pass
        try:
            return_code = self.job.results.success_rate != 100

        except Exception:
            # when job wasn't instanciated correctly
            return_code = 1
        
        # account for plugin errors
        return return_code or plugin_errors

    def monitor(self, *args, **kwargs):
        '''monitor
        '''
        self._monitor(*args, **kwargs)
        
        return self.consumer.get_detail_results()

    def _monitor(self, testbed_file = None, loglevel = None,
                 no_mail = False, mailto = None, mail_subject = None,
                 no_notify = False, notify_subject = None,
                 keep_alive = False, length = None,
                 runinfo_dir = None, meta = False, uid = None):
        '''_monitor
        '''
        # parse core arguments
        # --------------------
        args = self.parser.parse_args()

        # set defaults arguments
        # ----------------------
        testbed_file = testbed_file or args.testbed_file
        loglevel = loglevel or args.loglevel
        
        # configure logging level
        # ------------------------------
        logging.getLogger('geniemonitor').setLevel(loglevel)

        # check jobfile validity
        # ----------------------
        if not testbed_file:
            raise ValueError('must provide a valid TESTBEDFILE to run')

        # create core objects
        # -------------------
        # 1. mailer/reporter
        self.mailbot = MailBot(runtime = self.runtime,
                               from_addrs = self.env.user,
                               to_addrs = mailto or self.env.user,
                               subject = mail_subject,
                               notify_subject = notify_subject,
                               nomail = no_mail,
                               nonotify = no_notify,
                               **self.configuration.core.mailbot)

        self.switch = Switch(runtime = self.runtime,
                             keep_alive = keep_alive, length = length,
                             meta = meta, **self.configuration.core.switch)

        # always email everything
        # -----------------------
        with self.mailbot:
            # 2. runinfo
            self.runinfo = RunInfo(runtime = self.runtime,
                                   runinfo_dir = runinfo_dir,
                                   **self.configuration.core.runinfo)
            # 3. processor producer/consumer
            self.producer = Producer(runtime = self,
                                     **self.configuration.core.producer)
            self.consumer = Consumer(runtime = self,
                                     **self.configuration.core.consumer)
            # 4. reporter
            self.reporter = Reporter(runtime = self,
                                     consumer = self.consumer,
                                     producer = self.producer,
                                     **self.configuration.core.reporter)

            # 5. job
            self.job = Job(testbed_file = testbed_file, runtime = self.runtime,
                           **self.configuration.core.job)

            self.uid = uid or args.uid or self.uid or self.job.name

            # setup the job
            # -------------
            self.job.setup()

            # run the job
            # -----------
            self.job.run()

            # finalize the job
            # ----------------
            self.job.finalize()

        # cleanup the job
        # ---------------
        # best attempt
        #   - may not have an actual job object (if it failed to load)
        #   - may not always work - shit happens
        try:
            self.job.cleanup()
        except Exception:
            logger.debug(':( not everything goes as expected', exc_info = True)

    @property
    def directory(self):
        '''property: directory

        shortcut redirect to job.runinfo for backwards compatbility
        '''

        return self.runinfo.runinfo_dir if self.runinfo else os.getcwd()

    @property
    def testbed(self):
        '''property: testbed

        shortcut redirect to job.testbed for backwards compatbility
        '''

        return self.job.testbed if self.job else None

    @property
    def show_meta(self):
        '''property: show_meta

        shortcut redirect to switch.meta
        '''

        return self.switch.meta if self.switch else None

    @property
    def length(self):
        '''property: show_meta

        shortcut redirect to switch.length
        '''

        return self.switch.length if self.switch else 1

    @property
    def length_label(self):
        '''property: show_meta

        shortcut redirect to switch._length
        '''

        return self.switch._length if self.length != 1 else 'On Demand'

def main():
    '''command line entry point

    command-line entry point. Uses the default runtime and checks for whether a 
    jobfile is parsed from command line, if not, exist with parser error.

    strictly used for setuptools.load_entry_point/console_script. 
    '''
    default_runtime = GenieMonitorRuntime()
    try:
        # return as system code
        sys.exit(int(default_runtime.main()))

    except Exception as e:

        # handle exception by printing command line usage
        default_runtime.parser.print_usage(sys.stderr)
        print(filter_exception(*sys.exc_info()), file = sys.stderr)

        # and exiting with error code
        sys.exit(1)


def monitor(runtime = None, configuration = None,
            plugins = {}, *args, **kwargs):
    '''monitor api

    Shortcut function to start a Monitor job, wait for it to finish, and
    return the result to the caller. This api avoids the overhead of having
    to deal with the task objects, and provides a black-box method of
    creating tasks sequentially.

    Arguments
    ---------
        args (tuple): any other positional argument to be passed to Task()
        kwargs (dict): any other keyword arguments to be passed to Task()

    Returns
    -------
        the task's result code
    '''
    default_runtime = runtime or GenieMonitorRuntime()

    if configuration:
        default_runtime.configuration.load(configuration)

    if plugins:
        plugins = copy.deepcopy(plugins)
        default_runtime.configuration.update_plugins(plugins)
        default_runtime.plugins.load(default_runtime.configuration.plugins)

    return default_runtime.monitor(*args, **kwargs)
