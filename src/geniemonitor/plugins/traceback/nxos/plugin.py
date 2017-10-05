''' 
GenieMonitor Traceback Plugin for NXOS.
'''

# Python
import time
import logging
from datetime import datetime

# GenieMonitor
from ..plugin import Plugin as BasePlugin
from geniemonitor.utils import is_hitting_threshold
from geniemonitor.results import OK, WARNING, ERRORED, PARTIAL

from parsergen import oper_fill_tabular

# module logger
logger = logging.getLogger(__name__)

class Plugin(BasePlugin):

    def execution(self, device, execution_time):

        status = OK
        return status