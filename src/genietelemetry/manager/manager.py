# python
import sys
import re

# pcall
from ats.async import Pcall

# ats
from ats.utils import parser as argparse
from ats.topology.device import Device

from argparse import ArgumentParser

# configuration loader
from genietelemetry.config.manager import Configuration


class Manager(object):

    def __init__(self):

    	parser = argparse.ArgumentParser()
    	parser.add_argument('--genietelemetry', dest = 'genietelemetry')
    	genietelemetry_args = parser.parse_args()

    	# Instantiate configuration loader
    	configuration = Configuration()

		# parse configuration file
    	configuration_file = genietelemetry_args.genietelemetry

    	# load the configuration file
    	configuration.load(configuration_file)

    	# extracting plugins arguments
    	self.plugins_dict = configuration.plugins

    def run(self, testcase, testbed=None):
        # (Pdb) pprint.pprint(self.plugins_dict)
		# {'crashdumps': {'basecls': <class 'genietelemetry_libs.plugins.crashdumps.plugin.Plugin'>,
		#                 'devices': [],
		#                 'enabled': True,
		#                 'kwargs': {'interval': 30},
		#                 'module': '/ws/karmoham-sjc/pyats/projects/genietelemetry_libs/plugins/crashdumps.zip'},
		#  'keepalive': {'basecls': <class 'genietelemetry_libs.plugins.keepalive.plugin.Plugin'>,
		#                'devices': [],
		#                'enabled': True,
		#                'kwargs': {'interval': 30},
		#                'module': <module 'genietelemetry_libs.plugins.keepalive' from '/ws/karmoham-sjc/pyats/projects/genietelemetry_libs/plugins/keepalive/__init__.py'>},
		#  'tracebackcheck': {'basecls': <class 'genietelemetry_libs.plugins.tracebackcheck.plugin.Plugin'>,
		#                     'devices': [],
		#                     'enabled': True,
		#                     'kwargs': {'interval': 30},
		#                     'module': '/ws/karmoham-sjc/pyats/projects/genietelemetry_libs/plugins/tracebackcheck.zip'}}
    	new_results = {}
    	for plugin in self.plugins_dict.keys():
    		# Collect only the plugins identified in the config file
    		# Reason is beacuse, "keepalive" plugin "in old design" will always
    		# be part of the plugins_dict but the module won't be a string
			# TODO: should be removed
    		if not isinstance(self.plugins_dict[plugin]['module'], str):
    			continue

    		# Instiantiate the Plugin
    		plugin_obj = self.plugins_dict[plugin]['basecls']()

    		# Build the per plugin-arguments dictionary to be passed to pcall
    		plugin_args_dict = {}
    		plugin_args_dict['plugin'] = plugin_obj
    		plugin_args_dict['interval'] = \
    			self.plugins_dict[plugin]['kwargs']['interval']
    		plugin_args_dict['enabled'] = \
    			self.plugins_dict[plugin]['enabled']

    		# Construct the plugin devices list to be used in Pcall
    		# ex: ikwargs = [{'c': 3}, {'c': 4}]
    		devices_list = []
    		if self.plugins_dict[plugin]['devices']:
	    		for item in self.plugins_dict[plugin]['`']:
	    			new_dict = {}
	    			new_dict[item] = testbed.devices[item]
	    			devices_list.append(new_dict)
	    	else:
	    		for dev in testbed.devices:
	    			new_dict = {}
	    			new_dict[dev] = testbed.devices[dev]
	    			devices_list.append(new_dict)

    		# Pass plugin_obj, arguments and devices to Pcall
    		#   child 1: args=(plugin_obj), kwargs= {'enabled': True,
    		#                                        'interval': 30,
    		#                                        '--crashdumps_upload': 'True',
    		#                                        'N95_1': <Device N95_1 at 0xf677b78c>}
    		#   child 2: args=(plugin_obj), kwargs= {'enabled': True,
    		#                                        'interval': 30,
    		#                                        '--crashdumps_upload': 'True',
    		#                                        'N95_2': <Device N95_2 at 0xf677cfec>}
    		# import pdb; pdb.set_trace()
    		p = Pcall(self.call_plugins,
    			      ckwargs = plugin_args_dict, ikwargs = devices_list)

    		p.start()
    		p.join()

    		results = p.results
    		new_results[plugin] = results

    	# Construct the testcase monitor result
    	if not hasattr(self, 'testcase_monitor_result'):
    		self.testcase_monitor_result = {}

    	self.testcase_monitor_result[testcase.uid] = new_results
		# (Pdb) self.testcase_monitor_result
		# {'TriggerSleep.uut':
			# {'crashdumps':
				# ({'N95_2': {'2018-03-01T21:17:00.631819Z': 'No cores found!'}},
				#  {'N95_1': {'2018-03-01T21:25:28.699888Z': "Core dump generated for process 'm6rib' at 2018-03-01 21:23:00"}}),
			#  'tracebackcheck':
				# ({'N95_2': {'2018-03-01T21:17:02.985530Z': '***** No patterns matched *****'}},
				#  {'N95_1': {'2018-03-01T21:17:02.461916Z': '***** No patterns matched *****'}})},
		# 'common_setup':
			# {'crashdumps':
			    # ({'N95_2': {'2018-03-01T21:16:13.206079Z': 'No cores found!'}},
			    #  {'N95_1': {'2018-03-01T21:25:28.699888Z': "Core dump generated for process 'm6rib' at 2018-03-01 21:23:00"}}),
			# 'tracebackcheck':
			    # ({'N95_2': {'2018-03-01T21:16:15.538308Z': '***** No patterns matched *****'}},
			    #  {'N95_1': {'2018-03-01T21:16:14.981929Z': '***** No patterns matched *****'}})}}

    def call_plugins(self, **kwargs):

    	for itm, val in kwargs.items():
    		if isinstance(val, Device):
    			device_name = itm
    			device = val
    			break

    	# TODO: Investigate the device not connected
    	# (related to removing Genie mapping dadatfile)
    	if not device.is_connected():
    		device.connect()

    	call_result = kwargs['plugin'].execution(device, **kwargs)

    	results_dict = {}
    	results_dict[device_name] = call_result.meta

    	# (Pdb) results_dict
    	# {'N95_2': {'2018-02-27T21:28:14.152095Z': 'No cores found!'}}
    	return results_dict
