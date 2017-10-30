
# Python
import time
import logging
from datetime import datetime

# ATS
from ats.log.utils import banner

# GenieMonitor
from geniemonitor.utils import is_hitting_threshold
from geniemonitor.results import OK, WARNING, ERRORED, PARTIAL, CRITICAL

# Parsergen
from parsergen import oper_fill_tabular

# Unicon
from unicon.eal.dialogs import Statement, Dialog

# module logger
logger = logging.getLogger(__name__)


def check_cores(device, execution_time):

    # Init
    status = OK

    # Execute command to check for cores
    header = [ "VDC", "Module", "Instance",
                "Process-name", "PID", "Date\(Year-Month-Day Time\)" ]
    output = oper_fill_tabular(device = device, 
                               show_command = 'show cores vdc-all',
                               header_fields = header, index = [5])
    if not output.entries:
        logger.info(banner("No cores found!"))
        status.meta = "No cores found!"
        return status
    
    # Parse through output to collect core information (if any)
    for k in sorted(output.entries.keys(), reverse=True):
        row = output.entries[k]
        date = row.get("Date\(Year-Month-Day Time\)", None)
        if not date:
            continue
        date_ = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        tempstatus = is_hitting_threshold(self.runtime,
                                          execution_time, date_)

        # Save core info
        core_info = dict(module = row['Module'],
                         pid = row['PID'],
                         instance = row['Instance'],
                         process = row['Process-name'],
                         date = date.replace(" ", "_"))
        self.core_list.append(core_info)

        message = "Core dump generated for process '{}' at {}".format(row['Process-name'], date_)
        logger.error(banner(message))
        status += CRITICAL
        status.meta = message

    return status


def upload_to_server(device, core_list, **kwargs):

    # Init
    status= OK

    # Get info
    info = servers.get(protocol, {})
    servers = getattr(self.runtime.testbed, 'servers', {})
    username = kwargs['username']
    password = kwargs['password']
    protocol = kwargs['protocol']
    server = kwargs['server'] or info.get('address', None)
    port = kwargs['port'] or info.get('port', None)
    dest = kwargs['destination'] or info.get('path', '/')
    timeout = kwargs['timeout'] or 300

    # Check values are not None
    if username is None or password is None or server is None or dest is None:
        return ERRORED('Unable to upload core to server. '
                       'Parameters for upload not provided by user.')

    # Create unicon dialog (for ftp)
    dialog = Dialog([
        Statement(pattern=r'Enter username:',
                  action='sendline({})'.format(username),
                  loop_continue=True,
                  continue_timer=False),
        Statement(pattern=r'Password:',
                  action='sendline({})'.format(password),
                  loop_continue=True,
                  continue_timer=False),
        ])

    # Upload each core found
    for core in core_list:
        cmd = self.get_upload_cmd(server = server, port = port,
                                  dest = dest, protocol = protocol, **core)
        message = "Core dump upload attempt: {}".format(cmd)
        try:
            result = device.execute(cmd, timeout = timeout, reply=dialog)
            if 'operation failed' in result:
                logger.error(banner('Core upload operation failed'))
                status += ERRORED
                status.meta = "Failed: {}".format(message)
            else:
                logger.info(banner('Core upload operation successful'))
                status.meta = "Successful: {}".format(message)
        except Exception as e:
            # Handle exception
            logger.warning(e)
            status += ERRORED
            status.meta = "Failed: {}".format(message)

    return status


def get_upload_cmd(module, pid, instance, server, port, dest, date, process, protocol):

    # Sample command:
    # copy core://<module-number>/<process-id>[/instance-num]
    #      tftp:[//server[:port]][/path] vrf management
    path = '{dest}/core_{pid}_{process}_{date}_{time}'.format(
                                               dest = dest, pid = pid,
                                               process = process,
                                               date = date,
                                               time = time.time())
    if port:
        server = '{server}:{port}'.format(server = server, port = port)

    if instance:
        pid = '{pid}/{instance}'.format(pid = pid, instance = instance)

    cmd = 'copy core://{module}/{pid} ' \
          '{protocol}://{server}/{path} vrf management'

    return cmd.format(module = module, pid = pid, protocol = protocol,
                      server = server, path = path)


def clear_cores(device):

    # Execute command to delete cores
    try:
        device.execute('clear cores')
        logger.info(banner("Successfully cleared cores on device"))
        status = OK
        status.meta = "Successfully cleared cores on device"
    except Exception as e:
        # Handle exception
        logger.warning(e)
        logger.error("Unable to clear cores on device")
        status = ERRORED
        status.meta = "Unable to clear cores on device"

    return status
