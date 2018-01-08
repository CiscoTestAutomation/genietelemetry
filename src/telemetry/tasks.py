import os
import sys
import time
import psutil
import logging
import importlib
import setproctitle
from datetime import datetime
from collections import OrderedDict
from subprocess import PIPE, STDOUT
from . import utils
from .results import ERRORED, OK
from .plugins.manager import pmprocessor
from .plugins.stages import PluginStage

from ats.topology import loader
from ats.utils import sig_handlers

from ats.log import managed_handlers, TaskLogHandler

# tasks are only done using fork
multiprocessing = __import__('multiprocessing').get_context('fork')

from multiprocessing import Process

# declare module as infra
__telemetry_infra__ = True

# module logger
logger = logging.getLogger(__name__)

SLEEP_INTERVAL = 1
SECONDS_PER_DAY = 24*60*60

class Device(object):

    def __init__(self, device, task):
        self.device = device
        self.task = task

    @property
    def reporter(self):
        return self.task.reporter

    def __getattr__(self, item):
        return getattr(self.device, item)

    def connect(self):
        if not self.is_connected():
            self.device.connect(timeout=10)

    def disconnect(self):
        if self.is_connected():
            self.device.disconnect()

    def __enter__(self):

        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.disconnect()

class TaskManager(object):
    '''TaskManager class

    Each jobfile contains a single TaskManager, and all jobfile tasks are
    automatically registered to it. This allows global-management of all
    current running tasks & etc.
    '''

    def __init__(self, runtime):
        '''constructor

        sets internal variables
        '''
        
        # easypy runtime
        self.runtime = runtime

        # list of tasks managed by this TaskManager
        self._tasks = []

    def __iter__(self):
        '''TaskManager iterator

        makes TaskManager object instances iterable: looping over all managed
        tasks. 
        '''
        return iter(self._tasks)

    def __len__(self):
        return len(self._tasks)

    def __getitem__(self, index):
        '''
        Access a task by name or by position/order
        '''

        # integer/slice -> list.__getitem__
        if isinstance(index, int) or isinstance(index, slice):
            return self._tasks.__getitem__(index)

        # try dict.__getitem__ style using index as name
        for task in self._tasks:
            if task.taskid == index:
                return task
        else:
            raise ValueError('No such task known: %s' % index)

    @property
    def count(self):
        '''property: count

        number of currently managed tasks
        '''
        return len(self._tasks)


    def terminate(self):
        '''terminate all tasks

        This api terminates all currently active tasks. If a task is parent to
        other children processes, its these child processes are sent the
        SIGTERM signal before the parent task is terminated.
        '''

        for task in self._tasks:

            # terminate the task
            # ------------------
            # note that this does nothing for tasks that are already terminated
            # (violators will be shot, survivors will be shot again)
            task.terminate()

            # join the task (so that it doesn't turn into zombie)
            task.join()

    def register(self, task):
        self._tasks.append(task)

    @property
    def active(self):
        '''property: active

        returns the list of currently active and running task objects.
        '''
        return tuple(task for task in self._tasks if task.is_alive())


    @property
    def errors(self):
        '''errors

        Returns an ordered dictionary of task names & their corresponding errors

        '''

        return tuple(task for task in self._tasks if task.error)


    def Task(self, *args, **kwargs):

        # add runtime to arguments
        kwargs.setdefault('runtime', self.runtime)

        return Task(*args, **kwargs)

    def execute(self):

        for task in self._tasks:
            task.start()

        for task in self._tasks:
            task.wait()

