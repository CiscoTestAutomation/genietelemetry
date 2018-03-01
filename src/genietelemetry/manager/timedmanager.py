# python
import os
import sys
import time
import sched
import psutil
import logging
import setproctitle
import multiprocessing

from ats.topology import loader
from ats.log import managed_handlers, TaskLogHandler

from genietelemetry.config.manager import Configuration
from genietelemetry.config.plugins import PluginManager as BaseManager

# declare module as infra
__genietelemetry_infra__ = True

logger = logging.getLogger(__name__)

scheduler = sched.scheduler(time.time, time.sleep)

class PluginManager(BaseManager):
    '''Plugin Manager class

    Instanciates, configures, manages and runs all easypy plugins. This is the
    main driver behind the easypy plugin system. Do not mock: may blow up.

    In any given process, there is only a single instance of PluginManager.
    '''

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # dictionary of interval-plugins pair
        self._plugin_interval = dict()

        # list of plugin intervals
        self._intervals = list()

    def load(self, directory, data):

        super().load(directory, data)

        for name, plugin in self._plugins.items():
            interval = plugin.get('interval', 30)
            self._plugin_interval.setdefaults(interval, [])

        # init plugin interval dictionary
        self._intervals = sorted(self._plugin_interval.keys())
        for name, plugin in self._plugins.items():

            interval = plugin.get('interval', 30)
            for i in self._intervals:

                if interval % i != 0 or name in self._plugin_interval[i]:
                    continue

                self._plugin_interval[i].append(name)

class Task(multiprocessing.Process):
    '''Task class

    Task class represents the actual device telemetry task being executed
    through a child process. All tasks within genietelemetry are encapsulated in
    its own forked process from genietelemetry main program.

    '''
    def __init__(self, manager, device, **kwargs):
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
        self.manager = manager
        self.device = device
        self.name = get(device, 'name', device)
        self.runinfo_dir = manager.runinfo_dir or os.cwd()
        self.logfile = manager.logfile

        # create task id
        taskid = '__task_%s' % self.name
        
        # escape the forward slash with underscore
        taskid = taskid.replace('/','_')

        # instantiate the process
        super().__init__(name = taskid, kwargs = kwargs)


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

    def run(self):
        '''run task

        main entry point of all task processes. This api is run in the context
        of the forked child process. 
        '''

        self.module_logger = logging.getLogger('genietelemetry')
        self.task_handler = TaskLogHandler(self.logfile)

        self.module_logger.addHandler(self.task_handler)
        self.module_logger.addHandler(managed_handlers.screen)

        # do not propagate to root - this is now a different logger
        # for the task process
        self.module_logger.propagate = False

        self.tasklog_handler = managed_handlers.tasklog

        # In case if device name has '/' which will cause issues while creating
        # the monitoring directory on the server
        if '/' in self.name:
            device_name = self.name.replace('/', '_')
        else:
            device_name = self.name

        self.tasklog_handler.changeFile(
                        os.path.join(self.runinfo_dir,
                                     'telemetry_{}.log'.format(device_name)))

        logging.root.addHandler(self.tasklog_handler)

        # default to INFO
        logging.root.setLevel(logging.INFO)

        # restore sigint handler to native behavior
        sig_handlers.restore_sigint_handler()

        # start giving useful info
        logger.info("Starting monitoring on %s" % self.name)

        # set process title
        setproctitle.setproctitle('GenieTelemetry task: %s' % self.name)

        # found no plugin, finishing task
        if not self.manager.plugins.has_device_plugins(self.name):
            logger.warning("No monitoring plugin detected for %s" % self.name)
            return self.task_finished()

        # workaround for enabling pdb under child process
        # also include special handling of -pdb argument of aetest
        should_pdb = self.manager.pdb or self.kwargs.get('pdb', False)

        if should_pdb:
            sys.stdin = open('/dev/stdin')

        try:
            iterval = 0
            while True:

                time.sleep(1)

                iterval += 1

                # execute plugins
                # ---------------
                results = self.manager.run(self.name)

                logger.info(results)

        except (KeyboardInterrupt, SystemExit):
            pass
        except Exception as e:
            logger.exception(e)

        return self.task_finished()

    def task_finished(self):

        logger.info("Finished task execution: %s" % self.name)

        self.tasklog_handler.disableForked()

        self.module_logger.removeHandler(managed_handlers.screen)

        return


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


class TimedManager(object):

    def __init__(self,
                 testbed_file=None,
                 configuration_file=None,
                 runinfo_dir=None,
                 pdb=False):

        if not testbed_file:
            raise FileNotFoundError('Did you forget to provide a testbed file?')

        elif not os.path.isfile(testbed_file):
            raise FileNotFoundError("The provided testbed_file '%s' does not "
                                    "exist." % testbed_file)

        elif not os.access(testbed_file, os.R_OK):
            raise PermissionError("Testbed file '%s' is not accessible"
                                  % testbed_file)

        # store stuff internally
        self.name = os.path.splitext(os.path.basename(testbed_file))[0]
        self.file = os.path.abspath(testbed_file)

        self.testbed = loader.load(self.file)
        self.testbed_file = self.file

        self.runinfo_dir = runinfo_dir or os.cwd()
        self.logfile = os.path.join(self.runinfo_dir, 'telemetry.log')

        self.configuration = Configuration(plugins=PluginManager)
        self.configuration.load(config=configuration_file)
        self.configuration.init_plugins(self.runinfo_dir,
                                        plugins_dir='plugins',
                                        devices=self.testbed.devices)
        self.pdb = pdb

    @property
    def plugins(self):
        return self.configuration.plugins

    def run(self, device, interval):
        '''run plugins

        main function called by executions to run all plugins in order

        This ensures proper clean-up behavior of plugins, and as well make sure
        nothing is run execution in case a plugin is not running correctly.

        If a plugin action method has "execution" argument, the current
        executing execution device will be automatically provided as function
        argument.

        Arguments
        ---------
            device (device): current executing device
            interval (integer): current execution interval

        '''

        device_name = get(device, 'name', device)

        plugin_runs = []
        cargs = (device, )

        for i in self._intervals:
            # skip if not it's turn
            if interval % i != 0:
                continue
            # get list of plugin to be executed at this interval
            for plugins in self._plugin_interval[i]:
                for plugin in plugins:
                    device_plugin = self._cache[plugin].get(device_name, None)
                    if not device_plugin:
                        continue
                    plugin = device_plugin.get('instance', None)
                    if not plugin:
                        continue
                    plugin_runs.append(plugin)

        if not plugin_runs:
            return

        return super().run(device, plugin_runs)