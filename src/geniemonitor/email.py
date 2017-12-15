import os
import sys
import abc
import logging
from os import listdir
from os.path import isfile, join

from ats.utils.email import EmailMsg
from ats.utils import parser as argparse

from ats.datastructures import OrderableDict, MetaClassFactory, classproperty

from ats.log.utils import banner

from . import utils

logger = logging.getLogger(__name__)

# declare module as infra
__genie_monitor_infra__ = True

# default email subject on error (note, single line)
ERROR_SUBJECT = ('Monitoring Report - testbed: {runtime.testbed.name} '
                 'by: {runtime.env.user}, !!! an exception occured !!!')

# default email subject on plugin error (note, single line)
PLUGIN_ERROR_SUBJECT = ('Monitoring Report - testbed: {runtime.testbed.name} '
                 'by: {runtime.env.user}, '
                 '!!! exceptions occured in Monitoring plugins !!!')

# default error message body
ERROR_BODY = '''\
!!! an unhandled exception has interrupted execution !!!

This may be caused by:
    - keyboard interrupts (ctrl+c)
    - yaml file issues
    - unexpected exceptions from your plugins

As a consequence:
    - execution crashed and the environment may not be cleaned up

Please investigate the traceback below before raising issue to pyats-support.

--------------------------------------------------------------------------------

pyATS Instance   : {runtime.env.prefix}
CLI Arguments    : {runtime.env.argv}
User             : {runtime.env.user}
Host Server      : {runtime.env.host.name}

{traceback}
'''

# default email subject (note, single line)
DEFAULT_SUBJECT = ('Monitoring Report - testbed: {runtime.testbed.name} '
                   'by: {runtime.env.user}, '
                   'total: {runtime.tasks.count} '
                   '(O:{runtime.job.results[ok]}, '
                   'W:{runtime.job.results[warning]}, '
                   'C:{runtime.job.results[critical]} ...)')

# default email content (make sure to take a copy)
DEFAULT_CONTENT = OrderableDict()

DEFAULT_CONTENT['Monitoring Report'] = '''\
pyATS Instance   : {runtime.env.prefix}
CLI Arguments    : {runtime.env.argv}
User             : {runtime.env.user}
Host Server      : {runtime.env.host.name}

Monitoring Information
    Testbed Name : {runtime.testbed.name}
    Start time   : {runtime.job.starttime}
    Stop time    : {runtime.job.stoptime}
    Elapsed time : {runtime.job.elapsedtime}

Total Devices    : {runtime.tasks.count}

Overall Stats
    OK         : {runtime.job.results[ok]}
    Warning    : {runtime.job.results[warning]}
    Critical   : {runtime.job.results[critical]}
    Partial    : {runtime.job.results[partial]}
    Errored    : {runtime.job.results[errored]}

    TOTAL      : {runtime.tasks.count}
'''
DEFAULT_CONTENT['Health Status'] = '{runtime.consumer.health_summary}'

