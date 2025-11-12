# Use bash shell with pipefail option enabled so that the return status of a
# piped command is the value of the last (rightmost) commnand to exit with a
# non-zero status. This lets us pipe output into tee but still exit on test
# failures.
SHELL = /bin/bash
.SHELLFLAGS = -o pipefail -c

export DEBUG_DIRTY=true

#
# Project makefile for ska-mid-cbf-mcs project. 
PROJECT = ska-mid-cbf-fhs-vcc

KUBE_NAMESPACE ?= ska-mid-cbf## KUBE_NAMESPACE defines the Kubernetes Namespace that will be deployed to using Helm
SDP_KUBE_NAMESPACE ?= ska-mid-cbf-sdp##namespace to be used
DASHBOARD ?= webjive-dash.dump
CLUSTER_DOMAIN ?= cluster.local
FHS_SERVER_ID ?= fhs01
CONFIG_LOCATION ?= /app/mnt/lowLevelConfigMap

HELM_RELEASE ?= test##H ELM_RELEASE is the release that all Kubernetes resources will be labelled with

OCI_IMAGES = ska-mid-cbf-fhs-vcc
OCI_IMAGES_TO_PUBLISH ?= $(OCI_IMAGES)
OCI_IMAGE_BUILD_CONTEXT = $(PWD)

HELM_CHART ?= ska-mid-cbf-umbrella## HELM_CHART the chart name
K8S_CHART ?= $(HELM_CHART)
TANGO_DATABASE = tango-databaseds-$(HELM_RELEASE)
TANGO_HOST = $(TANGO_DATABASE):10000## TANGO_HOST is an input!

K8S_UMBRELLA_CHART_PATH ?= ./charts/ska-mid-cbf-umbrella

CI_REGISTRY ?= gitlab.com/ska-telescope/ska-mid-cbf-fhs-vcc

CI_PROJECT_DIR ?= .

KUBE_CONFIG_BASE64 ?=  ## base64 encoded kubectl credentials for KUBECONFIG
KUBECONFIG ?= /etc/deploy/config ## KUBECONFIG location

# this assumes host and talon board 1g ethernet is on the 192.168 subnet
#HOST_IP = $(shell ip a 2> /dev/null | sed -En 's/127.0.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\2/p' | grep 192.168) 
JIVE ?= false# Enable jive
TARANTA ?= false# Enable Taranta
MINIKUBE ?= false ## Minikube or not
K3D ?= false ## K3D or not
EXPOSE_All_DS ?= true ## Expose All Tango Services to the external network (enable Loadbalancer service)
SKA_TANGO_OPERATOR ?= false
ITANGO_ENABLED ?= true## ITango enabled in ska-tango-base

TARANTA_PARAMS = --set ska-taranta.enabled=$(TARANTA) \
				 --set ska-taranta-auth.enabled=$(TARANTA) \
				 --set ska-dashboard-repo.enabled=$(TARANTA)

ifneq ($(MINIKUBE),)
ifneq ($(MINIKUBE),true)
TARANTA_PARAMS = --set ska-taranta.enabled=$(TARANTA) \
				 --set ska-taranta-auth.enabled=true \
				 --set ska-dashboard-repo.enabled=false
endif
endif

ifneq ($(MINIKUBE),)
ifeq ($(MINIKUBE),true)
PV_STORAGE_PARAM = --set ska-mid-cbf-fhs-vcc.pvStorageClass=standard
endif
endif


K8S_CHART_PARAMS = --set global.minikube=$(MINIKUBE) \
	--set global.k3d=$(K3D) \
	--set global.exposeAllDS=$(EXPOSE_All_DS) \
	--set global.tango_host=$(TANGO_HOST) \
	--set global.cluster_domain=$(CLUSTER_DOMAIN) \
	--set global.operator=$(SKA_TANGO_OPERATOR) \
	--set ska-tango-base.itango.enabled=$(ITANGO_ENABLED) \
	--set ska-mid-cbf-fhs-vcc.hostInfo.clusterDomain=$(CLUSTER_DOMAIN) \
	--set ska-mid-cbf-fhs-vcc.hostInfo.fhsServerId=$(FHS_SERVER_ID) \
	--set ska-mid-cbf-fhs-vcc.hostInfo.configLocation=$(CONFIG_LOCATION) \
	--set ska-mid-cbf-fhs-vcc.hostInfo.namespace=$(KUBE_NAMESPACE) \
	${TARANTA_PARAMS} \
	${PV_STORAGE_PARAM}

