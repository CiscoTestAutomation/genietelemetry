''' 
GenieMonitor Crashdumps Plugin for IOSXE
'''

# Python
import time
import logging
from datetime import datetime
from collections import OrderedDict

# ATS
from ats.log.utils import banner

# GenieMonitor
from geniemonitor.plugins.bases import BasePlugin
from geniemonitor.utils import is_hitting_threshold
from geniemonitor.results import OK, WARNING, ERRORED, PARTIAL

# Parsergen
from parsergen import oper_fill_tabular


class Plugin(BasePlugin):

    # List to hold cores
    core_list = []


    def check_and_upload_cores(self, device, execution_time):

        # Init
        tempstatus = OK

        # Execute command to check for cores
        for location in ['flash:/core', 'bootflash:/core', 'harddisk:/core']:
            output = device.execute('dir {}'.format(location))
            if not output:
                return ERRORED
            else:
                # Parse through output to collect core information (if any)
                pattern = 'core something'
                for line in output.splitlines():
                    if re.search(pattern, line, re.IGNORECASE):
                        tempstatus += CRITICAL
                        process = 'abc'
                        tempstatus._meta = "Core dump generated for process '{}'".format(process)
                        core_info = dict(module = row['Module'],
                                         pid = row['PID'],
                                         instance = row['Instance'],
                                         process = row['Process-name'],
                                         date = date.replace(" ", "_"))
                        self.core_list.append(core_info)
        return tempstatus


    def upload_to_server(self, device, core_list):

        # Init
        status_= OK
        successful = True

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

        # Set response
        response = collections.OrderedDict()
        response[r"Enter username:"]="econ_send {}\\\r ; exp_continue".format(username)
        response[r"Password:"]="econ_send {}\\\r ; exp_continue".format(password)

        # Upload each core found
        for core in core_list:
            cmd = self.get_upload_cmd(server = server, port = port,
                                      dest = dest, **core)
            message = "Core dump upload attempt: {}".format(cmd)
            try:
                result = device.execute(cmd, timeout = timeout, reply=response)
                if 'operation failed' in result:
                    successful = False
                    logger.warning(banner('Upload operation failed'))
                    status_ += ERRORED
                    status_.meta = "Failed: {}".format(message)
                else:
                    status_.meta = "Successful: {}".format(message)
            except Exception as e:
                # Handle exception
                successful = False
                logger.warning(e)
                status_ += ERRORED
                status_.meta = "Failed: {}".format(message)

        return status_


    def get_upload_cmd(self, module, pid, instance, server, port, dest, 
                       date, process, protocol):
        
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


    def clear_cores(self, device):

        # Init
        status_ = OK

        # Execute command to delete cores
        try:
            device.execute('clear cores')
            status_.meta = "Cleared cores on device {}".format(device)
        except Exception as e:
            status_ += ERRORED
            status_.meta = "Failed to clear cores on device {}".format(device)
        
        return status_
''' 
GenieMonitor Crashdumps Plugin for IOSXE
'''

# Python
import time
import logging
from datetime import datetime

# ATS
from ats.log.utils import banner

# GenieMonitor
from geniemonitor.plugins.bases import BasePlugin
from geniemonitor.utils import is_hitting_threshold
from geniemonitor.results import OK, WARNING, ERRORED, PARTIAL


class Plugin(BasePlugin):

    pass