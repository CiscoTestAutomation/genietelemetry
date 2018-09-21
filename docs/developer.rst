.. highlightlang:: python

.. _developer:

===============================
Genie Telemetry Developer Guide
===============================

    1. Integrate genie.telemtry
    2. genie telemetry plugin
    3. genie telemetry plugin result

What is available?
------------------
``genie.telemetry`` comes in 3 tiers: the core package, the executable and
pyATS/Genie processor.

- The core package which is a python library that developer can import into
  their project and tailor making to suit their needs.

- The executable allows you to define a custom monitoring interval for selected
  genie telemetry plugins to monitor your testbed device. Run this as a daemon
  process and you will have a continous device health watchdog. Please beware
  that it will consume a connection to the device.

- The pyATS/Genie processor which a pre-built postprocessor that our team
  created to allow easy usage and integration between pyats/Genie and
  genie.telemtry plugins.


Integrate genie.telemtry
------------------------

Developers can integrate genie.telemetry into their python projects easily.

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


.. code-block:: python

    # Example
    # --------
    #
    #   hello-world project

    import sys
    import tempfile
    from copy import copy
    from ats.topology import loader
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


.. code-block:: bash

    $bash> python hello_world.py --genietelemetry hello_world.yaml


Genie telemetry plugin
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

Genie telemetry plugin result
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