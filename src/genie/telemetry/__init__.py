# metadata
__version__ = '19.7'
__author__ = 'ASG/ATS Team'
__contact__ = 'pyats-support@cisco.com'
__copyright__ = 'Cisco Systems, Inc. Cisco Confidential'

from .main import main
from .plugin import BasePlugin
from .manager import Manager, TimedManager

# try to record usage statistics
#  - only internal cisco users will have stats.CesMonitor module
#  - below code does nothing for DevNet users -  we DO NOT track usage stats
#    for PyPI/public/customer users
try:
    # new internal cisco-only pkg since devnet release
    from ats.cisco.stats import CesMonitor
except Exception:
    try:
        # legacy pyats version, stats was inside utils module
        from ats.utils.stats import CesMonitor
    except Exception:
        CesMonitor = None

finally:
    if CesMonitor is not None:
        # CesMonitor exists -> this is an internal cisco user
        CesMonitor(action = __name__, application='Genie').post()
        CesMonitor(action = __name__, application='pyATS Packages').post()