# shared lint config file var definitions
LINTCFG_DIR = tools/ska-mid-cbf-linter
PYLINT_CONFIG_FILE = $(LINTCFG_DIR)/.pylintrc
FLAKE8_CONFIG_FILE = $(LINTCFG_DIR)/.flake8
PYTHON_SWITCHES_FOR_FLAKE8 = --config=$(FLAKE8_CONFIG_FILE)
PYTHON_SWITCHES_FOR_PYLINT = --rcfile=$(PYLINT_CONFIG_FILE)
PYTHON_SWITCHES_FOR_PYLINT_LOCAL = --rcfile=$(PYLINT_CONFIG_FILE)

PYTHON_LINE_LENGTH = 160
POETRY_PYTHON_RUNNER = poetry run python3 -m

PYTHON_LINT_TARGET = ./src/
K8S_VARS_AFTER_PYTEST = -s

PYTHON_TEST_FILE = ./tests/unit/

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

python-pre-test:
	export PYTHONPATH=/usr/local/lib/python3.10/dist-packages/ska_mid_cbf_fhs_common/terrabox_software/grpc_driver_system/generated:$PYTHONPATH

check-minikube-eval:
	@minikube status | grep -iE '^.*(docker-env: in-use).*$$'; \
	if [ $$? -ne 0 ]; then \
		echo "Minikube docker-env not active. Please run: 'eval \$$(minikube docker-env)'."; \
		exit 1; \
	else echo "Minikube docker-env is active."; \
	fi

k8s-pre-install-chart:
	@if [ "$(MINIKUBE)" = "true" ]; then make check-minikube-eval; fi;
	rm -f charts/ska-mid-cbf-fhs-vcc/Chart.lock

k8s-deploy:
	make k8s-install-chart MINIKUBE=$(MINIKUBE) DEV=$(DEV) BOOGIE=$(BOOGIE)
	@echo "Waiting for all pods in namespace $(KUBE_NAMESPACE) to be ready..."
	@time kubectl wait pod --selector=app=ska-mid-cbf-fhs-vcc --for=condition=ready --timeout=15m0s --namespace $(KUBE_NAMESPACE)

k8s-deploy-dev: MINIKUBE=true
k8s-deploy-dev: CLUSTER_DOMAIN=cluster.local
k8s-deploy-dev:
	make k8s-deploy MINIKUBE=$(MINIKUBE) CLUSTER_DOMAIN=$(CLUSTER_DOMAIN) DEV=true BOOGIE=true

k8s-destroy:
	make k8s-uninstall-chart
	@echo "Waiting for all pods in namespace $(KUBE_NAMESPACE) to terminate..."
	@time kubectl wait pod --all --for=delete --timeout=5m0s --namespace $(KUBE_NAMESPACE)

build-and-deploy:
	make oci-build-all && make k8s-deploy-dev

build-local-common: COMMON_LIB_PATH = ../ska-mid-cbf-fhs-common
build-local-common:
	cp -r $(COMMON_LIB_PATH) ./temp-common
	-make oci-build-all OCI_IMAGE_FILE_PATH=./devcommon.Dockerfile
	rm -rf ./temp-common

lc-build-and-deploy:
	make build-local-common && make k8s-deploy-dev

format-python:
	$(POETRY_PYTHON_RUNNER) isort --profile black --line-length $(PYTHON_LINE_LENGTH) $(PYTHON_SWITCHES_FOR_ISORT) $(PYTHON_LINT_TARGET)
	$(POETRY_PYTHON_RUNNER) black --exclude .+\.ipynb --line-length $(PYTHON_LINE_LENGTH) $(PYTHON_SWITCHES_FOR_BLACK) $(PYTHON_LINT_TARGET)

