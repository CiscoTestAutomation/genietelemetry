.. highlightlang:: python

.. _genietelemetry_status_objects:

Health Status Objects
=====================

This guide will cover the basics of how Genie Telemetry health status work: the
different types of status, their corresponding code, and how they roll up
together.


Introduction
------------

Similar to the most test infrastructures, health status are quantified in the
following types ``OK``, ``WARNING``, ``CRITICAL``, ``PARTIAL`` or ``ERRORED``.

.. code-block:: python

    # Example
    # -------
    #
    #   Genie Telemetry health status objects

    from genie.telemetry.status import OK, CRITICAL

    # rolling up OK + CRITICAL yields CRITICAL
    OK + CRITICAL
    # Critical

HealthStatus Objects
--------------------

HealthStatus in Genie Telemetry are represented by 5 unique instances of
``HealthStatus`` `singleton`_ objects, each corresponding to a unique health
status type.

.. _singleton: http://en.wikipedia.org/wiki/Singleton_pattern


``OK``
    indicating that a device/plugin execution was successful, passing, health
    status accepted... etc.

``WARNING``
    indicating that a device/plugin execution was somewhat unsuccessful,
    reaching warning threshold... etc.

``CRITICAL``
    indicating that a device/plugin execution was uterly unsuccessful, reaching
    critical threshold... etc.

``PARTIAL``
    indicating that a device/plugin execution was partially successful... etc.

``ERRORED``
    a mistake or inaccuracy. E.g. an unexpected ``Exception``. The difference
    between failure and error is that failure represents carrying out an event
    as planned with the status not meeting expectation, whereas errored means
    something gone wrong in the course of carrying out that procedure.


Import & Usage
--------------

These 5 `singleton`_ health status objects can be imported into your code to be
used directly. As simple as:

.. code-block:: python

    # Example
    # -------
    #
    #   importing health status objects

    # import each health status object individually
    from genie.telemetry.status import (OK, WARNING, CRITICAL, PARTIAL, ERRORED)

    # or you can also import them altogether using * wildcard
    # the module has code that specifically limits this to be the same as
    # the localized import statement above
    from genie.telemetry.status import *

Object Attributes
-----------------

``HealthStatus`` objects have the following attributes:

code
    integer equivalent of this status type

name
    the string equivalent of this status type

meta
    the meta information associated with this status, keyed by timestamp when
    it happened and the actual information.

.. code-block:: python

    # Example
    # -------
    #
    #    using Genie Telemetry status objects

    # import all of them
    from genie.telemetry.status import OK, CRITICAL

    # getting the status equivalent code
    OK.code
    # 0

    # or get the code by typecasting
    int(OK)
    # 0

    # getting the status name string
    CRITICAL.name
    # critical

    # or typecast into str
    str(CRITICAL)
    # critical

    # getting the meta information associated with the status
    OK('Hello World').meta
    # {'2018-04-18T18:04:35.570472Z': 'Hello World'}

    # the meta information will be rolled up as well
    ( OK('Hello') + CRITICAL('World') ).meta
    # {'2018-04-18T18:08:05.259669Z': 'Hello',
    #  '2018-04-18T18:08:05.259730Z': 'World'}



Status Rollups
--------------

Status roll-up is the act of combining one or more status together and
yielding a new, summary status. Rolling up status with ``status`` module
objects is as simple as adding them together using the Python ``+`` operator.

.. code-block:: python

    # Example
    # -------
    #
    #   rolling multiple status objects

    # import all status codes
    from genie.telemetry.status import (OK, WARNING, CRITICAL, PARTIAL, ERRORED)

    # roll up some status together
    OK + WARNING
    # Warning

    PARTIAL + CRITICAL
    # Critical

    # chaining multiples
    OK + CRITICAL + WARNING
    # Critical

    # assign a status to variable
    status = OK

    # roll up that status against another
    status += WARNING


Roll-up Rules
-------------

When statuses are rolled-up together, their final summary status are calculated
by referencing the chart below:

.. list-table:: Status Roll-up Table
    :header-rows: 1
    :stub-columns: 1

    * - Status
      - ``OK``
      - ``WARNING``
      - ``CRITICAL``
      - ``ERRORED``
      - ``PARTIAL``

    * - ``OK``
      - ``OK``
      - ``WARNING``
      - ``CRITICAL``
      - ``ERRORED``
      - ``PARTIAL``

    * - ``WARNING``
      - ``WARNING``
      - ``WARNING``
      - ``CRITICAL``
      - ``ERRORED``
      - ``WARNING``

    * - ``CRITICAL``
      - ``CRITICAL``
      - ``CRITICAL``
      - ``CRITICAL``
      - ``ERRORED``
      - ``CRITICAL``

    * - ``ERRORED``
      - ``ERRORED``
      - ``ERRORED``
      - ``ERRORED``
      - ``ERRORED``
      - ``ERRORED``

    * - ``PARTIAL``
      - ``PARTIAL``
      - ``WARNING``
      - ``CRITICAL``
      - ``ERRORED``
      - ``PARTIAL``

.. note::
    To read the table, take the first row with the first column. Pick any
    status of the first row with any status of the first column, find the
    cross point, and this is the status you would get after roll up.

    Here is an example on how to read the table :
    ``CRITICAL`` + ``WARNING`` = ``CRITICAL``

When multiple statuses are added together in a single line, consider that
operation to be the same as breaking it down to multiple intermediate two-item
roll-ups:

.. code-block:: python

    # Example
    # -------
    #
    #   performing multiple rollups

    # import all status codes
    from genie.telemetry.status import (OK, WARNING, CRITICAL, PARTIAL, ERRORED)

    # consider this
    OK + WARNING + CRITICAL + PARTIAL

    # the same as performing
    status = OK + WARNING
    status = status + CRITICAL
    status = status + PARTIAL

