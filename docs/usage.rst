.. _usage:

============
GenieMonitor
============

    1. Installation
    2. GenieMonitor Launcher
    3. Standard Arguments

Installation
------------
GenieMonitor is hosted on pyATS pypi server. You can install it inside of your
pyATS instance by using command.

.. code-block:: bash

    bash$ pip install geniemonitor

GenieMonitor Launcher
---------------------
GenieMonitor comes with its own launcher: the ``geniemonitor`` executable. This
launcher is installed into your pyATS instance automatically, and is accessible
directly as part of the user PATH after activating your instance.

.. code-block:: bash

    # activate your pyats instance, eg:
    [tony@jarvis:~]$ cd /ws/tony-stark/pyats
    [tony@jarvis:pyats]$ source env.sh

    Activating the pyATS instance @ /ws/tony-stark/pyats
    --------------------------------------------------------------------
    PYTHONPATH=/ws/tony-stark/pyats:
    LD_LIBRARY_PATH=/auto/ttsw/ActiveTcl/8.4.19/lib:/usr/X11R6/lib
    --------------------------------------------------------------------

    # geniemonitor is now part of your path
    (pyats) [tony@jarvis:pyats]$ which geniemonitor
    /ws/tony-stark/pyats/bin/geniemonitor

``geniemonitor`` comes natively with built-in help information:

.. code-block:: bash

    [tony@jarvis:~]$ geniemonitor -h
    usage: geniemonitor [-h] [-testbed_file TESTBEDFILE] [-uid UID] [-loglevel]
                        [-configuration FILE] [-runinfo_dir] [-no_mail]
                        [-no_notify] [-mailto] [-mail_subject] [-notify_subject]
                        [-meta] [-length LENGTH] [-keep_alive] [-upload]
                        [-clean_up] [-upload_via UPLOAD_VIA]
                        [-upload_server UPLOAD_SERVER]
                        [-upload_port UPLOAD_PORT]
                        [-upload_folder UPLOAD_FOLDER]
                        [-upload_timeout UPLOAD_TIMEOUT]

    GenieMonitor command line arguments.

    Example
    -------
      geniemonitor -testbed_file /path/to/testbed.yaml

    ----------------------------------------------------------------------------

    Optional Arguments:
      -testbed_file TESTBEDFILE
                            testbed file to be monitored
      -uid UID              Specify monitoring job uid

    Help:
      -h, -help             show this help message and exit

    Logging:
      -loglevel             geniemonitor logging level
                            eg: -loglevel="INFO"

    Configuration:
      -configuration FILE   configuration yaml file for plugins and settings

    Runinfo:
      -runinfo_dir          specify alternate runinfo directory
      -archive_dir          specify alternate archive directory
      -no_archive           disable archive creation

    Mailing:
      -no_mail              disable report email notifications
      -no_notify            disable notification on device health staus
      -mailto               list of report email recipients
      -mail_subject         report email subject header
      -notify_subject       notification email subject header

    Monitor:
      -meta                 Specify show plugin result meta
      -length LENGTH        Specify monitor length, in XwYdZhPmQs format,
                            X Weeks, Y Days, Z Hours, P Minutes, Q Seconds.
                            ie: 5m20s, default to on demand request
      -keep_alive           Specify keep monitoring alive
                            Stop with Ctrl + C

    Crash Dumps:
      -upload               Specify whether upload core dumps
      -clean_up             Specify whether clear core after upload
      -upload_via UPLOAD_VIA
                            Specify upload protocol
                            default to TFTP
      -upload_server UPLOAD_SERVER
                            Specify upload Server
                            default uses servers information from yaml file
      -upload_port UPLOAD_PORT
                            Specify upload Port
                            default uses servers information from yaml file
      -upload_folder UPLOAD_FOLDER
                            Specify destination folder at remote server
                            default to '/'
      -upload_timeout UPLOAD_TIMEOUT
                            Specify upload timeout value
                            default to 300 seconds

Standard Arguments
------------------
``geniemonitor`` accepts a number of standard arguments that can be used to
influence and/or change monitoring behaviors. All arguments are constructed and
processed using python `argparse`_ module.


.. _argparse: https://docs.python.org/3/library/argparse.html

