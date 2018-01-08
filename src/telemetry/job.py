import os
import sys
import time
import psutil
import logging
import inspect
import datetime
import multiprocessing
import importlib.machinery

from textwrap import dedent

from ats.topology import loader
from ats.log import ScreenHandler, managed_handlers, warnings

from ats.log.utils import banner, title, str_shortener
from ats.datastructures import TreeNode, MetaClassFactory

from . import utils, tasks
from .results import StatusCounter
from .email import TextEmailReport, PLUGIN_ERROR_SUBJECT

# declare module as infra
__telemetry_infra__ = True

# module logger
logger = logging.getLogger(__name__)

class Job(object, metaclass = MetaClassFactory):
    '''Job class

    Representing a currently running jobfile within easypy. Each easypy run is
    only associated with a single Job class instance, and is accessible as
    `runtime.job`.

    Job objects performs the actual job environment setup, run, finalization
    and cleanup. Refer to corresponding method for details.

    '''

    def __init__(self, testbed_file, runtime):
        '''Job constructor

        Instantiates a job object and sets all sorts of internal states.

        Arguments
        ---------
            testbed_file (str): path/name to a testbed_file to be tested
            runinfo (RunInfo): runinfo class instance to be used for this job
        '''

        # do some error checking
        # ----------------------
        # for our users's sake
        if not testbed_file:
            raise FileNotFoundError('Did you forget to provide a testbed file?')

        elif not os.path.isfile(testbed_file):
            raise FileNotFoundError("The provided testbed_file '%s' does not "
                                    "exist." % testbed_file)

        elif not os.access(testbed_file, os.R_OK):
            raise PermissionError("Testbed file '%s' is not accessible"
                                  % testbed_file)

        # store the runtime
        self.runtime = runtime
        self.runinfo = runtime.runinfo

        # store stuff internally
        self.name = os.path.splitext(os.path.basename(testbed_file))[0]
        self.file = os.path.abspath(testbed_file)
        self.report = TextEmailReport(runtime = runtime)
        # store the reporter
        self.reporter = runtime.reporter.child(self)

        # init other stuff
        self.results = StatusCounter()
        self.diags_report = None
        self.starttime = None
        self.stoptime = None
        self.elapsedtime = None
        self.image = None
        self.release = None

        self.testbed = loader.load(self.file)
        self.testbed_file = self.file

    def setup(self):
        '''setup Job run

        Stage to setup the required environment of a job run.

        '''
        self.runinfo.create()

        # always print warnings from pyATS
        warnings.enable_deprecation_warnings()

        # redirect warnings to logging & stderr
        warnings.enable_warnings_to_log()

        self.joblog = os.path.join(self.runinfo.runinfo_dir, 
                                   'MonitorLog.{name}'.format(name = self.name))

        self.tasklog_handler = managed_handlers.tasklog

        self.tasklog_handler.changeFile(self.joblog)

        logging.root.addHandler(self.tasklog_handler)

        # start the reporter
        # ------------------
        self.runtime.reporter.start()


    def finalize(self):
        '''Finalizes job run

        Stage to finalize/wrap up a job execution before cleanup.

        '''
        # cleanup reporter
        # ----------------
        self.runtime.reporter.stop()

        # create the archive dir
        self.runinfo.archive()

        # Close down the JobLog.
        self.tasklog_handler.close()
        logging.root.removeHandler(self.tasklog_handler)

    def cleanup(self):
        '''Cleanup job environment

        Stage to cleanup the whole job environment. Best-attempt: should not
        be raising exceptions. Since this stage is performed after archive is
        created, all messages are logged to screen only.

        1. kill all children processes (if any)
        2. detach all logging handlers (for graceful exit)
        3. delete the runinfo.runinfo_dir
        '''
        logger.debug('Cleaning up the environment ...')

        # kill all children (*grin*)
        # --------------------------

        # find all non-multiprocessing managed children
        managed_pids = [i.pid for i in multiprocessing.active_children()]
        all_children = psutil.Process().children(recursive = True)
        foster_childs = [i for i in all_children if i.pid not in managed_pids]

        # terminate all foster childs first before killing our own childs
        goners, livings = psutil.wait_procs(foster_childs, timeout = 1)
        for children in livings:
            logger.debug('terminating child process: %s' % children.name())
            try:
                children.terminate()
            except:
                pass

        # now terminate our own children
        for process in multiprocessing.active_children():
            # do NOT touch the synchro process
            if process is self.runtime.synchro._process:
                continue

            if process.is_alive() or process.pid:
                logger.debug('terminating child process: %s' % process.name)
                try:
                    process.terminate()
                    process.join()
                except:
                    pass

        # kill all loggers handlers
        # -------------------------
        for logger_ in logging.Logger.manager.loggerDict.values():
            # apparently not every logger has handlers -> wtf?
            for handler in getattr(logger_, 'handlers', ()):
                # don't touch ScreenHandlers
                if isinstance(handler, ScreenHandler):
                    continue

                try:
                    handler.close()
                except:
                    pass
                finally:
                    logger_.removeHandler(handler)

        logger.debug('... done cleanup!')

    def run(self):
        '''Job run

        Runs the provided jobfile. Steps:

        1. runs all pre-job plugins
        2. run main() function entry of provided jobfile
        3. cleanup any dangling tasks
        4. add any child task messages to report email
        5. run post-job plugins
        '''
        logger.info('Starting monitoring job for testbed: %s' % self.name)
        logger.info('Monitoring length: %s' % self.runtime.length_label)
        logger.info('-' * 80)

        # prepare plugins
        # ------------------
        self.runtime.plugins.prepare_plugins()

        # mark time start
        # ---------------
        self.starttime = datetime.datetime.now()

        # reporter start job
        # ------------------
        self.reporter.start()

        # run job
        # -------
        try:

            for name, device in self.testbed.devices.items():
                self.runtime.plugins.init_plugins(device)
                device.connections['defaults'] = self.runtime.connection
                tasks.Task(device = device, runtime = self.runtime)
            self.runtime.tasks.execute()

        except KeyboardInterrupt:
            # ctrl+c handle
            # -------------
            logger.warning('Ctrl+C keyboard interrupt detected...')
            logger.warning('Aborting run & cleaning up '
                           'as fast as possible...')

        except Exception:
            # generic shit code handle
            # ------------------------
            err_msg = "Caught error in jobfile '%s':\n\n%s" \
                     % (self.file, utils.filter_exception(*sys.exc_info()))

            # log it (joblog)
            logger.error(err_msg)

        finally:
            # check tasks all finished
            # ------------------------
            if self.runtime.tasks.active:

                # build error message
                err_msg = 'The following dangling tasks have been found:\n'
                for task in self.runtime.tasks.active:
                    err_msg += '    - %s: %s\n' % (task.taskid, 
                                                   task.device.name)
                err_msg += '\nThese tasks have been forcifully terminated. '
                err_msg += 'Did you forget to call task.wait()?'

                # kill all children and inform the user
                self.runtime.tasks.terminate()

                # log it (joblog)
                logger.error(err_msg)

        # reporter stop job
        # -----------------
        self.reporter.stop()

        # mark time stop
        # --------------
        self.stoptime = datetime.datetime.now()
        self.elapsedtime = self.stoptime - self.starttime

        logger.info('-' * 80)
        logger.info("Job finished. Wrapping up...")
