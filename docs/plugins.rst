.. _plugin_system:

Plugin System
=============

``genie.telemetry`` is designed around a modular plugin-based architecture.
The end goal is to allow maximum developer configurability & extendability
without sacrificing overall structure, flow and code-base integrity.

.. note::

    Genie Telemetry plugins are not for the faint of heart: it is intended for
    advanced developers to provide optional *pluggable* ``genie.telemetry``
    features for other developers to use.


Concept & Rules
---------------

Plugins offers *optional* functionalities that may be added to
``genie.telemetry``.
Each plugin must be configured first via a configuration YAML file before they
can be loaded, instantiated and executed.

All plugins must obey the following rules of development:

- plugins may be configured locally (for this run only) by passing in a config
  YAML via a command-line argument called ``-configuration``.

- plugins shall be independent from all other plugins.

- plugins must inherit from ``genie.telemetry.plugin.BasePlugin`` class

- plugins may contain its own argument parser which standardizes on double-dash
  ``--`` style arguments, and shall not contain positional arguments.

- plugin developers are expected to read and understand ``genie.telemetry``
  plugin template. It is mostly not possible to develop useful plugins by simply
  reading this document.

There is only one stage where plugins may run its actions.

.. csv-table:: Genie Telemetry Plugin Stages
    :header: Stage, Description

    ``execution``, "core plugin execution logic"

Plugins are run in the designated interval in the configuration yaml file.


Creating Plugins
----------------

To create a plugin, simply subclass ``genie.telemetry.plugin.BasePlugin``
class and define the stages where your plugin needs to run.

.. code-block:: python

    # Example
    # --------
    #
    #   hello-world plugin

    import logging
    import argparse
    import datetime

    from genie.telemetry.plugin import BasePlugin

    logger = logging.getLogger(__name__)

    class Plugin(BasePlugin):
        '''HelloWorld Plugin

        Saluting the world and printing the device name and runtime if a custom
        flag is used.
        '''

        # each plugin may have a unique name
        # set it by setting the 'name' class variable.
        # (defaults to the current class name)
        __plugin_name__ = 'HelloWorld'

        # each plugin may have a version
        # set the plugin version by setting the 'version' class variable.
        # (defaults to 1.0.0)
        __version__ = '1.0.0'

        # each plugin may have a list of supported os
        # set the plugin supported os by setting the 'token' class variable.
        # (defaults to [])
        __supported_os__ = ['nxos', 'iosxr', 'iosxe']

        # each plugin may have a parser to parse its own command line arguments.
        # these parsers are invoked automatically by the parser engine during
        # easypy startup. (always use add_help=False)
        parser = argparse.ArgumentParser(add_help = False)

        # always create a plugin's own parser group
        # and add arguments to that group instead
        hello_world_grp = parser.add_argument_group('Hello World')

        # custom arguments shall always use -- as prefix
        # positional custom arguments are NOT allowed.
        hello_world_grp.add_argument('--print_timestamp',
                                     action = 'store_true',
                                     default = False)

        # plugins may define its own class constructor __init__, though, it
        # must respect the parent __init__, so super() needs to be called.
        # any additional arguments defined in the plugin config file would be
        # passed to here as keyword arguments
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        # define your plugin's core execution logic as method.

        # define the execution action
        # the current device object is provided as input to this action method
        # when called.
        def execution(self, device):

            # plugin parser results are always stored as 'self.args'
            if self.args.print_timestamp:
                self.execution_start = datetime.datetime.now()
                logger.info('Current time is: %s' % self.execution_start)

            logger.info('Execution %s: Hello World!' % device.name)


After defining a plugin class, it needs to be configured in order to run. The
``genie.telemetry`` plugin manager automatically reads plugin configurations
from the file path that's provided with ``-configuration`` parameter.

.. code-block:: yaml

    # Example
    # -------
    #
    #   example genie telemetry configuration file for plugins

    plugins:                   # top level key for plugins

        HelloWorldPlugin:   # this is the plugin name we defined
                            # enabled, module and order keys are
                            # mandatory. Any additional key/values are
                            # used as arguments to the plugin class
                            # constructor.

          module: module.where.plugin.is.defined      # module path where this
                                                      # plugin can be imported

          interval: 30              # defines the interval of execution of
                                    # plugins, in seconds only.
          devices: []               # device filter list: if not defined, the
                                    # plugin will be applied to all devices,
                                    # otherwise, only the included devices will
                                    # be applied.

