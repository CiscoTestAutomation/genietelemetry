###############################################################################
#                            telemetry Internal Makefile
#
# Author:
#
# Support:
#	pyats-support@cisco.com
#
# Version:
#   v1.0.0
#
# Date: 
#   October 2017
#
# About This File:
#   This script will build the telemetry package for distribution in PyPI
#   server
#
# Requirements:
#	1. Module name is the same as package name.
#	2. setup.py file is stored within the module folder
###############################################################################

# Variables
PKG_NAME      = telemetry
BUILDDIR      = $(shell pwd)/__build__
PROD_USER     = pyadm@pyats-ci
PROD_PKGS     = /auto/pyats/packages/cisco-shared
PYTHON        = python
TESTCMD       = python -m unittest discover tests
DISTDIR       = $(BUILDDIR)/dist

.PHONY: clean package distribute develop undevelop help docs tests

help:
	@echo "Please use 'make <target>' where <target> is one of"
	@echo ""
	@echo "package         : Build the package"
	@echo "test            : Test the package"
	@echo "distribute      : Distribute the package to PyPi server"
	@echo "clean           : Remove build artifacts"
	@echo "develop         : Build and install development package"
	@echo "undevelop       : Uninstall development package"

test:
	@$(TESTCMD)

package: 
	@echo ""
	@echo "--------------------------------------------------------------------"
	@echo "Building $(PKG_NAME) distributable: $@"
	@echo ""

	@mkdir -p $(DISTDIR)
	@./setup.py test
    
    # NOTE : Only specify --universal if the package works for both py2 and py3
    # https://packaging.python.org/en/latest/distributing.html#universal-wheels
	@./setup.py bdist_wheel --dist-dir=$(DISTDIR) 

	@echo ""
	@echo "Completed building: $@"
	@echo ""

develop: 
	@echo ""
	@echo "--------------------------------------------------------------------"
	@echo "Building and installing $(PKG_NAME) development distributable: $@"
	@echo ""

	@./setup.py develop --no-deps -q

	@echo ""
	@echo "Completed building and installing: $@"
	@echo ""

undevelop: 
	@echo ""
	@echo "--------------------------------------------------------------------"
	@echo "Uninstalling $(PKG_NAME) development distributable: $@"
	@echo ""

	@./setup.py develop --no-deps -q --uninstall

	@echo ""
	@echo "Completed uninstalling: $@"
	@echo ""

clean:
	@echo ""
	@echo "--------------------------------------------------------------------"
	@echo "Removing make directory: $(BUILDDIR)"
	@rm -rf $(BUILDDIR)
	@echo ""
	@echo "Removing build artifacts ..."
	@./setup.py clean
	@echo ""
	@echo "Done."
	@echo ""

distribute: 
	@echo ""
	@echo "--------------------------------------------------------------------"
	@echo "Copying all distributable to $(PROD_PKGS)"
	@test -d $(DISTDIR) || { echo "Nothing to distribute! Exiting..."; exit 1; }
	@ssh -q $(PROD_USER) 'test -e $(PROD_PKGS)/$(PKG_NAME) || mkdir $(PROD_PKGS)/$(PKG_NAME)'
	@scp $(DISTDIR)/* $(PROD_USER):$(PROD_PKGS)/$(PKG_NAME)/
	@echo ""
	@echo "Done."
	@echo ""

docs:
	@echo ""
	@echo "--------------------------------------------------------------------"
	@echo "Redirecting make docs to ./docs"
	@cd ./docs && make docs
	@echo ""
	@echo "Done."
	@echo ""