# Use bash shell with pipefail option enabled so that the return status of a
# piped command is the value of the last (rightmost) commnand to exit with a
# non-zero status. This lets us pipe output into tee but still exit on test
# failures.
SHELL = /bin/bash
.SHELLFLAGS = -o pipefail -c

# W503: "Line break before binary operator." Disabled to work around a bug in flake8 where currently both "before" and "after" are disallowed.
PYTHON_SWITCHES_FOR_FLAKE8 = --ignore=DAR201,W503

# F0002, F0010: Astroid errors. Not our problem.
# E0401: Import errors. Ignore for now until we figure out our actual project structure.
# E0611: Name not found in module. This occurs in our pipeline because the image we pull down uses an older version of Python; we should remove this immediately once we have our image building to CAR.
PYTHON_SWITCHES_FOR_PYLINT = --disable=E0401,E0611,F0002,F0010
PYTHON_SWITCHES_FOR_PYLINT_LOCAL = --disable=E0401,F0002,F0010

#
# include makefile to pick up the standard Make targets, e.g., 'make build'
# build, 'make push' docker push procedure, etc. The other Make targets
# ('make interactive', 'make test', etc.) are defined in this file.
#

include .make/*.mk

all: test lint

# The following steps copy across useful output to this volume which can
# then be extracted to form the CI summary for the test procedure.
test:

	 python setup.py test | tee ./build/setup_py_test.stdout; \
	 mv coverage.xml ./build/reports/code-coverage.xml;

# The following steps copy across useful output to this volume which can
# then be extracted to form the CI summary for the test procedure.
lint:

	# FIXME pylint needs to run twice since there is no way go gather the text and junit xml output at the same time
	pip3 install pylint2junit; \
	pylint --output-format=parseable src/ska/skeleton | tee ./build/code_analysis.stdout; \
	pylint --output-format=pylint2junit.JunitReporter src/ska/skeleton > ./build/reports/linting.xml;


.PHONY: all test lint

NOTEBOOK_IGNORE_FILES = not notebook.ipynb

