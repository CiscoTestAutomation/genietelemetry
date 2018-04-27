################################################################################
#                                                                              #
#                      Cisco Systems Proprietary Software                      #
#        Not to be distributed without consent from Test Technology            #
#                               Cisco Systems, Inc.                            #
#                                                                              #
################################################################################
#                            genie.telemetry Internal Makefile
#
# Author:
#   Siming Yuan    (siyuan)    - NOSTG
#
# Support:
#	pyats-support@cisco.com
#
# Version:
#   v2.1
#
# Date: 
#   April 2018
#
# About This File:
#   This script will build the genie.telemetry package for distribution in PyPI server
#
# Requirements:
#	1. Module name is the same as package name.
#	2. setup.py file is stored within the module folder
################################################################################

# Variables
BUILD_ROOT    = $(shell pwd)/__build__
OUTPUT_DIR    = $(BUILD_ROOT)/dist
BUILD_CMD     = python setup.py bdist_wheel --dist-dir=$(OUTPUT_DIR)
PROD_USER     = pyadm@pyats-ci
PROD_PKGS     = /auto/pyats/packages/cisco-shared
PROD_SCRIPTS  = /auto/pyats/bin
TESTCMD       = python -m unittest discover -f src/genie/telemetry/tests/
WATCHERS      = python-core@cisco.com
HEADER        = [Watchdog]
PYPIREPO      = pypitest

# Development pkg requirements
DEPENDENCIES  = restview psutil Sphinx wheel asynctest
DEPENDENCIES += setproctitle sphinxcontrib-napoleon sphinx-rtd-theme httplib2 
DEPENDENCIES += pip-tools Cython requests

# Internal variables.
# (note - build examples & templates last because it will fail uploading to pypi
#  due to duplicates, and we'll for now accept that error)
PYPI_PKGS      = genietelemetry

# force cythonize if uploading to pypi
ifeq ($(UPLOADPYPI), true)
	DEVNET = true
	CYTHONIZE = true
endif

ifeq ($(MAKECMDGOALS), devnet)
	DEVNET = true
	CYTHONIZE = true
	INCLUDE_TESTS = false
endif

# build options
ifeq ($(CYTHONIZE), true)
	BUILD_CMD += --cythonize
endif

ifeq ($(INCLUDE_TESTS), true)
	BUILD_CMD += --include-tests
endif

# build options
ifeq ($(DEVNET), true)
	BUILD_CMD += --devnet
endif

# add upload flag ONLY if it's a devnet build, cythonized and asked for upload
ifeq ($(DEVNET)$(CYTHONIZE)$(UPLOADPYPI), truetruetrue)
	BUILD_CMD += upload -r $(PYPIREPO)
endif


.PHONY: help docs distribute_docs clean check\
	    develop undevelop distribute test $(PYPI_PKGS)

help:
	@echo "Please use 'make <target>' where <target> is one of"
	@echo ""
	@echo "     --- common actions ---"
	@echo ""
	@echo "	check                check setup.py content"
	@echo " clean                remove the build directory ($(BUILD_ROOT))"
	@echo " help                 display this help"
	@echo " test                 run all unittests in an efficient manner"
	@echo " develop              set all package to development mode"
	@echo " undevelop            unset the above development mode"
	@echo ""
	@echo "     --- build all targets ---"
	@echo ""
	@echo " all                  make all available pyATS packages"
	@echo ""
	@echo "     --- build specific targets ---"
	@echo ""
	@echo " genietelemetry       build genie telemetry package"
	@echo ""
	@echo "     --- distributions to production environment ---"
	@echo ""
	@echo " distribute           distribute built pkgs to production server"
	@echo ""
	@echo "     --- redirects ---"
	@echo " docs             create all documentation locally. This the same as"
	@echo "                  running 'make docs' in ./docs/"
	@echo " distribute_docs  release local documentation to website. This is"
	@echo "                  the same as running 'make distribute' in ./docs/"
	@echo ""
	@echo "     --- build arguments ---"
	@echo " DEVNET=true              build for devnet style (cythonized, no ut)"
	@echo " CYTHONIZE=true           build cythonized package"
	@echo " INCLUDE_TESTS=true       build include unittests in cythonized pkgs"

docs:
	@echo ""
	@echo "--------------------------------------------------------------------"
	@echo "Building Docs"
	@sphinx-build -b html -c docs/ -d ./__build__/documentation/doctrees docs/ ./__build__/documentation/html
	@echo ""
	@echo "Done."
	@echo ""

distribute_docs:
	@echo ""
	@echo "--------------------------------------------------------------------"
	@echo "Redirecting make distribute_html to ./docs"
	@cd ./docs && make distribute

clean:
	@echo ""
	@echo "--------------------------------------------------------------------"
	@echo "Removing make directory: $(BUILD_ROOT)"
	@rm -rf $(BUILD_ROOT)
	@python setup.py clean
	@echo "Removing *.pyc *.c and __pycache__/ files"
	@find . -type f -name "*.pyc" | xargs rm -vrf
	@find . -type f -name "*.c" | xargs rm -vrf
	@find . -type d -name "__pycache__" | xargs rm -vrf
	@echo ""
	@echo "Done."
	@echo ""

develop:
	@echo ""
	@echo "--------------------------------------------------------------------"
	@echo "Installing development dependencies"
	@pip install $(DEPENDENCIES)
	@echo ""
	@echo "--------------------------------------------------------------------"
	@echo "Setting up development environment"
	@./setup.py develop --no-deps -q
	@echo ""
	@echo "Done."
	@echo ""

undevelop:
	@echo ""
	@echo "--------------------------------------------------------------------"
	@echo "Removing development environment"
	@./setup.py develop --no-deps -q --uninstall
	@echo ""
	@echo "Done."
	@echo ""

distribute: 
	@echo ""
	@echo "--------------------------------------------------------------------"
	@echo "Copying all distributable to $(PROD_PKGS)"
	@test -d $(BUILD_ROOT) || { echo "Nothing to distribute! Exiting..."; exit 1; }
	@echo "Organizing distributable into folders"
	@python tools/organize_dist.py --dist $(OUTPUT_DIR)
	@echo "Distributing..."
	@rsync -rtlv --progress $(OUTPUT_DIR)/* $(PROD_USER):$(PROD_PKGS)/pyats
	@echo -e "The following pyATS packages were distributed by ${USER} to \
	$(PROD_USER):$(PROD_PKGS)/pyats\n\n\
	`ls -1 $(OUTPUT_DIR)/*/*`\n\n\
	-----------------------------------------------------------------------\n\n\
	Distribution Environment:\n\n\
	`git status --`\n\n\
	-----------------------------------------------\n\n\
	`git log -n 1 --stat --`\n\n" | \
	mail -s "$(HEADER) pyATS Package Distribution by ${USER}" $(WATCHERS)
	@echo ""
	@echo "Done."
	@echo ""

genietelemetry:
	@echo ""
	@echo "--------------------------------------------------------------------"
	@echo "Building genie.telemetry Namespace Package"

	mkdir -p $(OUTPUT_DIR)/
	$(BUILD_CMD)

	@echo "Completed building genie.telemetry Namespace Package"
	@echo ""

test:
	@echo ""
	@echo "--------------------------------------------------------------------"
	@echo "Running all unit tests..."
	@echo ""

	@$(TESTCMD) 

	@echo "Completed unit testing"
	@echo ""

check:
	@echo ""
	@echo "--------------------------------------------------------------------"
	@echo "Checking setup.py consistency..."
	@echo ""

	@python setup.py check

	@echo "Done"
	@echo ""
