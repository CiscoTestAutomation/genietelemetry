.. _usage:

===============
Genie Telemetry
===============

    1. Installation
    2. GenieTelemetry Launcher
    2. Standard Arguments

Installation
------------
``genie.telemetry`` package is hosted on the pyATS pypi server. 

``genie.telemetry`` comes in two parts. The core package and the libraries.

First install the core package via pip.

.. code-block:: bash

    bash$ pip install genie.telemetry

The user-contributed libraries are downloadable via Git. Execute this command
under your `projects` directory in your pyATS virtual environment `$VIRTUAL_ENV`.

.. code-block:: bash

    cd $VIRTUAL_ENV/projects
    git clone ssh://git@bitbucket-eng-sjc1.cisco.com:7999/pyats-proj/genietelemetry_libs.git


GenieTelemetry Launcher
-----------------------
Genie Telemetry comes with its own launcher: the ``genietelemetry`` executable.
This launcher is installed into your pyATS instance automatically, and is
accessible directly as part of the user PATH after activating your instance.

.. code-block:: bash

    # activate your pyats instance, eg:
    [tony@jarvis:~]$ cd /ws/tony-stark/pyats
    [tony@jarvis:pyats]$ source env.sh

    Activating the pyATS instance @ /ws/tony-stark/pyats
    --------------------------------------------------------------------
    PYTHONPATH=/ws/tony-stark/pyats:
    LD_LIBRARY_PATH=/auto/ttsw/ActiveTcl/8.4.19/lib:/usr/X11R6/lib
    --------------------------------------------------------------------

    # genietelemetry is now part of your path
    (pyats) [tony@jarvis:pyats]$ which genietelemetry
    /ws/tony-stark/pyats/bin/genietelemetry

``genietelemetry`` comes natively with built-in help information:

.. code-block:: bash

    [tony@jarvis:~]$ genietelemetry -h
    usage: genietelemetry [TESTBEDFILE]
                          [-h] [-loglevel] [-configuration FILE] [-uid UID]
                          [-runinfo_dir RUNINFO_DIR]
                          [-callback_notify CALLBACK_NOTIFY] [-timeout TIMEOUT]
                          [-connection_timeout CONNECTION_TIMEOUT] [-no_mail]
                          [-no_notify] [-mailto] [-mail_subject]
                          [-notify_subject] [-email_domain] [-smtp_host]
                          [-smtp_port]

    genie telemetry command line arguments.

    Example
    -------
      genietelemetry /path/to/testbed.yaml

    ----------------------------------------------------------------------------

    Positional Arguments:
      TESTBEDFILE           testbed file to be monitored

    Help:
      -h, -help             show this help message and exit

    Logging:
      -loglevel             genie telemetry logging level
                            eg: -loglevel="INFO"

    Configuration:
      -configuration FILE   configuration yaml file for plugins and settings
      -uid UID              Specify monitoring job uid
      -runinfo_dir RUNINFO_DIR
                            Specify directory to store execution logs
      -callback_notify CALLBACK_NOTIFY
                            Specify Liveview callback notify URI
      -timeout TIMEOUT      Specify plugin maximum execution length
                            Default to 300 seconds
      -connection_timeout CONNECTION_TIMEOUT
                            Specify connection timeout

    Mailing:
      -no_mail              disable final email report
      -no_notify            disable notification on device health status other
                            than "ok"
      -mailto               list of email recipients
      -mail_subject         report email subject header
      -notify_subject       notification email subject header
      -email_domain         default email domain
      -smtp_host            specify smtp host
      -smtp_port            specify smtp server port


