# python
import sys
import re

# pcall
from ats.async import Pcall

# ATS
from ats.topology.device import Device
from ats.utils import parser as argparse
from ats.datastructures import classproperty

# configuration loader
from genietelemetry.config.manager import Configuration


class Manager(object):

	def __init__(self, testbed):
		'''
		initialize the manager class by loading the plugin configuration file
		and initiating the corresponding plugins.
		'''
		# Instantiate configuration loader
		self.configuration = Configuration()

		# parse configuration file
		self.parse_args(sys.argv)

		# parse configuration file
		configuration_file = self.args.genietelemetry

		# load the configuration file
		self.testbed = testbed
		self.configuration.load(configuration_file)

		self.configuration.init_plugins('/tmp/',
			devices=testbed.devices.values())

	@classproperty
	def parser(cls):
		'''
		store the module corresponding arguments.
		'''
		parser = argparse.ArgsPropagationParser(add_help = False)
		parser.title = 'GenieTelemetry'

		# GenieTelemetry config file
		# --------------------------
		parser.add_argument('--genietelemetry',
							action="store",
							help='GenieTelemetry configuration file')
		return parser

	def parse_args(self, argv):
		'''parse_args

		parse arguments if available, store results to self.args. This follows
		the easypy argument propagation scheme, where any unknown arguments to
		this plugin is then stored back into sys.argv and untouched.

		Does nothing if a plugin doesn't come with a built-in parser.
		'''

		# do nothing when there's no parser
		if not self.parser:
			return

		# avoid parsing unknowns
		self.args, _ = self.parser.parse_known_args(argv)

	def run(self, testcase, testbed):
		'''run

		use pcall to run parallel device/plugins run and return back the result
		as a dictionary of testcase and the corresponding plugin/device result.
		'''

		new_results = {}

		for dev in testbed.devices.values():
			dev_name = dev.name
			plugins = self.configuration.plugins.get_device_plugins(dev_name)
			plugin_list = []
			for plugin in plugins:
				plugin_list.append([plugin])

    		# Pass device and corresponding plugins to Pcall
    		#   child 1: args=(device object, plugin1)
    		#   child 2: args=(device object, plugin2)
			p = Pcall(self.call_plugins, cargs = [dev], iargs = plugin_list)
			p.start()
			p.join()

			results = p.results
			# Associate device with the plugin result
			for x, y in zip(results, plugins):
				new_results[y.__plugin_name__] = {}
				new_results[y.__plugin_name__][dev_name] = x

		# Construct the testcase monitor result
		if not hasattr(self, 'testcase_monitor_result'):
			self.testcase_monitor_result = {}

		# Associate testcase name with the plugin results
		# Example
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
			#  'tracebackcheck':
				# ({'N95_2': {'2018-03-01T21:16:15.538308Z': '***** No patterns matched *****'}},
				#  {'N95_1': {'2018-03-01T21:16:14.981929Z': '***** No patterns matched *****'}})}}
		self.testcase_monitor_result[testcase.uid] = new_results

	def call_plugins(self, device, plugin):
		call_result = plugin.execution(device)

		# Example
		# {'2018-03-02T22:38:26.845988Z': "Core dump generated for process 'sysmgr' at 2018-03-01 23:21:11"}
		return call_result.meta