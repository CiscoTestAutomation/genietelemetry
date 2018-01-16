import json
from .bases import Consumer
from datetime import datetime, timedelta

from ats.log.utils import banner
from telemetry.results import ERRORED, OK, WARNING, CRITICAL, StatusCounter

class DataConsumer(Consumer):

    @property
    def context(self):
        return self.runtime.context

    def peek_datetime_range(self, datetime, delta):
        to_process = sorted(list(self.context.keys()))
        to_return = []
        for t in to_process[::-1]:
            if datetime - t > delta:
                break
            to_return.append(t)
        return to_return[::-1]

    def consume_from_steam(self, device = None, datetime_ = None, delta = None):

        if not delta:
            delta = timedelta(minutes = 1)

        if datetime_:
            time_range = self.peek_datetime_range(datetime_, delta)
        else:
            time_range = self.context.keys()

        to_return = []
        for t in time_range:
            if not device or device == self.context[t].get('device', None):
                to_return.append(self.context[t])
        return to_return

    def _report(self, datetime_ = None, device = None, **kwargs):
        dict_ =  self.consume_from_steam(device = device,
                                         datetime_ = datetime_,
                                         delta = timedelta(**kwargs))
        result = StatusCounter()
        report = []

        errors = []
        meta = []
        device_status = {}
        for data in dict_:
            dev = data.get('device')
            status = data.get('status')
            plugin_meta = status.meta
            if not device:
                device_status.setdefault(dev, OK)
                status += device_status[dev]
                device_status[dev] = status
            else:
                status = str(status).lower()
                r_ = getattr(result, status, 0) + 1
                result.update({status: r_})

            context = data.get('context', {})

            error = context.get('error', None)
            if error:
                errors.append('device: %s'% dev)
                errors.append('timestamp: %s'% data.get('datetime'))
                errors.append('plugin: %s'% context.get('plugin', None))
                errors.append('-' * 80)
                errors.append(error)
                errors.append('-' * 80)
            if plugin_meta and self.runtime.show_meta:
                meta.append('plugin: %s'% context.get('plugin', None))
                meta.append('%s'% json.dumps(plugin_meta, indent = 4))
                meta.append('-' * 80)
        status_groups = {}

        for dev, status in device_status.items():
            status = str(status).lower()
            r_ = getattr(result, status, 0) + 1
            result.update({status: r_})
            key = status.upper()
            if key not in status_groups:
                status_groups[key] = []
            status_groups[key].append(dev)

        if device_status:
            for status, keys in status_groups.items():
                if keys:
                    report.append('Group: %s' % status)
                    report.append('-' * 80)
                    report.extend(keys)

        if meta and self.runtime.show_meta:
            report.append(banner('Meta data'))
            report.extend(meta)

        if errors:
            report.append(banner('Error Report'))
            report.extend(errors)

        return '\n'.join(report)

    def get_detail_results(self):

        dict_ =  self.consume_from_steam()
        detail = {}
        testbed_status = OK
        detail['testbed'] = { 'name': self.runtime.testbed.name,
                              'status': testbed_status }
        detail['devices'] = {}
        for data in dict_:
            dev = data.get('device')
            status = data.get('status')
            plugin_meta = status.meta or {}

            if dev not in detail['devices']:
                detail['devices'][dev] = { 'name': dev,
                                           'status': OK,
                                           'plugins': {} }
            device = detail['devices'][dev]
            device['status'] += status

            context = data.get('context', {})
            plugin = context.get('plugin', None)
            if plugin not in detail['devices'][dev]['plugins']:
                device['plugins'][plugin] = { 'meta': [], 'error': [] }
            plugin = device['plugins'][plugin]
            timestamp = data.get('datetime')
            error = context.get('error', None)
            if error:
                plugin['error'].append((timestamp, error))
            if plugin_meta and self.runtime.show_meta:
                for ck,cv in plugin_meta.items():
                    plugin['meta'].append((ck, cv))
                
            testbed_status += status
        detail['testbed']['status'] = testbed_status
        return detail

    def get_summary_detail(self, device = None):
        dict_ =  self.consume_from_steam(device = device)
        device_status = {}

        for data in dict_:
            dev = data.get('device')
            status = data.get('status')

            if dev not in device_status:
                device_status[dev] = OK
            device_status[dev] += status

        result = {}
        for dev, status in device_status.items():
            status = str(status).lower()
            r_ = getattr(result, status, 0) + 1
            result.update({status: r_})

        return result