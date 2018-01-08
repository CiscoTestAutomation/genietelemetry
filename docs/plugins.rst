.. _plugins:

Plugin System
=============

``telemetry`` is designed around a modular plugin-based architecture. The end
goal is to allow maximum developer configurability & extendability without
sacrificing overall structure, flow and code-base integrity.

.. note::

    Telemetry plugins are not for the faint of heart: it is intended for
    advanced developers to provide optional *pluggable* ``telemetry``
    features for other developers to use.


Concept & Rules
---------------

Plugins offers *optional* functionalities that may be added to ``telemetry``.
Each plugin must be configured first via a configuration YAML file before they
can be loaded, instantiated and executed.

All plugins must obey the following rules of development:

- plugins may be configured globally (for all runs in this pyATS instance) by
  creating a  ``telemetry_config.yaml`` in the root pyATS installation
  folder.

- plugins may be configured locally (for this run only) by passing in a config
  YAML via a command-line argument called ``-configuration``.

- plugins shall be independent from all other plugins.

- plugins must inherit from ``telemetry.plugins.bases.BasePlugin`` class

- plugins may contain its own argument parser. Such parsers shall follow the
  :ref:`telemetry_argument_propagation` scheme, and shall not contain
  positional arguments.

- plugins may modify ``telemetry.runtime`` attributes, but is it the
  responbility of the plugin owner to diagnose and support any failures due to
  such changes.

- plugin developers are expected to read and understand ``telemetry`` source
  code. It is mostly not possible to develop useful plugins by simply reading
  this document.

There is only one stage where plugins may run its actions.

.. csv-table:: Telemetry Plugin Stages
    :header: Stage, Description

    ``execution``, "core plugin execution logic"

Plugins are run in the designated interval in the configuration yaml file.


Creating Plugins
----------------

To create a plugin, simply subclass ``telemetry.plugins.bases.BasePlugin``
class and define the stages where your plugin needs to run.

.. code-block:: python

    # Example
    # --------
    #
    #   hello-world plugin

    import logging
    import argparse
    import datetime

    from telemetry.plugins.bases import BasePlugin

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
        # if 'device' is specified as a function argument, the current device
        # object is provided as input to this action method when called.
        # same idea when 'execution_datetime' is specified as a function
        # argument, the plugin execution datetime is provided as input to this
        # action method.
        def execution(self, device, execution_datetime):

            # plugin parser results are always stored as 'self.args'
            if self.args.print_timestamp:
                self.execution_start = datetime.datetime.now()
                logger.info('Current time is: %s' % self.execution_start)

            logger.info('Execution %s: Hello World!' % device.name)


After defining a plugin class, it needs to be configured in order to run. The
``telemetry`` plugin manager automatically reads plugin configurations from a
YAML file, ``telemetry_config.yaml``, located under top level folder of pyats
instance or the file path can be provided with ``-configuration`` parameter.

.. code-block:: yaml

    # Example
    # -------
    #
    #   example telemetry configuration file for plugins

    plugins:                   # top level key for plugins

        HelloWorldPlugin:   # this is the plugin name we defined
                            # enabled, module and order keys are
                            # mandatory. Any additional key/values are
                            # used as arguments to the plugin class
                            # constructor.

          enabled: True           # flag marking it as "enabled"
                                  # set to False to disable a plugin

          module: module.where.plugin.is.defined      # module path where this
                                                      # plugin can be imported

          interval: 30              # defines the interval of execution of
                                    # plugins, in seconds only.
          devices: []               # device filter list: if not defined, the
                                    # plugin will be applied to all devices,
                                    # otherwise, only the included devices will
                                    # be applied.

And ``telemetry`` automatically discovers, loads your plugin, and runs its
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
          enabled: True
          module: module.where.plugin.is.defined
          interval: 30 
          devices: [Tonystark-sjc]


Plugin Errors
-------------

Because plugins are a fundamental building block of ``telemetry``, any
unhandled exceptions raised from plugin actions result in catastrophic failures:
make **double sure** that your plugin is well tested and robust against all
possible environments and outcomes.

By default, all plugin errors are automatically caught and handled by
``BasePlugin.error_handler()`` method, which registers the error and prevent
the system from crashing. Plugin developers may overwrite this method to
develop custom error handling schemes.

