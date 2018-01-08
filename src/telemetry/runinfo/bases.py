import os
import time
import shutil
import logging

from pathlib import Path

from ats.datastructures import MetaClassFactory, classproperty
from ats.utils import parser as argparse

# module logger
logger = logging.getLogger(__name__)

YY_MM = '%y-%m'

DD_H_M_S = '%d_%H_%M_%S'

class RunInfo(object, metaclass = MetaClassFactory):
    '''RunInfo

    RunInfo classes provides the following functionality to the current Easypy
    running jobfile:
        - a runtime directory where all log/output goes to
        - an archive capability, where the above runtime directory is archived
          (saved to file).
        - upload mechanism, potentially uploading the given runtime/archive into
          an upstream log viewer/result aggregator.

    Concepts:
        - RunInfo subclasses may implement how they wish to interpret the input
          argument runinfo_dir/archive_dir. The default implementation:
          - adds a yy-mm date nesting to the archive directory for structure
          - creates a <job_uid> folder under runinfo_dir to be used as this
            run's directory.
    '''

    @classproperty
    def parser(cls):
        '''
        base parser serving all runinfo implementations.
        '''

        parser = argparse.ArgsPropagationParser(add_help = False)

        parser.title = 'Runinfo'
        
        parser.add_argument('-runinfo_dir',
                            type = str,
                            metavar = '',
                            default = argparse.SUPPRESS,
                            help = 'specify alternate runinfo directory')

        parser.add_argument('-archive_dir',
                            type = str,
                            metavar = '',
                            default = argparse.SUPPRESS,
                            help = 'specify alternate archive directory')

        parser.add_argument('-no_archive',
                            action = 'store_true',
                            default = argparse.SUPPRESS,
                            help = 'disable archive creation')
        return parser

    def __init__(self, runtime, runinfo_dir = None,
                 archive_dir = None, no_archive = False):

        # now
        timestamp = time.localtime()

        # standard default execution environment
        users_dir = Path(runtime.env.prefix, 'users')
        user_home = users_dir/runtime.env.user
        user_runinfo = user_home/'monitor_runinfo'
        user_archive = user_home/'monitor_archive'

        # create users folder if missing
        # (users directory should also allow group usage)
        if not users_dir.exists():
            users_dir.mkdir()
            users_dir.chmod(mode = 0o775)

        # create user's folder and structure if missing
        if not user_runinfo.exists():
            user_runinfo.mkdir(parents = True)
            user_archive.mkdir(parents = True)

        # save input arguments
        self.runtime = runtime
        self.runinfo_dir = runinfo_dir
        self.archive_dir = archive_dir
        self.no_archive = no_archive

        # parse arguments into self
        # (overwrite any of the above)
        self.parser.parse_args(namespace = self)

        # set defaults & convert to pathlib.Path
        runinfo_dir = Path(self.runinfo_dir or user_runinfo)
        archive_dir = Path(self.archive_dir or user_archive)
        archive_dir /= time.strftime(YY_MM, timestamp)

        # save in string format for compatiblity :\
        self.runinfo_dir = str(runinfo_dir)
        self.archive_dir = str(archive_dir)

        self.archive_file = None
        self.uid = self.runtime.uid

    def create(self):
        """ create

        creates the directories that were set in the __init__ method
        """
        # setup runinfo folder
        # (should not pre-exist)
        self.uid = "{}.{}".format(self.runtime.uid, time.time())
        runinfo_dir = Path(self.runinfo_dir)
        runinfo_dir /= self.uid

        if not runinfo_dir.exists():
            runinfo_dir.mkdir(parents = True)

        self.runinfo_dir = str(runinfo_dir)

    def archive(self):
        """ archive

        creates the archive file with the information taken from runinfo
        directory to the archive directory by using zip.
        """

        # Path form is easier to use
        archive_dir = Path(self.archive_dir)

        # create archive directory
        # ------------------------
        if not archive_dir.exists():
            archive_dir.mkdir()

        # creating archive
        # ----------------
        if self.no_archive:
            logger.info("Skipping archive creation.")
            logger.info('Logs can be found at: %s' % self.runinfo_dir)

        else:
            # compute target archive file name
            archive_filename = '{uid}.zip'.format(uid = self.uid)
            self.archive_file = str(archive_dir / archive_filename)
            logger.info('Creating archive file: %s' % self.archive_file)

            try:
                # create zip-type archive
                shutil.make_archive(*self.archive_file.rsplit('.', 1),
                                    root_dir = str(self.runinfo_dir))

            except Exception:
                # force no-cleanup and at least leave us some history
                # cannot upload if we didn't make a zip file
                self.no_archive = True

                # re-raise the exception
                raise
