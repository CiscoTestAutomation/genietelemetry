# Genie Telemetry Library

Genie.Telemetry is a plugin system for collecting statistics and telemetry 
information from devices under test, leveraging Genie libraries and development
methodology.

Multiple plugins have been already developed,

* crashdumps
* tracebackcheck
* alignmentcheck
* cpucheck

## About

Genie is both a library framework and a test harness that facilitates rapid
development, encourage re-usable and simplify writing test automation. Genie
bundled with the modular architecture of pyATS framework accelerates and
simplifies test automation leveraging all the perks of the Python programming
language in an object-orienting fashion.

pyATS is an end-to-end testing ecosystem, specializing in data-driven and
reusable testing, and engineered to be suitable for Agile, rapid development
iterations. Extensible by design, pyATS enables developers to start with small,
simple and linear test cases, and scale towards large, complex and asynchronous
test suites.

Genie was initially developed internally in Cisco, and is now available to the
general public starting early 2018 through [Cisco DevNet].

[Cisco Devnet]: https://developer.cisco.com/


# Installation

This is an optional package for Genie. Install it alongside your environment
where pyATS/Genie is isntalled.

```bash
bash$ pip install genie.telemetry
```

Detailed installation guide can be found on [our website].

[our website]: https://developer.cisco.com/pyats/


# Development

To develop this package, assuming you have Genie already installed in your
environment, follow the commands below:

```bash
# remove the packages
bash$ pip uninstall -y genie.telemetry

# clone this repo
bash$ git clone https://github.com/CiscoTestAutomation/genietelemetry.git

# put all packages in dev mode
bash$ cd genietelemetry
bash$ make develop
```

Now you should be able to develop the files and see it reflected in your runs.
```