Whenever plugins error out, your email report will contain the detailed
exception.


Plugin Meta Data
----------------

By default, plugin meta data is collected through ``HealthStatus.meta`` method,
which stores any python picklable value and display at notification or final
report when ``-meta`` argument is used. Plugin developers may overwrite this
method to develop custom meta data handling logic.


Plugin Execution
----------------
Plugin Templates can be found in the template folder after installation

.. code-block:: bash

    $VIRTUAL_ENV/templates/telemetry/

Steps for executing your plugin:

    - Compress your plugin package or file into zip file

    .. code-block:: bash

        [tony@jarvis:template]$ zip -r plugin.zip plugin/
          adding: plugin/ (stored 0%)
          adding: plugin/iosxe/ (stored 0%)
          adding: plugin/iosxe/__init__.py (deflated 32%)
          adding: plugin/iosxe/plugin.py (deflated 49%)
          adding: plugin/iosxr/ (stored 0%)
          adding: plugin/iosxr/__init__.py (deflated 32%)
          adding: plugin/iosxr/plugin.py (deflated 50%)
          adding: plugin/nxos/ (stored 0%)
          adding: plugin/nxos/__init__.py (deflated 32%)
          adding: plugin/nxos/plugin.py (deflated 50%)
          adding: plugin/__init__.py (deflated 18%)
          adding: plugin/plugin.py (deflated 60%)
        [tony@jarvis:template]$ ls -al
        total 24
        drwxr-xr-x 3 tony eng 4096 Sep 30 23:50 .
        drwxr-xr-x 4 tony eng 4096 Sep 30 23:39 ..
        drwxr-xr-x 5 tony eng 4096 Sep 30 23:39 plugin
        -rw-r--r-- 1 tony eng 8273 Sep 30 23:50 plugin.zip
        [tony@jarvis:template]$ pwd
        /ws/tony-stark/pyats/template

    - Create your config.yaml file

    .. code-block:: yaml

        plugins:
            plugin:
                interval: 30
                enabled: True
                module: /ws/tony-stark/pyats/template/plugin.zip

        core:
            job:
                class: telemetry.job.Job
            reporter:
                class: telemetry.reporter.HealthReporter
            runinfo:
                class: telemetry.runinfo.RunInfo
            mailbot:
                class: telemetry.email.MailBot
            producer:
                class: telemetry.processor.DataProducer
            consumer:
                class: telemetry.processor.DataConsumer
            connection:
                class: unicon.Unicon
            thresholds:
                OK: 272h
                Warning: 252h
                Critical: 248h

    - Execute telemetry for on-demand monitoring:

    .. code-block:: bash

        telemetry -testbed_file /path/to/testbed.yaml
                     -configuration /path/to/config.yaml
                     -plugin_arg1 "abc"

You should see the following lines show up in the log.

.. code-block:: bash

    Starting monitoring job for testbed: basement_lab
    Monitoring type: On Demand
    ----------------------------------------------------------------------------
    Unpacking and importing plugins
    ----------------------------------------------------------------------------
     - imported module : crashdumps
     - unpacked plugin file : /ws/tony-stark/pyats/template/plugin.zip
     - imported module : plugin
    ----------------------------------------------------------------------------
    initializing plugins for Jarvis
     - loading plugin crashdumps
     - loading plugin plugin
    Starting monitoring on device_1


Abstraction Plugin Package
--------------------------
First make sure you have read pyATS abstract_, especially the section on Lookup
Decorator as it is the root of abstraction in Telemetry.

.. _abstract: http://wwwin-pyats.cisco.com/cisco-shared/abstract/html/

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


Default Plugins
---------------
Once development for your plugin is completed, it can be added to the "default"
list of plugins that run everytime telemetry is executed. The keepalive
plugin is an example of a default plugin.

To add your plugin to the default list, simply add your information to the
src/telemetry/config/defaults.py file

.. code-block:: bash

    DEFAULT_CONFIGURATION = '''
        plugins:
            keepalive:
                interval: 30
                enabled: True
                module: telemetry.plugins.keepalive
            mynewplugin:
                interval: 60
                enabled: True
                module: telemetry.plugins.mynewplugin
