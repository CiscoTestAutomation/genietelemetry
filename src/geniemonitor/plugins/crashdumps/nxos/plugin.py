''' 
GenieMonitor Crashdumps Plugin for NXOS.
'''
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

        healder = [ "VDC", "Module", "Instance",
                    "Process-name", "PID", "Date\(Year-Month-Day Time\)" ]
        result = oper_fill_tabular(device = device, show_command = 'show core',
                                   header_fields = healder, index = [5])
        if not result.entries:
            return OK
        status = OK
        informations = []
        for k in sorted(result.entries.keys(), reverse=True):
            row = result.entries[k]
            date = row.get("Date\(Year-Month-Day Time\)", None)
            if not date:
                continue
            date_ = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

            tempstatus = is_hitting_threshold(self.runtime,
                                              execution_time, date_)

            meta = "core dump generted for process {} at {}".format(
                                                            row['Process-name'],
                                                            date_)
            tempstatus.meta = meta

            status += tempstatus

            if tempstatus != OK:
                information = dict(module = row['Module'],
                                   pid = row['PID'],
                                   instance = row['Instance'],
                                   process = row['Process-name'],
                                   date = date.replace(" ", "_"))
                informations.append(information)

        if informations:
            status += self.upload_to_server(device, informations)
        return status

    def upload_to_server(self, device, informations):

        if not self.args.upload:
            return OK

        successful = True
        portocol = self.args.upload_via or 'tftp'
        servers = getattr(self.runtime.testbed, 'servers', {})
        info = servers.get(portocol, {})

        server = self.args.upload_server or info.get('address', None)
        port = self.args.upload_port or info.get('port', None)
        dest = self.args.upload_folder or info.get('path', '/')
        timeout = self.args.upload_timeout or 300

        status_= OK

        for item in informations:
            cmd = self.get_upload_cmd(server = server, port = port,
                                      dest = dest, **item)
            message = "core dump upload attemp to {}".format(cmd)
            try:
                result = device.execute(cmd, timeout = timeout)
                if 'operation failed' in result:
                    successful = False
                    logger.warning('Upload operation failed')
                    status_ += PARTIAL
                    status_.meta = "Failed: {}".format(message)
                else:
                    status_.meta = "Successful: {}".format(message)
            except Exception as e:
                # handle exception
                successful = False
                logger.warning(e)
                status_ += PARTIAL
                status_.meta = "Failed: {}".format(message)

        # only clear cores if and only clear is True and successful uploads
        if self.args.clean_up and successful:
            try:
                device.execute('clear cores')
                status_ += OK
                status_.meta = "Successful: clear cores"
            except Exception as e:
                status_ += PARTIAL
                status_.meta = "Failed: clear cores"

        return status_

    def get_upload_cmd(self, module, pid, instance, server, port, dest, date,
                       process, protocol = 'tftp'):
        # copy core://<module-number>/<process-id>[/instance-num]
        #      tftp:[//server[:port]][/path] vrf management
        path = '{dest}/cores/core_{pid}_{process}_{date}_{time}'.format(
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
                          server = server,path = path)