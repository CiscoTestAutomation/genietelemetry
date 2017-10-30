
# Python
import re
import logging

# ATS
from ats.log.utils import banner

# GenieMonitor
from geniemonitor.results import OK, WARNING, ERRORED, PARTIAL, CRITICAL

# Unicon
from unicon.eal.dialogs import Statement, Dialog
from unicon.eal.utils import expect_log

# module logger
logger = logging.getLogger(__name__)


def check_cores(device):

    # Init
    status = OK

    # Execute command to check for cores
    for location in ['disk0:', 'disk0:core', 'harddisk:']:
        try:
            output = device.execute('dir {}'.format(location))
        except Exception as e:
            # Handle exception
            logger.warning(e)
            logger.warning(banner("Location '{}' does not exist on device".format(location)))
            continue
        
        if 'Invalid input detected' in output:
            logger.warning(banner("Location '{}' does not exist on device".format(location)))
            continue
        elif not output:
            logger.error(banner("Unable to check for cores"))
            return ERRORED

        # 24 -rwxr--r-- 1 18225345 Oct 23 05:15 ipv6_rib_9498.by.11.20170624-014425.xr-vm_node0_RP0_CPU0.237a0.core.gz
        pattern = '(?P<number>(\d+)) +(?P<permissions>(\S+)) +(?P<other_number>(\d+)) +(?P<filesize>(\d+)) +(?P<month>(\S+)) +(?P<date>(\d+)) +(?P<time>(\S+)) +(?P<core>(.*core\.gz))'
        for line in output.splitlines():
            # Parse through output to collect core information (if any)
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                core = match.groupdict()['core']
                status += CRITICAL
                status.meta = "Core dump generated:\n'{}'".format(core)
                core_info = dict(location = location,
                                 core = core)
                core_list.append(core_info)

        if not core_list:
            logger.info(banner("No cores found!"))
            status.meta = "No cores found!"
    
    return status


def upload_to_server(device, core_list):

    # Init
    status= OK

    # Get info
    protocol = self.args.upload_via or 'tftp'
    servers = getattr(self.runtime.testbed, 'servers', {})
    info = servers.get(protocol, {})
    server = self.args.upload_server or info.get('address', None)
    port = self.args.upload_port or info.get('port', None)
    dest = self.args.upload_folder or info.get('path', '/')
    timeout = self.args.upload_timeout or 300
    username = self.args.upload_username
    password = self.args.upload_password

    # Check values are not None
    if username is None or password is None or server is None or dest is None:
        return ERRORED('Unable to upload core to server. '
                       'Parameters for upload not provided by user')

    # Create unicon dialog (for ftp)
    dialog = Dialog([
        Statement(pattern=r'Destination username:.*',
                  action='sendline({username})'.format(username=username),
                  loop_continue=True,
                  continue_timer=False),
        Statement(pattern=r'Destination password:.*',
                  action='sendline({password})'.format(password=password),
                  loop_continue=True,
                  continue_timer=False),
        Statement(pattern=r'Destination filename.*',
                  action='sendline()',
                  loop_continue=True,
                  continue_timer=False),
        ])

    # Upload each core found
    for item in self.core_list:
        cmd = self.get_upload_cmd(server = server, port = port, dest = dest, 
                                  protocol = protocol, core = item['core'], 
                                  location = item['location'])
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


def get_upload_cmd(server, port, dest, protocol, core, location):
    
    if port:
        server = '{server}:{port}'.format(server = server, port = port)

    cmd = 'copy {location}/{core} {protocol}://{server}/{dest}/{core}'

    return cmd.format(location=location, core=core, protocol=protocol,
                      server=server, dest=dest)


def clear_cores(device):

    # Create dialog for response
    dialog = Dialog([
        Statement(pattern=r'Delete.*',
                  action='sendline()',
                  loop_continue=True,
                  continue_timer=False),
        ])

    # Delete cores from the device
    for item in self.core_list:
        try:
            # Execute delete command for this core
            cmd = 'delete {location}/{core}'.format(
                    core=item['core'],location=item['location'])
            output = device.execute(cmd, timeout=300, reply=dialog)
            # Log to user
            message = 'Successfully deleted {location}/{core}'.format(
                        core=item['core'],location=item['location'])
            logger.info(banner(message))
            status = OK
            status.meta = message
        except Exception as e:
            # Handle exception
            logger.warning(e)
            message = 'Unable to delete {location}/{core}'.format(
                        core=item['core'],location=item['location'])
            logger.error(banner(message))
            status = ERRORED
            status.meta = message

    return status
