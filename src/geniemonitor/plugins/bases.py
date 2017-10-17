import os
import sys
import json
import yaml
import inspect
import logging

from datetime import datetime

from ats.log.utils import banner
from ats.datastructures import OrderableDict, classproperty

from geniemonitor.results import ERRORED, OK
from geniemonitor.email import TextEmailReport

from .. import utils

from .stages import PluginStage, Scope

# declare module as infra
__genie_monitor_infra__ = True

logger = logging.getLogger(__name__)

# default email subject (note, single line)
DEFAULT_SUBJECT = ('Monitoring Notification - device: {plugin.object.name} '
                   'status: {plugin.status}')

# default email content (make sure to take a copy)
DEFAULT_CONTENT = OrderableDict()

DEFAULT_CONTENT['Monitoring Notification'] = '''\
pyATS Instance   : {plugin.runtime.env.prefix}
CLI Arguments    : {plugin.runtime.env.argv}
User             : {plugin.runtime.env.user}
Host Server      : {plugin.runtime.env.host.name}

Monitoring Information
    Testbed Name : {plugin.runtime.testbed.name}
    Start time   : {plugin.runtime.job.starttime}

{plugin.object.name}
    Plugin Name : {plugin.name}
    Status : {plugin.status}
'''

DEFAULT_CONTENT['Plugin Snapshot'] = '{plugin.get_snapshot}'

DEFAULT_CONTENT['Status Meta'] = '{plugin.get_meta}'

DEFAULT_CONTENT['Exception Traceback'] = '{plugin.get_errors}'

class Notification(TextEmailReport):
    '''Notification class

    Used as the standard email notification generator. 
    '''

    def __init__(self,
                 plugin,
                 subject = DEFAULT_SUBJECT,
                 contents = None,
                 attachment = None):
        self.plugin = plugin
        self.subject = subject
        self.contents = contents or DEFAULT_CONTENT.copy()
        self.attachment = attachment
        self.custom_template = None

    def format_subject(self):
        try:
            return self.subject.format(plugin = self.plugin)
        except IndexError:
            # This can occur if an entry has an embedded {} in it, which
            # confuses format().
            return self.subject

    def format_content(self):
        report = []
        for title, content in self.contents.items():
            try:
                report.append('\n'.join((banner(title),
                                         content.format(
                                                    plugin = self.plugin))))
            except (IndexError, ValueError):
                # This can occur if an entry has an embedded {} in it, which
                # confuses format().
                report.append('\n'.join((banner(title), content)))

        return '\n\n'.join(report)


class BasePlugin(object):
    ''' Base class for all plugin'''

    def __init__(self, runtime, interval = None, module = None):
        '''__init__

        initializes basic information about a plugin
        '''

        # easypy runtime
        self.runtime = runtime

        # stores the plugin's parsed argument results
        self.args = None

        # error caught while running this plugin
        # (multiprocessing aware/shared dictionary)
        self.errors = self.runtime.synchro.dict()

        self.interval = interval
        self.last_execution = None
        self.report = Notification(plugin = self)
        self.object = None
        self.status = OK
        self.module = module

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

    @staticmethod
    def fmt_stage_name(stage):
        '''fmt_stage_name
        
        formats the current stage name and add pid to it if it's a execution
        related stage. This allows execution errors to be split from each other
        '''

        if stage.scope is Scope.execution:
            return '{pid}-{stage}'.format(pid = os.getpid(), 
                                          stage = stage.value)
        else:
            return stage.value

    def error_handler(self, stage, e):
        '''error_handler

        each plugin has the built-in ability to handle its own exceptions. By
        default, this exception is caught and stored - in order to avoid system
        crashing. This is the default error handler that handles this behavior.

        Warning
        -------
            overwriting this function allows you to control how errors in your
            plugins are handled, but also may lead to errors being "hidden" when
            you truly want them. Make sure you... keep track of what you are 
            doing.
        '''

        stage_name = self.fmt_stage_name(stage)

        # store error message with traceback
        self.errors[stage_name] = utils.filter_exception(*sys.exc_info())

        # log the error
        logger.error("Caught error in plugin '%s':\n\n%s" \
                     % (self.name, self.errors[stage_name]))
        logger.error(self.errors[stage_name])

    @property
    def get_errors(self):
        return '\n\n'.join(self.errors.values())

    @property
    def get_meta(self):
        metas = []
        if self.runtime.show_meta:
            metas.append(json.dumps(self.status.meta, indent = 4))
        return '\n\n'.join(metas)

    @property
    def get_snapshot(self):
        snapshot = []
        plugins = self.runtime.plugins.get_device_plugins(self.object)
        for plugin in plugins:
            name = plugin.name.ljust(50)
            snapshot.append('{}[{}]'.format(name, str(plugin.status).upper()))
        return '\n'.join(snapshot)

    def has_errors(self, stage = None):
        '''has_errors

        checks if errors occured during a particular execution stage of this 
        plugin. This is the API to use to access the errors generated when this
        plugin's various stages are run.
        '''

        if stage is None:
            return bool(self.errors)

        stage_name = self.fmt_stage_name(stage)

        return bool(self.errors.get(stage_name, None))


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


    def run(self, obj, stage):
        '''run plugin stage

        plugin entry point called by plugin manager to run a particular stage.

        any exceptions/errors during execution of a plugin stage would be stored
        within the plugin itself, accessible via .has_errors() api.

        Arguments
        ---------
            obj (device): current executing execution object
            stage (Stage): plugin stage to be run

        '''
        self.object = obj

        # catch any bad-stages
        stage = PluginStage(stage)
        stage_name = self.fmt_stage_name(stage)

        # get stage method
        method = getattr(self, stage.value, None)

        if not method:
            # stage not defined, do nothing.
            return

        if not self.runtime.switch.monitor(device = self.object,
                                           plugin = self):
            logger.info("Monitoring Skipped on Plugin %s" % self.name)
            self.status = OK
            return self.status

        reporter = obj.reporter.child(self)
        errors = None
        with reporter:
            # log it
            logger.debug('Running plugin %s: %s' % (repr(self), stage.name))

            result = None
            now = datetime.now()
            try:
                # call it and pass in the arguments
                len_args = len(inspect.getargspec(method).args[1:])
                args = [obj, now][:len_args]
                result = method(*args)
            except Exception as e:
                # handle the error!
                self.error_handler(stage, e)
            finally:
                errors = self.errors.get(stage_name, None)
                if result is None:
                    if errors:
                        result = ERRORED
                        reporter.report(obj, now, result, error = errors)
                    else:
                        result = OK
                        reporter.report(obj, now, result)
                else:
                    reporter.report(obj, now, result, error = errors)

            logger.debug('Finished running plugin %s: %s' % (repr(self), 
                                                             stage.name))

        self.status = result
        if result != OK:
            self.runtime.mailbot.send_notify(self)
        return result

    def get_summary_detail(self):
        return {}
