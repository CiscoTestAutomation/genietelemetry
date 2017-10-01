import getpass
import weakref

from ats.datastructures import MetaClassFactory
from ats.utils import parser as argparse

from .context import ContextReporter

class Reporter(ContextReporter, metaclass = MetaClassFactory):
    
    parser = argparse.ArgsPropagationParser(add_help = False)

    def __init__(self, runtime):

        # orphants have no parent
        super().__init__(parent = None)

        # save everything
        self.runtime = runtime

        # parse arguments into self
        # (overwrite any of the above)
        self.parser.parse_args(namespace = self)

        self.children_ = {}