.. tip::

    The built-in help information of ``genietelemetry`` automatically finds and
    lists all arguments available from each genie telemetry plugin if
    configuration file is provided.

    For example, the following config file contains tracebackcheck plugin with
    3 arguments.

    .. code-block:: yaml

        plugins:
            tracebackcheck:
                interval: 30
                module: genietelemetry_libs.plugins.tracebackcheck

    .. code-block:: bash

    [tony@jarvis:~]$ genietelemetry -h /path/to/config.yaml
    usage: genietelemetry [TESTBEDFILE]
                          [-h] [-loglevel] [-configuration FILE] [-uid UID]
                          [-runinfo_dir RUNINFO_DIR]
                          [-callback_notify CALLBACK_NOTIFY] [-timeout TIMEOUT]
                          [-connection_timeout CONNECTION_TIMEOUT] [-no_mail]
                          [-no_notify] [-mailto] [-mail_subject]
                          [-notify_subject] [-email_domain] [-smtp_host]
                          [-smtp_port]
                          [--tracebackcheck_logic_pattern TRACEBACKCHECK_LOGIC_PATTERN]
                          [--tracebackcheck_clean_up TRACEBACKCHECK_CLEAN_UP]
                          [--tracebackcheck_timeout TRACEBACKCHECK_TIMEOUT]


    genie telemetry command line arguments.

    Example
    -------
      genietelemetry /path/to/testbed.yaml

    ----------------------------------------------------------------------------

    Positional Arguments:
      TESTBEDFILE           testbed file to be monitored

    Help:
      -h, -help             show this help message and exit

    Logging:
      -loglevel             genie telemetry logging level
                            eg: -loglevel="INFO"

    Configuration:
      -configuration FILE   configuration yaml file for plugins and settings
      -uid UID              Specify monitoring job uid
      -runinfo_dir RUNINFO_DIR
                            Specify directory to store execution logs
      -callback_notify CALLBACK_NOTIFY
                            Specify Liveview callback notify URI
      -timeout TIMEOUT      Specify plugin maximum execution length
                            Default to 300 seconds
      -connection_timeout CONNECTION_TIMEOUT
                            Specify connection timeout

    Mailing:
      -no_mail              disable final email report
      -no_notify            disable notification on device health status other
                            than "ok"
      -mailto               list of email recipients
      -mail_subject         report email subject header
      -notify_subject       notification email subject header
      -email_domain         default email domain
      -smtp_host            specify smtp host
      -smtp_port            specify smtp server port

    Traceback Check:
      --tracebackcheck_logic_pattern TRACEBACKCHECK_LOGIC_PATTERN
                            Specify logical expression for patterns to
                            include/exclude when checking tracebacks following
                            PyATS logic format. Default patternis to check for
                            Tracebacks.
      --tracebackcheck_clean_up TRACEBACKCHECK_CLEAN_UP
                            Specify whether to clear all warnings and tracebacks
                            after reporting error
      --tracebackcheck_timeout TRACEBACKCHECK_TIMEOUT
                            Specify duration (in seconds) to wait before timing
                            out execution of a command



Standard Arguments
------------------
``genie.telemetry`` accepts a number of standard arguments that can be used to
influence and/or change monitoring behaviors. All arguments are constructed and
processed using python `argparse`_ module.


.. _argparse: https://docs.python.org/3/library/argparse.html

.. csv-table:: Genie Telemetry Standard Arguments
    :header: Argument, Description
    :widths: 30, 70

    ``testbed_file``, "mandatory argument, full path/name of testbed yaml file
    to monitor with."
    ``-configuration``, "configuration yaml file for telemetry plugins"
    ``-uid``, "unique id from upper systems identifying this run"
    ``-loglevel``, "specify the output log level for GenieTelemetry"
    ``-runinfo_dir``, "specify alternative runtime info directory location to
    store execution logs"
    ``-callback_notify``, "Specify Liveview callback notify URI"
    ``-timeout``, "Specify plugin maximum execution length, default to 300 sec"
    ``-connection_timeout``, "Specify connection timeout if connection class
    allows timeout override"
    ``-no_mail``, "flag, disables email report at the end of run"
    ``-mailto``, "specify the list of email report recipients."
    ``-mail_subject``, "email report subject line."
    ``-no_notify``, "flag, disable notification on abnormal device health staus
    reported by each plugin."
    ``-notify_subject``, "notification email subject header."
    ``-email_domain``, "specify default email domain, required for email or
    notification"
    ``-smtp_host``, "specify smtp host, required for email or notification"
    ``-smtp_port``, "specify smtp server port, required for email or
    notification"

