.. highlightlang:: python

.. _harness:

Telemetry and pyATS/Genie
============================

This guide will cover the basics of how to integrate Telemetry with
pyATS/Genie.


Introduction
------------

In order to integrate Telemetry with pyATS/Genie, a TelemetryRunner plugin
needs to be added to easypy through easypy config file.

.. code-block:: yaml

    # Example
    # -------
    #
    #   Easypy config file

    plugins:
        TelemetryRunner:
          enabled: True
          module: telemetry.runner
          order: 1.0

The file can be stored at pyATS $VIRTUAL_ENV as easypy_config.yaml, or called as
part of easypy command.

.. code-block:: bash

    easypy your_easypy_job.py -configuration /path/to/easypy/config.yaml

The processor definition should be append to your telemetry config yaml file.
The supported schema is as following:

.. code-block:: yaml

    processors:
        <your processor name>: [<list of plugin name>]


.. note::
    processor with empty list of plugins will have all monitoring plugins
    blinded to the testbed.

To call the processor inside of your testscript.
You should always import TelemetryRunner and calls the defined processor.

.. code-block:: python

    from ats import aetest
    from telemetry.runner import TelemetryRunner

    class HelloWorldTestcase(aetest.Testcase):

        @aetest.processors.pre(TelemetryRunner.processor_pre)
        @aetest.test
        def Hello(self):
            pass