class MailBot(object, metaclass = MetaClassFactory):
    '''Mail Bot Class

    Allows auto-generation of report emails when GenieMonitor is finished
    running, pulling the reports from runtime.job.report. This class is a
    context manager: when codes are executed within it, any exceptions caught by
    __exit__ will be added to the email report and sent out.

    '''

    @classproperty
    def parser(cls):
        '''
        mailbot command-line arguments for easypy
        '''
        parser = argparse.ArgsPropagationParser(add_help = False)
        parser.title = 'Mailing'
        
        parser.add_argument('-no_mail',
                            action = "store_true",
                            default = argparse.SUPPRESS,
                            dest = 'nomail',
                            help = 'disable report email notifications')

        parser.add_argument('-no_notify',
                            action = "store_true",
                            default = argparse.SUPPRESS,
                            dest = 'nonotify',
                            help = 'disable notification on device health '
                                   'staus')

        parser.add_argument('-mailto',
                            type = str,
                            metavar = '',
                            default = argparse.SUPPRESS,
                            dest = 'to_addrs',
                            help = 'list of report email recipients')

        parser.add_argument('-mail_subject',
                            type = str,
                            metavar = '',
                            default = argparse.SUPPRESS,
                            dest = 'subject',
                            help = 'report email subject header')

        parser.add_argument('-notify_subject',
                            type = str,
                            metavar = '',
                            default = argparse.SUPPRESS,
                            dest = 'notify_subject',
                            help = 'notification email subject header')

        return parser

    def __init__(self,
                 runtime,
                 from_addrs,
                 to_addrs,
                 subject,
                 notify_subject,
                 nomail = False,
                 nonotify = False,
                 smtp_host = None,
                 smtp_port = None):
        '''mailbot constructor

        Arguments
        ---------
            from_addrs (list/str): list or string-list of addresses to be used
                                   in the generated email's "From:" field.
            to_addrs(list/str): list or string-list of addresses to be used
                                in the generated email's "To:" field.
            subject (str): alternate subject for the report email
            nomail (bool): flag to turn off auto-email notification

        '''

        # save runtime
        self.runtime = runtime

        # save arguments
        self.subject = subject
        self.notify_subject = notify_subject
        self.nomail = nomail
        self.nonotify = nonotify

        self.from_addrs = from_addrs
        self.to_addrs = to_addrs

        # parse arguments into self
        # (overwrite any of the above)
        self.parser.parse_args(namespace = self)

        # store smtp server to be used
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port

    def __enter__(self):
        '''context manager entry

        Does nothing. YOLO.

        Return
        ------
            self.
        '''
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        '''context manager exit

        If any exception is caught, an exception report email will be sent with
        the details. Otherwise, builds the standard easypy report and sends.

        Arguments
        ---------
            exc_type (cls): current exception type
            exc_value (obj): current exception value
            exc_tb (obj): current exception traceback object

        Returns
        -------
            True: always suppress the caught exception and handle internally
        '''
        if exc_type:
            # something crashed
            message = ExceptionEmailReport(
                 runtime = self.runtime,
                 contents = (exc_type,
                             exc_value,
                             exc_tb)).create_email(self.from_addrs,
                                                   self.to_addrs)
            logger.error(message.get_content())

        else:
            # everything worked, collect standard job report message
            # pass mailhtml flag to create_email
            message = self.runtime.job.report.create_email(self.from_addrs,
                                                           self.to_addrs)
            logger.info(message.get_content())

        # handle subject overwrite from command-line
        if self.subject:
            message.subject = self.subject

        if self.runtime.runinfo:
            path = self.runtime.runinfo.runinfo_dir
            onlyfiles = [join(path, f) for f in listdir(path) \
                                                       if isfile(join(path, f))]

            message.attachments.extend(onlyfiles)
            for filename in onlyfiles:
                with open(filename, 'r') as file:
                    content = file.read()
                message.body+='\n'.join((banner(os.path.basename(filename)),
                                         content))

        if not self.nomail:
            # send the bloody email
            message.send(host = self.smtp_host, port = self.smtp_port)

        # exception was handled, do not propagate
        return True

    def send_notify(self, plugin):

        if not self.nomail and not self.nonotify:
            message = plugin.report.create_email(self.from_addrs,
                                                 self.to_addrs)
            logger.info(message.get_content())

            # handle subject overwrite from command-line
            if self.notify_subject:
                message.subject = self.notify_subject

            # send the bloody email
            message.send(host = self.smtp_host, port = self.smtp_port)

    @property
    def mailto(self):
        '''mailto property getter

        Returns the to_addrs Mailbot object.
        '''
        return self.to_addrs

    @mailto.setter
    def mailto(self, list):
        '''mailto property setter
        Allows modification of to_addrs recipients in Mailbot.
        Overrides -mailto command-line argument. Can be used to modify mailto
        during runtime
        '''
        # if self.runtime.env.user not in list:
        #     list.append(self.runtime.env.user)

        # convert email addresses into Address objects
        self.to_addrs = list

class AbstractEmailReport(object, metaclass = abc.ABCMeta):
    '''AbstractEmailReport class

    Base class for all report emails to inherit from and follow.
    '''

    def create_email(self, from_addrs, to_addrs):
        '''create_email

        returns EmailMessage class instance with subject and body filled. This
        class can be overwritten to allow for MIME rich contents
        '''

        email = EmailMsg(from_addrs, to_addrs, self.format_subject(),
                         self.format_content(), self.get_attachment())

        return email

    def save(self, filename):
        '''save

        saves the report content to file. can be overwritten to do more.
        '''
        with open(filename, 'w') as file:
            file.write(str(self))

    @abc.abstractmethod
    def format_subject(self):
        '''format_subject

        abstract method, returns the subject of email report in str
        '''
        pass

    @abc.abstractmethod
    def format_content(self):
        '''format_content

        abstract method, returns the content of email report in str
        '''
        pass

    def __str__(self):
        return self.format_content()


class ExceptionEmailReport(AbstractEmailReport):
    '''ExceptionEmailReport class

    Used by MailBot to convert exceptions and tracebacks into an informative
    email message. This class is only used when the test-infrastructure crashes.
    '''
    def __init__(self, runtime,
                 subject = ERROR_SUBJECT,
                 contents = None,
                 attachment = None):
        self.runtime = runtime
        self.subject = subject
        self.contents = contents or sys.exc_info()
        self.attachment = attachment

    def format_subject(self):
        try:
            return self.subject.format(runtime = self.runtime)
        except Exception:
            # may not always be able to get the job name....
            return 'Monitoring Report - !!! an exception occured !!!'

    def format_content(self):
        tb = utils.filter_exception(*self.contents)

        return ERROR_BODY.format(traceback = tb, 
                                 runtime = self.runtime)

    def get_attachment(self):

        return self.attachment


class TextEmailReport(AbstractEmailReport):
    '''TextEmailReport class

    Used as the standard email report generator. The reporting content is based
    off basic string-formating using templates and "runtime" as the input.

    contains a "contents" OrderableDict, allowing users to add, remove and
    re-order report content. Each key in this dict formats into a section's
    banner title, and each value is sent through the formatter to generate
    section body.
    '''

    def __init__(self,
                 runtime,
                 subject = DEFAULT_SUBJECT,
                 contents = None,
                 attachment = None):
        self.runtime = runtime
        self.subject = subject
        self.contents = contents or DEFAULT_CONTENT.copy()
        self.attachment = attachment
        self.custom_template = None

    def format_subject(self):
        try:
            return self.subject.format(runtime = self.runtime)
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
                                                    runtime = self.runtime))))
            except (IndexError, ValueError):
                # This can occur if an entry has an embedded {} in it, which
                # confuses format().
                report.append('\n'.join((banner(title), content)))

        return '\n\n'.join(report)

    def get_attachment(self):

        return self.attachment