.. tip::

    ``genie.telemetry`` standardizes on single-dash ``-`` style arguments.

    ``genietelemetry_libs`` standardizes on double-dash ``--`` style arguments.


``-help``
    Prints help information and how to use each arguments.

    .. code-block:: bash

        bash$ genietelemetry -help

``testbed_file``
    Mandatory argument. Specifies the full path/name to the testbed yaml to
    monitor with. Refer to :ref:`genietelemetry_testbed` for more details.

    .. code-block:: bash

        bash$ genietelemetry /path/to/testbed.yaml

``-configuration``
    Mandatory argument, used to provide the YAML plugin configuration file. Use
    this if you want to configure your Genie Telemetry to run certain plugins
    for this particular run.

    .. code-block:: bash

        bash$ genietelemetry /path/to/testbed.yaml
                             -configuration /path/to/config.yaml

``-uid``
    optional argument. Allows upstream executor to pass down a unique identifier
    string to be stored in report.

    .. code-block:: bash

        bash$ genietelemetry /path/to/testbed.yaml
                             -configuration /path/to/config.yaml
                             -uid "this_is_an_example"

``-loglevel``
    Specifies the logging level for GenieTelemetry. Use this to increase or
    decrease GenieTelemetry module's log output level for debugging purposes.
    May be specified in UPPERCASE or lowercase.

    .. code-block:: bash

        bash$ genietelemetry /path/to/testbed.yaml
                             -configuration /path/to/config.yaml
                             -loglevel INFO
        bash$ genietelemetry /path/to/testbed.yaml
                             -configuration /path/to/config.yaml
                             -loglevel DEBUG

.. _log level: https://docs.python.org/3/howto/logging.html#logging-levels

``-no_mail``
    Flag, disables email report at the end of execution.

    .. code-block:: bash

        bash$ genietelemetry /path/to/testbed.yaml
                             -configuration /path/to/config.yaml
                             -no_mail

``-email_domain``
    Default email domain for emailing. Required argument for email or
    notification.

    .. code-block:: bash

        bash$ genietelemetry /path/to/testbed.yaml
                             -configuration /path/to/config.yaml
                             -email_domain cisco.com
                             -smtp_host cisco.com

``-smtp_host``
    SMTP host for emailing. Required argument for email or
    notification.

    .. code-block:: bash

        bash$ genietelemetry /path/to/testbed.yaml
                             -configuration /path/to/config.yaml
                             -email_domain cisco.com
                             -smtp_host cisco.com

``-smtp_port``
    SMTP port for emailing. Optional argument for email or
    notification. (Default: 25)

    .. code-block:: bash

        bash$ genietelemetry /path/to/testbed.yaml
                             -configuration /path/to/config.yaml
                             -email_domain cisco.com
                             -smtp_host cisco.com
                             -smtp_port 25

``-mailto``
    Provides a list of recipients that receive email report at the
    end of the run. Supports using either white-space, comma or semi-colon as
    the delimiter, and supports either user ids or full email addresses.
    (default: current user)

    .. code-block:: bash

        bash$ genietelemetry /path/to/testbed.yaml
                             -configuration /path/to/config.yaml
                             -email_domain cisco.com
                             -smtp_host cisco.com
                             -mailto "chambers, psp, crobbins@cisco.com"

``-mail_subject``
    When specified, replaces the default email report subject line.
    (default: ``Monitoring Report - testbed: <name> by: <username>, Status
    <status>``)

    .. code-block:: bash

        bash$ genietelemetry /path/to/testbed.yaml
                             -configuration /path/to/config.yaml
                             -email_domain cisco.com
                             -smtp_host cisco.com
                             -mail_subject "legen -wait-for-it- dary.Legendary!"