.. csv-table:: GenieMonitor Standard Arguments
    :header: Argument, Description
    :widths: 30, 70

    ``-testbed_file``, "mandatory argument, full path/name of testbed yaml file
    to monitor with."
    ``-configuration``, "configuration yaml file for plugins and settings"
    ``-uid``, "unique id from upper systems identifying this run"
    ``-loglevel``, "specify the output log level for GenieMonitor"
    ``-runinfo_dir``, "specify alternative runtime info directory location"
    ``-archive_dir``, "specify alternative archive info directory location"
    ``-no_archive``, "flag, disables archive creation"
    ``-no_mail``, "flag, disables email notification at the end of run"
    ``-mailto``, "specify the list of email notification recipients."
    ``-mail_subject``, "email notification subject line."
    ``-no_notify``, "flag, disable notification on abnormal device health staus
    by each plugin."
    ``-notify_subject``, "notification email subject header."
    ``-meta``, "flag, enable to show plugin meta data."
    ``-length``, "specify the monitoring length"
    ``-keep_alive``, "flag, enable indefinite testbed monitoring, stop with
    Ctrl + C"

.. tip::

    ``geniemonitor`` standardizes on single-dash ``-`` style arguments.


``-help``
    Prints help information and how to use each arguments.

    .. code-block:: bash

        bash$ geniemonitor -help

``testbed_file``
    Mandatory argument. Specifies the full path/name to the testbed yaml to
    monitor with. Refer to :ref:`geniemonitor_testbed` for more details.

    .. code-block:: bash

        bash$ geniemonitor -testbed_file /path/to/testbed.yaml

``-configuration``
    optional argument, used to provide the YAML plugin configuration file. Use
    this if you want to configure your GenieMonitor to run certain plugins in
    custom orders for this particular run.

    .. code-block:: bash

        bash$ geniemonitor -testbed_file /path/to/testbed.yaml
                           -configuration /path/to/config.yaml

``-uid``
    optional argument. Allows upstream executor to pass down a unique identifier
    string to be stored in report.

    .. code-block:: bash

        bash$ geniemonitor -testbed_file /path/to/testbed.yaml
                           -uid "this_is_an_example"

``-loglevel``
    Specifies the logging level for GenieMonitor. Use this to increase or
    decrease GenieMonitor module's log output level for debugging purposes. May
    be specified in UPPERCASE or lowercase.

    .. code-block:: bash

        bash$ geniemonitor -testbed_file /path/to/testbed.yaml -loglevel INFO
        bash$ geniemonitor -testbed_file /path/to/testbed.yaml -loglevel DEBUG

.. _log level: https://docs.python.org/3/howto/logging.html#logging-levels

``-no_mail``
    Flag, disables email notification at the end of execution.

    .. code-block:: bash

        bash$ geniemonitor -testbed_file /path/to/testbed.yaml -no_mail

``-mailto``
    Provides a list of recipients that receive email notification at the
    end of the run. Supports using either white-space, comma or semi-colon as
    the delimiter, and supports either user ids or full email addresses.
    (default: current user)

    .. code-block:: bash

        bash$ geniemonitor -testbed_file /path/to/testbed.yaml
                           -mailto "chambers, psp, crobbins@cisco.com"

``-mail_subject``
    When specified, replaces the default email notification subject line.
    (default: ``Monitoring Report - testbed: <name> by: <uid>, total: # (O:#,
    W:#, C:# ...)``)

    .. code-block:: bash

        bash$ geniemonitor -testbed_file /path/to/testbed.yaml
                           -mail_subject "legen -wait-for-it- dary. Legendary!"

``-no_notify``
    Flag, disables notification on abnormal device health staus detected from
    each plugin.

    .. code-block:: bash

        bash$ geniemonitor -testbed_file /path/to/testbed.yaml -no_notify

``-notify_subject``
    When specified, replaces the default email notification subject line.
    (default: ``Monitoring Notification - device: <name> status: <status>``)

    .. code-block:: bash

        bash$ geniemonitor -testbed_file /path/to/testbed.yaml
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

``-meta``
    Flag, enables to show plugin meta data for notification and report.

    .. code-block:: bash

        bash$ geniemonitor -testbed_file /path/to/testbed.yaml -meta

``-length``
    Specify the monitoring length, in XwYdZhPmQs format.
    XwYdZhPmQs translates into X Weeks, Y Days, Z Hours, P Minutes, Q Seconds.
    Default to on demand request.

    .. code-block:: bash

        bash$ geniemonitor -testbed_file /path/to/testbed.yaml -length 20m

``-keep_alive``
    Flag, enables indefinite testbed monitoring, stop with Ctrl + C.

    .. code-block:: bash

        bash$ geniemonitor -testbed_file /path/to/testbed.yaml -keep_alive

.. _geniemonitor_testbed:

Testbed File
------------
Testbed file for GenieMonitor is slightly different to regular pyATS testbed
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