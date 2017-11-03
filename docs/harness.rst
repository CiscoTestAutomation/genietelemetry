.. highlightlang:: python

.. _harness:

GenieMonitor and pyATS/Genie
============================

This guide will cover the basics of how to integrate GenieMonitor with
pyATS/Genie.


Introduction
------------

In order to integrate GenieMonitor with pyATS/Genie, a GenieMonitorRunner plugin
needs to be added to easypy through easypy config file.

.. code-block:: yaml

    # Example
    # -------
    #
    #   Easypy config file

    plugins:
        GenieMonitorRunner:
          enabled: True
          module: geniemonitor.runner
          order: 1.0

The file can be stored at pyATS $VIRTUAL_ENV as easypy_config.yaml, or called as
part of easypy command.

.. code-block:: bash

    easypy your_easypy_job.py -configuration /path/to/easypy/config.yaml

The processor definition should be append to your geniemonitor config yaml file.
The supported schema is as following:

.. code-block:: yaml

    processors:
        <your processor name>: [<list of plugin name>]


.. note::
    processor with empty list of plugins will have all monitoring plugins
    blinded to the testbed.

To call the processor inside of your testscript.
You should always import GenieMonitorRunner and calls the defined processor.

.. code-block:: python

    from ats import aetest
    from geniemonitor.runner import GenieMonitorRunner

    class HelloWorldTestcase(aetest.Testcase):

        @aetest.processors.pre(GenieMonitorRunner.processor_pre)
        @aetest.test
        def Hello(self):
            pass