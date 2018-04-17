.. _usage:

============
GenieTelemetry
==============

    1. Installation
    2. GenieTelemetry Launcher
    3. Standard Arguments

Installation
------------
``genietelemetry`` package is hosted on the pyATS pypi server. 

``genietelemetry`` package can be installed in two parts. First install the core 
package via pip.

.. code-block:: bash

    bash$ pip install genietelemetry

The user-contributed libraries are downloadable via Git. Execute this command
under your `projects` directory in your pyATS virtual environment `$VIRTUAL_ENV`.

.. code-block:: bash

    cd $VIRTUAL_ENV/projects
    git clone ssh://git@bitbucket-eng-sjc1.cisco.com:7999/pyats-proj/genietelemetry_libs.git


GenieTelemetry Launcher
-----------------------
GenieTelemetry comes with its own launcher: the ``genietelemetry`` executable.
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
                          [-notify_subject]

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


Standard Arguments
------------------
``genietelemetry`` accepts a number of standard arguments that can be used to
influence and/or change monitoring behaviors. All arguments are constructed and
processed using python `argparse`_ module.


.. _argparse: https://docs.python.org/3/library/argparse.html

.. csv-table:: GenieTelemetry Standard Arguments
    :header: Argument, Description
    :widths: 30, 70

    ``-testbed_file``, "mandatory argument, full path/name of testbed yaml file
    to monitor with."
    ``-configuration``, "configuration yaml file for plugins and settings"
    ``-uid``, "unique id from upper systems identifying this run"
    ``-loglevel``, "specify the output log level for GenieTelemetry"
    ``-runinfo_dir``, "specify alternative runtime info directory location"
    ``-archive_dir``, "specify alternative archive info directory location"
    ``-no_archive``, "flag, disables archive creation"
    ``-no_mail``, "flag, disables email notification at the end of run"
    ``-mailto``, "specify the list of email notification recipients."
    ``-mail_subject``, "email notification subject line."
    ``-no_notify``, "flag, disable notification on abnormal device health staus
    by each plugin."
    ``-notify_subject``, "notification email subject header."
    ``-no_meta``, "flag, enable to hide plugin meta data."
    ``-length``, "specify the monitoring length"
    ``-keep_alive``, "flag, enable indefinite testbed monitoring, stop with
    Ctrl + C"

.. tip::

    ``genietelemetry`` standardizes on single-dash ``-`` style arguments.


``-help``
    Prints help information and how to use each arguments.

    .. code-block:: bash

        bash$ genietelemetry -help

``testbed_file``
    Mandatory argument. Specifies the full path/name to the testbed yaml to
    monitor with. Refer to :ref:`genietelemetry_testbed` for more details.

    .. code-block:: bash

        bash$ genietelemetry -testbed_file /path/to/testbed.yaml

``-configuration``
    optional argument, used to provide the YAML plugin configuration file. Use
    this if you want to configure your GenieTelemetry to run certain plugins in
    custom orders for this particular run.

    .. code-block:: bash

        bash$ genietelemetry -testbed_file /path/to/testbed.yaml
                             -configuration /path/to/config.yaml

``-uid``
    optional argument. Allows upstream executor to pass down a unique identifier
    string to be stored in report.

    .. code-block:: bash

        bash$ genietelemetry -testbed_file /path/to/testbed.yaml
                           -uid "this_is_an_example"

``-loglevel``
    Specifies the logging level for GenieTelemetry. Use this to increase or
    decrease GenieTelemetry module's log output level for debugging purposes.
    May be specified in UPPERCASE or lowercase.

    .. code-block:: bash

        bash$ genietelemetry -testbed_file /path/to/testbed.yaml -loglevel INFO
        bash$ genietelemetry -testbed_file /path/to/testbed.yaml -loglevel DEBUG

.. _log level: https://docs.python.org/3/howto/logging.html#logging-levels

``-no_mail``
    Flag, disables email notification at the end of execution.

    .. code-block:: bash

        bash$ genietelemetry -testbed_file /path/to/testbed.yaml -no_mail

``-mailto``
    Provides a list of recipients that receive email notification at the
    end of the run. Supports using either white-space, comma or semi-colon as
    the delimiter, and supports either user ids or full email addresses.
    (default: current user)

    .. code-block:: bash

        bash$ genietelemetry -testbed_file /path/to/testbed.yaml
                             -mailto "chambers, psp, crobbins@cisco.com"

``-mail_subject``
    When specified, replaces the default email notification subject line.
    (default: ``Monitoring Report - testbed: <name> by: <uid>, total: # (O:#,
    W:#, C:# ...)``)

    .. code-block:: bash

        bash$ genietelemetry -testbed_file /path/to/testbed.yaml
                             -mail_subject "legen -wait-for-it- dary. Legendary!"

``-no_notify``
    Flag, disables notification on abnormal device health staus detected from
    each plugin.

    .. code-block:: bash

        bash$ genietelemetry -testbed_file /path/to/testbed.yaml -no_notify

``-notify_subject``
    When specified, replaces the default email notification subject line.
    (default: ``Monitoring Notification - device: <name> status: <status>``)

    .. code-block:: bash

        bash$ genietelemetry -testbed_file /path/to/testbed.yaml
                           -mail_subject "legen -wait-for-it- dary. Legendary!"

``-runinfo_dir``
    Specifies an alternative location for ``easypy`` execution ``runinfo``
    directory.

    .. code-block:: bash

        bash$ easypy /path/to/jobfile.py -runinfo_dir /my/runinfo/directory

``-archive_dir``
    Specifies an alternative location for ``easypy`` execution ``archive``
    directory.

    .. code-block:: bash

        bash$ easypy /path/to/jobfile.py -archive_dir /my/archive/directory

``-no_archive``
    Flag, disables archive creation

    .. code-block:: bash

        bash$ easypy /path/to/jobfile.py -no_archive

``-no_meta``
    Flag, enables to hide plugin meta data for notification and report.

    .. code-block:: bash

        bash$ genietelemetry -testbed_file /path/to/testbed.yaml -no_meta

``-length``
    Specify the monitoring length, in XwYdZhPmQs format.
    XwYdZhPmQs translates into X Weeks, Y Days, Z Hours, P Minutes, Q Seconds.
    Default to on demand request.

    .. code-block:: bash

        bash$ genietelemetry -testbed_file /path/to/testbed.yaml -length 20m

``-keep_alive``
    Flag, enables indefinite testbed monitoring, stop with Ctrl + C.

    .. code-block:: bash

        bash$ genietelemetry -testbed_file /path/to/testbed.yaml -keep_alive

.. _genietelemetry_testbed:

Testbed File
------------
Testbed file for GenieTelemetry is slightly different to regular pyATS testbed
yaml file.

- device should contains mandatory key 'os' and has custom abstraction order
  defined for abstraction plugins to work.
- suggested values for 'os' abstraction token are `nxos`, `iosxe` and `iosxr`.

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

    Please remember to include `unicon`_ and `abstraction`_ order in your testbed
    YAML file as shown in the example above.
    
    .. _unicon: http://wwwin-pyats.cisco.com/cisco-shared/unicon/latest/
    .. _abstraction: http://wwwin-pyats.cisco.com/cisco-shared/abstract/html/