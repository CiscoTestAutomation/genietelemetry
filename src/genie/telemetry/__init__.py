# metadata
__version__ = '3.0.2'
__author__ = 'ASG/ATS Team'
__contact__ = 'pyats-support@cisco.com'
__copyright__ = 'Cisco Systems, Inc. Cisco Confidential'

from .main import main
from .plugin import BasePlugin
from .manager import Manager, TimedManager

try:
    from ats.cisco.stats import CesMonitor
    CesMonitor(action = 'genietelemetry', application='Genie').post()
except Exception:
    try:
        from ats.utils.stats import CesMonitor
        CesMonitor(action = 'genietelemetry', application='Genie').post()
    except Exception:
        pass