fix-python-imports:
	$(POETRY_PYTHON_RUNNER) isort --profile black --line-length $(PYTHON_LINE_LENGTH) $(PYTHON_SWITCHES_FOR_ISORT) $(PYTHON_LINT_TARGET)

lint-python-local:
	mkdir -p build/lint-output
	@echo "Linting..."
	-@ISORT_ERROR=0 BLACK_ERROR=0 FLAKE_ERROR=0 PYLINT_ERROR=0; \
	$(POETRY_PYTHON_RUNNER) isort --check-only --profile black --line-length $(PYTHON_LINE_LENGTH) $(PYTHON_SWITCHES_FOR_ISORT) $(PYTHON_LINT_TARGET) &> build/lint-output/1-isort-output.txt; \
	if [ $$? -ne 0 ]; then ISORT_ERROR=1; fi; \
	$(POETRY_PYTHON_RUNNER) black --exclude .+\.ipynb --check --line-length $(PYTHON_LINE_LENGTH) $(PYTHON_SWITCHES_FOR_BLACK) $(PYTHON_LINT_TARGET) &> build/lint-output/2-black-output.txt; \
	if [ $$? -ne 0 ]; then BLACK_ERROR=1; fi; \
	$(POETRY_PYTHON_RUNNER) flake8 --show-source --statistics --max-line-length $(PYTHON_LINE_LENGTH) $(PYTHON_SWITCHES_FOR_FLAKE8) $(PYTHON_LINT_TARGET) &> build/lint-output/3-flake8-output.txt; \
	if [ $$? -ne 0 ]; then FLAKE_ERROR=1; fi; \
	$(POETRY_PYTHON_RUNNER) pylint --output-format=parseable --max-line-length $(PYTHON_LINE_LENGTH) $(PYTHON_SWITCHES_FOR_PYLINT_LOCAL) $(PYTHON_LINT_TARGET) &> build/lint-output/4-pylint-output.txt; \
	if [ $$? -ne 0 ]; then PYLINT_ERROR=1; fi; \
	if [ $$ISORT_ERROR -ne 0 ]; then echo "Isort lint errors were found. Check build/lint-output/1-isort-output.txt for details."; fi; \
	if [ $$BLACK_ERROR -ne 0 ]; then echo "Black lint errors were found. Check build/lint-output/2-black-output.txt for details."; fi; \
	if [ $$FLAKE_ERROR -ne 0 ]; then echo "Flake8 lint errors were found. Check build/lint-output/3-flake8-output.txt for details."; fi; \
	if [ $$PYLINT_ERROR -ne 0 ]; then echo "Pylint lint errors were found. Check build/lint-output/4-pylint-output.txt for details."; fi; \
	if [ $$ISORT_ERROR -eq 0 ] && [ $$BLACK_ERROR -eq 0 ] && [ $$FLAKE_ERROR -eq 0 ] && [ $$PYLINT_ERROR -eq 0 ]; then echo "Lint was successful. Check build/lint-output for any additional details."; fi;

build-docs-local:
	@echo "Cleaning up old build(s)..."
	-@rm -rf docs/src/_code/ska_mid_cbf_fhs_vcc/*.rst
	-@rm -rf ./build/sphinx_local/
	@echo "Generating API docs..."
	-@poetry run sphinx-apidoc -t docs/src/_templates -o docs/src/_code/ska_mid_cbf_fhs_vcc -M -f -d 2 src/ska_mid_cbf_fhs_vcc/
	@echo "Building docs..."
	-@$(POETRY_PYTHON_RUNNER) sphinx -T -b html -d ./build/sphinx_local/cache/doctrees -D language=en ./docs/src ./build/sphinx_local/output
	@echo "Done. Open build/sphinx_local/output/index.html to view the generated docs."

lint-all:
	make fix-python-imports;make format-python;make lint-python-local
	


NOTEBOOK_IGNORE_FILES = not notebook.ipynb

# define private overrides for above variables in here
-include PrivateRules.mk