``-no_notify``
    Flag, disables notification on abnormal device health staus detected from
    each plugin.

    .. code-block:: bash

        bash$ genietelemetry /path/to/testbed.yaml
                             -configuration /path/to/config.yaml
                             -email_domain cisco.com
                             -smtp_host cisco.com
                             -no_notify

``-notify_subject``
    When specified, replaces the default email notification subject line.
    (default: ``Monitoring Notification - device: <name> plugin: <plugin>
    status: <status>``)

    .. code-block:: bash

        bash$ genietelemetry /path/to/testbed.yaml
                             -configuration /path/to/config.yaml
                             -email_domain cisco.com
                             -smtp_host cisco.com
                             -mail_subject "legen -wait-for-it- dary.Legendary!"

``-runinfo_dir``
    Specifies an alternative location for ``genietelemetry`` execution
    ``runinfo`` directory to store log and result yaml file. Default to current
    folder.

    .. code-block:: bash

        bash$ genietelemetry /path/to/testbed.yaml
                             -configuration /path/to/config.yaml
                             -email_domain cisco.com
                             -smtp_host cisco.com
                             -runinfo_dir /my/runinfo/directory

``-callback_notify``
    Specify Liveview callback notify URI. The Genie Telemetry will stream log
    and execution result over websocket protocol.

    .. code-block:: bash

        bash$ genietelemetry /path/to/testbed.yaml
                             -configuration /path/to/config.yaml
                             -email_domain cisco.com
                             -smtp_host cisco.com
                             -callback_notify http://your.socket.io.server
.. note::

    This argument has prerequisite of ats.liveview package.

.. tip::

    If the uri contains fragment which will be used as part of Authorization
    Header for the Websocket request.

    for example: http://your.socket.io.server#jwt+<Token> will translate into
    Websocket request header: 

    .. code-block::

        Authorization: jwt <Token>


``-timeout``
    Specify each plugin maximum execution length. Default to 300 seconds

    .. code-block:: bash

        bash$ genietelemetry /path/to/testbed.yaml
                             -configuration /path/to/config.yaml
                             -email_domain cisco.com
                             -smtp_host cisco.com
                             -timeout 30

``-connection_timeout``
    Specify connection timeout, if connection class defined at testbed yaml file
    supports timeout argument override.

    .. code-block:: bash

        bash$ genietelemetry /path/to/testbed.yaml
                             -configuration /path/to/config.yaml
                             -email_domain cisco.com
                             -smtp_host cisco.com
                             -connection_timeout 10

.. _genietelemetry_testbed:

Testbed File
------------
Testbed file for Genie Telemetry is slightly different to regular pyATS testbed
yaml file.

- device should contains mandatory key 'os' and has custom abstraction order
  defined for abstraction plugins to work.
- suggested values for 'os' abstraction token are `nxos`, `iosxe`, `iosxr` or
  any token that is used at your genie telemetry plugin.

Example Testbed File

.. code-block:: yaml

    testbed:
        name: sampleTestbed
        tacacs:
            login_prompt: "login:"
            password_prompt: "Password:"
            username: admin
        passwords:
            tacacs: CSCO12345^
            enable:  lab
            line: lab

    devices:
        ott-tb1-n7k4:
            type: Nexus 7000
            alias: device-1
            os: 'nxos'
            connections:
                a:
                  protocol: telnet
                  ip: 10.85.84.80
                  port: 2001
                b:
                  protocol: telnet
                  ip: 10.85.84.80
                  port: 2003
                alt:
                  protocol: telnet
                  ip: 5.19.27.5
            custom:
                abstraction:
                  order: [os]

.. hint::

    Please remember to include default connection class and `abstraction`_ order
    in your testbed YAML file as shown in the example above.

    .. _abstraction: http://wwwin-pyats.cisco.com/cisco-shared/abstract/html/