class Task(multiprocessing.Process):
    '''Task class

    Task class represents the actual task/testscript being executed through a
    child process. All tasks within easypy are encapsulated in its own forked
    process from easypy main program.

    Comes with all the necessary apis to allow users to control task runs from
    a jobfile, supporting both synchronous and asynchronous execution of tasks.
    '''
    def __init__(self, device, runtime = None, **kwargs):
        '''task constructor

        instantiates a new task object. This does not fork/start the new
        process yet. Task results are piped back to the calling process using
        TaskPipe instance.

        Arguments
        ---------
            device (device): device to be worked on in the task child process
            manager (TaskManager): task manager currently managing all processes
            kwargs (dict): any other arguments to be propagated to the test
                           harness.
        '''

        if runtime is None:
            # default to the global runtime
            from . import runtime as default_runtime
            runtime = default_runtime

        # store runtime and manager
        self.runtime = runtime
        self.manager = runtime.tasks

        # job must be running
        if not self.runtime.job:
            raise RuntimeError('Cannot start a task when no job is running.')

        # create process-shared namespace
        self._shared_ns = self.runtime.synchro.Namespace()

        self.device = Device(device, self)
        self.name = device.name

        self.plugin_executions = self.runtime.synchro.list()

        # store the reporter
        self.reporter = self.runtime.job.reporter.child(self.device)

        # create task id
        taskid = '__task%s_%s' % (self.manager.count + 1, self.device.name)
        
        # escape the forward slash with underscore
        taskid = taskid.replace('/','_')

        # instantiate the process
        super().__init__(name = taskid, kwargs = kwargs)

        # register to manager
        self.manager.register(self)


    @property
    def kwargs(self):
        '''property: kwargs

        Returns
        -------

            returns the keyword argument kwargs provided to class constructor
        '''
        return self._kwargs

    @property
    def taskid(self):
        '''property: taskid

        Returns
        -------
            returns the unique task identifer. this is the same as the process
            name.
        '''
        return self.name

    @property
    def result(self):
        '''property getter: result

        returns the task result from shared namespace.
        '''

        return getattr(self._shared_ns, 'result', None)

    @result.setter
    def result(self, value):
        '''property setter: result

        automatically saves the provided result value to the shared namespace.
        '''
        self._shared_ns.result = value

    @property
    def error(self):
        '''property getter: error

        returns the task error from shared namespace.
        '''

        return getattr(self._shared_ns, 'error', None)

    @error.setter
    def error(self, details):
        '''property setter: error

        automatically saves the provided error to the shared namespace.
        '''
        self._shared_ns.error = details

    def run(self):
        '''run task

        main entry point of all task processes. This api is run in the context
        of the forked child process. The following is performed here:

        1. configure environment/process for test harness execution
        2. attempt to run the test-harness with the provided arguments, catch
           any errors that may occur and report to parent using task messaging
           system
        3. wrap up.
        '''

        self.module_logger = logging.getLogger('telemetry')
        self.task_handler = TaskLogHandler(self.runtime.job.joblog)

        self.module_logger.addHandler(self.task_handler)
        self.module_logger.addHandler(managed_handlers.screen)

        # do not propagate to root - this is now a different logger
        # for the task process
        self.module_logger.propagate = False

        self.tasklog_handler = managed_handlers.tasklog
        self.tasklog_handler.changeFile('%s/Device.%s' % 
                                          (self.runtime.directory,
                                           self.device.name))

        logging.root.addHandler(self.tasklog_handler)

        # default to INFO
        logging.root.setLevel(logging.INFO)

        # reporter start task
        # ------------------
        self.reporter.start()

        # restore sigint handler to native behavior
        sig_handlers.restore_sigint_handler()

        # start giving useful info
        logger.info("Starting monitoring on %s" % self.device.name)

        # set process title
        setproctitle.setproctitle('Telemetry task: %s' % self.name)

        plugins = self.runtime.plugins.get_device_plugins(self.device)
        # found no plugin, finishing task
        if not plugins:
            logger.warning("No monitoring plugin detected for %s" %
                                                               self.device.name)
            return self.task_finished()

        # workaround for enabling pdb under child process
        # also include special handling of -pdb argument of aetest
        should_pdb = self.runtime.pdb or self.kwargs.get('pdb', False)

        if should_pdb:
            sys.stdin = open('/dev/stdin')

        self.plugin_processor = Process(target = pmprocessor,
                                        args = (self.plugin_executions,
                                                self, plugins, should_pdb))
        try:
            self.plugin_processor.start()
            timer = 0
            while self.runtime.switch.on(self.device, timer):

                now = datetime.now()

                self.reporter.nop(now)
                # execute plugin
                # --------
                self.runtime.plugins.run(self.device, now = now,
                                         stage = PluginStage.execution)
                time.sleep(SLEEP_INTERVAL)
                timer += SLEEP_INTERVAL

            # wait for all queued plugin execution to finish
            self.plugin_executions.append([PluginStage.finished, None])
            while self.plugin_executions:
                time.sleep(SLEEP_INTERVAL)

        except (KeyboardInterrupt, SystemExit):
            pass
        except Exception as e:
            # handle error
            self.error_handler(e)
            self.runtime.producer.push_to_steam(
                                        dict(datetime = datetime.now(),
                                             object = self.device.name,
                                             content = self.result,
                                             context = { 'error': self.error }))

        return self.task_finished()

    def task_finished(self):

        logger.info("Finished task execution: %s" % self.name)

        # reporter stop task
        # -----------------
        self.reporter.stop()

        self.tasklog_handler.disableForked()
        logging.root.removeHandler(self.tasklog_handler)

        self.task_handler.close()
        self.module_logger.removeHandler(self.task_handler)
        self.module_logger.removeHandler(managed_handlers.screen)

        return self.result

    def get_result(self, stage, condition=None):

        if self.runtime.plugins.has_errors(stage = stage):
            return ERRORED if self.result is None else self.result
        return OK if self.result is None else self.result

    def error_handler(self, e):
        # set result to Errored
        self.result = ERRORED

        # save error for future reference
        self.error = traceback = utils.filter_exception(*sys.exc_info())

        # log the error into TaskLog
        logger.error('Caught error during task execution: %s' % self.name)
        logger.error(traceback)


    def start(self):
        '''start method

        starts this task. Nuff said.
        '''
        # start the process
        super().start()


    def wait(self, max_runtime = None):
        '''wait method

        Waits for this task to finish executing. If max_runtime is provided and
        exceeded, the task child process will be terminated (SIGTERM), and a
        TimeoutException will be raised to the caller.

        Arguments
        ---------
            max_runtime (int): maximum time to wait for the task to run and
                               finish, before terminating it forcifully and
                               raising errors. If not provided, waits forever.
        '''
        self.join(max_runtime)

        if self.is_alive():

            # exceeded runtime, kill it
            self.terminate()

            raise TimeoutError("Task '%s' has exceeded its max runtime of "
                               "'%s' seconds. It has been terminated "
                               "forcefully."
                               % (self.taskid, max_runtime))

    def terminate(self):
        # let the games begin!
        # --------------------
        
        # kill all task children process first
        try:
            children = psutil.Process(self.pid).children(recursive = True)
        
        except psutil.NoSuchProcess:
            # process already dead - no children
            children = []

        # terminate all children (after waiting 1s)
        goners, livings = psutil.wait_procs(children, timeout = 1)

        for children in livings:
            logger.debug('terminating task %s child process: %s'
                         % (self.taskid, children.name()))
            try:
                children.terminate()
            except Exception:
                pass

        # call Process.terminate()
        super().terminate()

    def get_summary_detail(self):
        pass


# shortcut api
def run(*args, max_runtime = None, **kwargs):
    '''run api

    Shortcut function to start a Task(), wait for it to finish, and return
    the result to the caller. This api avoids the overhead of having to deal
    with the task objects, and provides a black-box method of creating tasks
    sequentially.

    Arguments
    ---------
        max_runtime (int): maximum time to wait for the task to run and
                           finish, before terminating it forcifully and
                           raising errors. If not provided, waits forever.
        args (tuple): any other positional argument to be passed to Task()
        kwargs (dict): any other keyword arguments to be passed to Task()

    Returns
    -------
        the task's result code
    '''
    task = Task(*args, **kwargs)
    task.start()
    task.wait(max_runtime)
    return task.result
