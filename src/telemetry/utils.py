import os
import sys
import logging
import zipfile
import traceback

from datetime import datetime, timedelta
from telemetry.results import OK, WARNING, CRITICAL
from ats.utils.import_utils import import_from_name

# declare module as infra
__telemetry_infra__ = True

# module logger
logger = logging.getLogger(__name__)

def filter_exception(exc_type, exc_value, tb):
    '''filter_exception

    Filters an exception's traceback stack and removes Telemetry stack frames
    from it to make it more apparent that the error came from a script. Should
    be only used on user-script errors, and must not be used when an error is
    caught from ats.telemetry infra itself.

    Any frame with __telemetry_infra__ flag set is considered telemetry
    infra stack.

    Returns
    -------
        properly formatted exception message with stack trace, with telemetry
        stacks removed

    '''

    # Skip Telemetry traceback levels
    while tb and tb.tb_frame.f_globals.get('__telemetry_infra__', False):
        tb = tb.tb_next

    # return the formatted exception
    return ''.join(traceback.format_exception(exc_type, exc_value, tb)).strip()

def unzip_and_import(directory_name, input_file):
    name, extension = os.path.splitext(os.path.basename(input_file))
    if extension not in ('.zip', '.whl', '.plugin'):
        raise SchemaError("Invalid plugin file extension for %s" % input_file)

    working_path = os.path.join(directory_name, 'plugins', name)
    # unzip it
    with zipfile.ZipFile(input_file,"r") as zip_ref:
        zip_ref.extractall(working_path)

    if not os.path.isdir(os.path.join(working_path, name)):
        # Clean up the directory
        os.removedirs(working_path)
        raise SchemaError("Invalid plugin.whl structure for %s" % input_file)
    # append and import
    sys.path.append(working_path)
    return name, import_from_name(name), import_from_name('%s.Plugin'%name)

def str_to_datetime(input):
    dt, _, us = input.partition(".")
    dt = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
    us = int(us.rstrip("Z"), 10)
    return dt + timedelta(microseconds = us)

def is_hitting_threshold(runtime, now, before):

    difference = now - before

    status = _threshold(runtime.thresholds.Critical, difference, CRITICAL)
    if status is not None:
        logger.debug('hitting Critical threshold with %s ' % difference)
        return status

    status =_threshold(runtime.thresholds.Warning, difference, WARNING)
    if status is not None:
        logger.debug('hitting Warning threshold with %s ' % difference)
        return status

    logger.debug('hitting OK threshold with %s ' % difference)
    return _threshold(runtime.thresholds.OK, difference, OK) or OK

def _threshold(threshold, difference, expected):
    if difference <= threshold:
        logger.debug('[%s] Difference %s <= %s'%(expected, difference,
                                                threshold))
        return expected
    return None
