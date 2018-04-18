.. highlightlang:: python

.. _harness:

Genie Telemetry and pyATS/Genie
===============================

This guide will cover the basics of how to integrate Genie Telemetry with
pyATS/Genie.

.. sidebar:: Helpful Reading

    - `Preprocessors`_
    - `Decorators`_

.. _Decorators: https://wiki.python.org/moin/PythonDecorators
.. _Preprocessors: http://en.wikipedia.org/wiki/Preprocessor

Introduction
------------

In order to integrate Genie Telemetry with pyATS/Genie, please import and utilze
genie_telemetry_processor in your testscript or your test datafile.

.. code-block:: python

    # Example
    # -------
    #
    #   Test script

    from ats import aetest
    from genie.telemetry import prepostprocessor

    class common_setup(aetest.CommonSetup):

        @aetest.subsection
        @aetest.processors(post = [genie_telemetry_processor])
        def make_connection(self, testbed):
            pass

    class tc_one(aetest.Testcase):

        @aetest.test
        @aetest.processors(post = [genie_telemetry_processor])
        def test(self):
            pass

    class common_cleanup(aetest.CommonCleanup):

        @aetest.subsection
        @aetest.processors(pre = [genie_telemetry_processor])
        def disconnect(self):
            pass

.. note::

    Please ensure the device connections have been established before genie
    telemetry processor is executed. A good place to add the processor will be
    the post processor stage after testbed connection setup.

    Please ensure genie_telemetry_processor is also part of common cleanup in
    order to have the result yaml file rendered. A good place to add the
    processor will be the pre processor stage before disconnect testbed.


The genie telemetry processor will initialize the genie telemetry and execute
telemetry plugins defined at your genie telemetry config yaml file which should
be passed in as part of easypy command.

.. code-block:: bash

    easypy easypy_job.py --genietelemetry /path/to/genie/telemetry/config.yaml

To customize which plugin to execute or not execute genie_telemetry_processor
for certain testcase, the following parameters needs to be defined at class
level.

.. code-block:: python

    class tc_two(aetest.Testcase):

        # skip genie telemetry processor for testcase tc_two
        parameters = {'genie_telemetry':False}

        # even tho the processor is defined however the execution will be
        # skipped
        @aetest.test
        @aetest.processors(post = [genie_telemetry_processor])
        def test(self):
            pass

    class tc_three(aetest.Testcase):

        # only execute telemetry plugin 'tracebackcheck' for testcase tc_three
        parameters = {'telemetry_plugins':['tracebackcheck']}

        @aetest.test
        @aetest.processors(post = [genie_telemetry_processor])
        def test(self):
            pass

    class tc_four(aetest.Testcase):

        @aetest.test
        def test(self):
            pass

.. note::
    telemetry_plugins with empty list, or not declare telemetry_plugins will
    have all genie telemetry plugins blinded to the testcase.

    Defining keyword genie_telemetry as False gives you finer control over
    testcase level processor execution if genie_telemetry_processor is declared
    as a global processor.



Example Datafile
----------------

.. code-block:: yaml

    # Example
    # -------
    #
    #   the following is an example datafile yaml file

    common_setup:   

        processors:
            post:
                - genie.telemetry.genie_telemetry_processor
    testcases:
        MyTestcase_One:

            parameters:
                telemetry_plugins: ['tracebackcheck']

            processors:
                post:
                    - genie.telemetry.genie_telemetry_processor

        MyTestcase_Two:

            parameters:
                input_x: 2000
                input_y: 3000

        MyTestcase_Three:

            parameters:
                telemetry_plugins: ['interfaceupcheck']

            processors:
                post:
                    - genie.telemetry.genie_telemetry_processor

    common_cleanup:

        processors:
            pre:
                - genie.telemetry.genie_telemetry_processor
