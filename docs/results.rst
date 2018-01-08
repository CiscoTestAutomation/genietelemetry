.. highlightlang:: python

.. _telemetry_result_objects:

Health Status Objects
=====================

This guide will cover the basics of how Telemetry health status work: the
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
    #   Telemetry health status objects

    from telemetry.results import OK, CRITICAL

    # rolling up OK + CRITICAL yields CRITICAL
    OK + CRITICAL
    # Critical

HealthStatus Objects
--------------------

HealthStatus in Telemetry are represented by 5 unique instances of
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
    from telemetry.results import (OK, WARNING, CRITICAL, PARTIAL, ERRORED)

    # or you can also import them altogether using * wildcard
    # the module has code that specifically limits this to be the same as
    # the localized import statement above
    from telemetry.results import *

All status singleton objects are instances of ``HealthStatus`` class, e,g:

.. code-block:: python

    # Example
    # -------
    #
    #   status singleton objects (HealthStatus)

    # note that for all intents and purposes:
    #   - always use the pre-created bjects
    #
    # this here is only for demonstration purposes.

    # let's import the base class HealthStatus
    # (all results objects are instances of HealthStatus class)
    from telemetry.results import HealthStatus

    # result objects are instances of HealthStatus
    type(OK)
    # <class 'telemetry.results.status.HealthStatus'>

    # and demonstrate these are singletons
    # eg - Passed (code 1) is created via TestResult(1)
    OK is HealthStatus(0)
    # True
    WARNING is TestResult(1)
    # True


.. tip::

    do not instantiate more ``HealthStatus`` objects. All the supported status
    types are already pre-created for you and should be imported and used
    directly. As singleton objects, instantiating ``HealthStatus`` class
    multiple times has no effect anyway. The above code only shows the
    class to help users understand the status object types and where they
    came from.


Object Attributes
-----------------

``HealthStatus`` objects have the following attributes:

code
    integer equivalent of this status type

name
    the string equivalent of this status type


.. code-block:: python

    # Example
    # -------
    #
    #    using Telemetry status objects

    # import all of them
    from telemetry.results import OK, CRITICAL

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



Status Rollups
--------------

Status roll-up is the act of combining one or more status together and
yielding a new, summary result. Rolling up status with ``results`` module
objects is as simple as adding them together using the Python ``+`` operator.

.. code-block:: python

    # Example
    # -------
    #
    #   rolling multiple status objects

    # import all status codes
    from telemetry.results import (OK, WARNING, CRITICAL, PARTIAL, ERRORED)

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
    from telemetry.results import (OK, WARNING, CRITICAL, PARTIAL, ERRORED)

    # consider this
    OK + WARNING + CRITICAL + PARTIAL

    # the same as performing
    status = OK + WARNING
    status = status + CRITICAL
    status = status + PARTIAL