And ``genie.telemetry`` automatically discovers, loads your plugin, and runs its
actions as part of its standard execution stage.


Plugin Device Filter
--------------------

By default, plugin will be applied to all devices within the testbed. User can
fine tuning the devices filter by supplying a devices list in the configuration
file. Monitoring plugin will only executed on devices that is in the inclusive
list.

The following example indicates plugin HelloWorldPlugin only be executed on
device with name `Tonystark-sjc`.

.. code-block:: bash
    
    plugins:
        HelloWorldPlugin:
          module: module.where.plugin.is.defined
          interval: 30 
          devices: [Tonystark-sjc]


Plugin Errors
-------------

Because plugins are a fundamental building block of ``genie.telemetry``, any
unhandled exceptions raised from plugin actions result in catastrophic failures:
make **double sure** that your plugin is well tested and robust against all
possible environments and outcomes.

By default, all plugin errors are automatically caught and handled which prevent
the system from crashing.

Whenever plugins error out, the status of the execution will be ERRORED along
with exception message in the result, your email report will contain the
detailed exception in the log.


Plugin Meta Data
----------------

By default, plugin meta data is collected through ``HealthStatus.meta``,
which stores any python picklable value and display at notification.


Plugin Execution
----------------
Plugin Templates can be found in the template folder of ``genietelemetry_libs``


Steps for executing your plugin:

    - Move your plugin package to any location that is accessible via PYTHONPATH

    .. code-block:: bash

        [tony@jarvis:template]$ cp -r plugin/ $VIRTUAL_ENV/projects/genietelemetry_libs/plugins/hello
        [tony@jarvis:template]$ ls -al $VIRTUAL_ENV/projects/genietelemetry_libs/plugins/hello
        total 24
        drwxr-xr-x 3 tony eng 4096 Sep 30 23:50 .
        drwxr-xr-x 4 tony eng 4096 Sep 30 23:39 ..
        drwxr-xr-x 5 tony eng 4096 Sep 30 23:39 iosxe
        drwxr-xr-x 5 tony eng 4096 Sep 30 23:39 iosxr
        drwxr-xr-x 5 tony eng 4096 Sep 30 23:39 nxos
        -rw-r--r-- 1 tony eng 8273 Sep 30 23:50 plugin.py

    - Create your config.yaml file

    .. code-block:: yaml

        plugins:
            plugin:
                interval: 30
                module: genietelemetry_libs.plugins.hello

    - Execute genietelemetry for on-demand monitoring:

    .. code-block:: bash

        genietelemetry /path/to/testbed.yaml
                       -configuration /path/to/config.yaml
                       --print_timestamp false

You should see the following lines show up in the log.

.. code-block:: bash

    Loading genie.telemetry Configuration
    Loading genie.telemetry Plugins
    Initializing genie.telemetry Plugins for Testbed Devices
    Initializing plugins for Jarvis
     - loading plugin plugin
    Starting TimedManager ... 
    Setting up connection to device (Jarvis)


Abstraction Plugin Package
--------------------------
First make sure you have read pyATS :abstraction:`abstraction <http>`,
especially the section on Lookup Decorator as it is the root of abstraction in
Genie Telemetry.

.. code-block:: bash

    plugins
       |-- __init__.py              <-- Package declaration
       |-- plugin.py                <-- Base Plugin Structure file
       |-- iosxe                    <-- Token
       |   |-- __init__.py          <-- Token declaration
       |   `-- plugin.py            <-- Plugin core logic implementation
       |-- nxos                     <-- Token
       |   |-- __init__.py          <-- Token declaration
       |   `-- plugin.py            <-- Plugin core logic implementation
       |-- iosxr                    <-- Token
       |   |-- __init__.py          <-- Token declaration
       |   `-- plugin.py            <-- Plugin core logic implementation

