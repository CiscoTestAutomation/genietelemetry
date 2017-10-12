import os
import time
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

        return parser

    def __init__(self, runtime, runinfo_dir = None):

        # now
        timestamp = time.localtime()

        # standard default execution environment
        users_dir = Path(runtime.env.prefix, 'users')
        user_home = users_dir/runtime.env.user
        user_runinfo = user_home/'monitor'

        # create users folder if missing
        # (users directory should also allow group usage)
        if not users_dir.exists():
            users_dir.mkdir()
            users_dir.chmod(mode = 0o775)

        # create user's folder and structure if missing
        if not user_runinfo.exists():
            user_runinfo.mkdir(parents = True)

        # save input arguments
        self.runtime = runtime
        self.runinfo_dir = runinfo_dir

        # parse arguments into self
        # (overwrite any of the above)
        self.parser.parse_args(namespace = self)

        # set defaults & convert to pathlib.Path
        runinfo_dir = Path(self.runinfo_dir or user_runinfo)
        runinfo_dir /= time.strftime(YY_MM, timestamp)
        runinfo_dir /= time.strftime(DD_H_M_S, timestamp)

        # save in string format for compatiblity :\
        self.runinfo_dir = str(runinfo_dir)

    def create(self):
        """ create

        creates the directories that were set in the __init__ method
        """
        # setup runinfo folder
        # (should not pre-exist)
        if not Path(self.runinfo_dir).exists():
            Path(self.runinfo_dir).mkdir(parents = True)
