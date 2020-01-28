.. highlightlang:: python

.. _developer:

===============================
Genie Telemetry Developer Guide
===============================

    1. What's avaialble?
    2. Genie Telemetry Configuration
    3. Genie Telemetry Plugin
    4. Customized Integration
    5. Genie Telemetry Plugin Result

What is available?
------------------
``genie.telemetry`` comes in 3 tiers: the executable and the libraries and the
core package.

- The command line executable, launch a pre-defined set of plugins (managed by
  yaml file). Users have the ability to select a list of monitoring plugins
  for their testbeds with options such as customizable interval or white-list
  devices for specific plugin. Run this as a daemon process and you will have a
  continous device health watchdog. Please beware that it will consume a
  connection to the device.

- ``genie.libs.telemetry`` library ships with a variety list of plugins that
  engineers at ``genie`` team created to enhance your onboarding experience and
  could be used as reference or base plugin. The built-in pyATS/Genie processor
  which a pre-built postprocessor that allow easy usage and integration between
  pyats/Genie and ``genie.telemtry`` plugins.

- The core package which is a python package for custom extension, which
  developers can import into their project and tailor to suit their needs. It
  comes with the device connection setup, supports os abstraction and handles
  plugin scheduling.


Genie Telemetry Configuration
-----------------------------

First, you need a configuration yaml file. The yaml file should contains
required information such as plugin name and module path. The ``genie.telemetry``
plugin manager automatically reads plugin configurations from the file and
enables defined plugins in the system.

.. code-block:: yaml

    # Example
    # --------
    #
    #   content of hello-world config yaml

    plugins:
        # plugin name:
        #   module: python module path to your plugin
        cpucheck:
            module: genie.libs.telemetry.plugins.cpucheck
        tracebackcheck:
            module: genie.libs.telemtery.plugins.tracebackcheck
        crashdumps:
            module: genie.libs.telemtery.plugins.crashdumps

For more information on yaml schema of configuration file, please have a look at
:ref:`genietelemetry_configuration`


Genie Telemetry Plugin
----------------------

The potential of genie telemetry plugin is endless. It's purely based on how do
you as developer want to interact with testbed. The core package takes care of
the connection, os abstraction and scheduling so you can focus on creating great
plugins.

- You could simply have a set of configuration/command that you want to deploy
  to device at your testbed and it becomes an ultimate autonomous testbed
  management tool. It could be a daily backup, deployment a package, security
  policy or cleanup the entire network at midnight without login hundreds of
  devices and do this manually.

- You could create a list of monitor and disaster recovery plugin and the tool
  transform into a continous device watchdog that checks system usage (cpu, disk
  or network), program process monitoring, restart crashed program or any great
  idea that you have in your mind.

For more information how to create your very frist plugin, please have a look at
:ref:`plugin_system`


Customized Integration
----------------------

Developers can integrate ``genie.telemetry`` into their python projects easily.

``genie.telemetry`` delivers with a Manager class which should initialized
with required arguments such as testbed, configuration, runinfo directory before
plugin execution.

You can then invoke **run(...)** api with an unique name for the execution and
an optional list of plugins to execute. Only plugin that was defined at
configuration file will be executed. By default or empty list of plugins passed
in as argument, all defined plugins will be executed.

.. code-block:: python

    # Example
    # --------
    #
    #   hello-world project

    import sys
    import tempfile
    from copy import copy
    from pyats.topology import loader
    from genie.telemetry import Manager

    class HelloWorld(object):

        def __init__(self, testbed_file):

            # load the testbed
            self.testbed = loader.load(testbed_file)

            # parse the configuration file
            # $bash> python helloworld.py --genietelemetry /path/to/config/file
            args = copy(sys.argv[1:])
            this.configuration = Manager.parser.parse_args(args).configuration

            # have the log and result yaml store to temporary directory
            kwargs = dict(runinfo_dir=tempfile.gettempdir(),
                          configuration=this.configuration)

            # create our genie telemetry manager
            self.genie_telemetry = Manager(this.testbed, **kwargs)

            # setup device connections to testbed
            self.genie_telemetry.setup()

        def run(self, uid, plugins=[]):

            # Checking the execution result
            anomalies = []

            # run the selected plugins, if empty list, all plugins will run
            self.genie_telemetry.run(uid, plugins=plugins)

            # iterating over plugin, results
            results = self.genie_telemetry.results.get(uid, {})

            for pluginname, devices in results.items():

                p_results = []
                # iterating over device, result
                for name, result in devices.items():
                    status = result.get('status', None)
                    status_name = getattr(status, 'name', status)
                    if str(status_name).lower() == 'ok':
                        continue
                    p_results.append('\n\t\t'.join([name, status_name]))

                # everything is ok
                if not p_results:
                    continue

                anomalies.append('\n\t'.join([pluginname,
                                              '\n'.join(p_results)]))

            # print out the execution result
            print(''.join(anomalies))

    if __name__ == '__main__':

        # create our hello_world object
        hello_world = HelloWorld('/ws/tonystark-sjc/team_iron_man.yaml')

        # run cpucheck and tracebackcheck plugins
        hello_world.run('cpucheck_and_tracebackcheck',
                        plugins=['cpucheck','tracebackcheck'])

        # run cpucheck plugin only
        hello_world.run('cpucheck_only',
                        plugins=['cpucheck'])

        # run all plugins defined at configuration file
        hello_world.run('all_plugins')

        # render a genie telemetry report yaml file
        hello_world.genie_telemetry.finalize_report()


The code is ready, you can now test the customized ``genie.telemetry``
application using the following command.

.. code-block:: bash

    $bash> python hello_world.py --genietelemetry hello_world.yaml


Genie Telemetry Plugin Result
-----------------------------

Developer could roll up health status or integrate custom logic based on all
plugins execution result for the specific run. Specific business logic could be
designed for much complex scenario such as the following.

- The cpu check plugin reported 90% usage with CRITICAL status and the process
  check plugin detectd one fo cpu intense program is running right now. As this
  is expected behavior, we could safely determine that the device is still in
  good state.

- Everything is OK, however at the particular time there should be a backup
  process running and don't present. We should kick off the backup process to
  remedy the issue.

For more information how to use this at your plugin, please have a look at
:ref:`status_objects`