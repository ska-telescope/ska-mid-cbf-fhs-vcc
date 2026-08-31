ARG BUILD_IMAGE=harbor.skao.int/production/ska-build-python:0.3.3
ARG BASE_IMAGE=harbor.skao.int/production/ska-tango-images-tango-python:0.4.1
FROM $BUILD_IMAGE AS build

ENV VIRTUAL_ENV=/app \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1

# # ############################################
# # # Python 3.14
# # ############################################
RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install python3.14-full -y --no-install-recommends && \
    apt-get install python3.14-dev python3.14-venv -y --no-install-recommends && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.14 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.14 1

RUN python3.14 -m venv $VIRTUAL_ENV; \
    mkdir /build; \
    ln -s $VIRTUAL_ENV /build/.venv

ENV PATH=$VIRTUAL_ENV/bin:$PATH

RUN python3.14 -m ensurepip --upgrade && \
    python3.14 -m pip install --upgrade pip && \
    python3.14 -m pip install --upgrade setuptools && \
    python3.14 -m pip install certifi

ENV POETRY_HOME=/opt/poetry
ENV POETRY_VERSION=2.4.0
RUN mkdir -p $POETRY_HOME && curl -sSL https://raw.githubusercontent.com/python-poetry/install.python-poetry.org/main/install-poetry.py --output $POETRY_HOME/install-poetry.py
RUN cd $POETRY_HOME && POETRY_VERSION=${POETRY_VERSION} python3.14 install-poetry.py --yes
RUN ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry
ENV PATH /opt/poetry/bin:$PATH
RUN ls -la ./

ENV PIP_REQUESTS_TIMEOUT 30
ENV POETRY_REQUESTS_TIMEOUT 30

WORKDIR /build

# We install the dependencies and the application in two steps so that the
# dependency installation can be cached by the OCI image builder.  The
# important point is to install the dependencies _before_ we copy in src so
# that changes to the src directory to not result in needlessly reinstalling the
# dependencies.

# Installing the dependencies into /app here relies on the .venv symlink created
# above.  We use poetry to install the dependencies so that we can pass
# `--only main` to avoid installing dev dependencies.  This option is not
# available for pip.
COPY pyproject.toml poetry.lock* ./

RUN poetry lock && poetry install --only main --no-root

# The README.md here must match the `tool.poetry.readme` key in the
# pyproject.toml otherwise the `pip install` step below will fail.
COPY README.md ./
COPY src ./src

# We use pip to install the application because `poetry install` is
# equivalent to `pip install --editable` which creates symlinks to the src
# directory, whereas we want to copy the files.
RUN pip install --no-deps .

# We don't want to copy pip into the runtime image
RUN pip uninstall -y pip

FROM $BASE_IMAGE

USER root

RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install python3.14-full -y --no-install-recommends && \
    apt-get install python3.14-dev python3.14-venv -y --no-install-recommends

USER tango

ENV VIRTUAL_ENV=/app
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY --from=build $VIRTUAL_ENV $VIRTUAL_ENV

USER root

RUN update-alternatives --install $VIRTUAL_ENV/bin/python3 python3 $VIRTUAL_ENV/bin/python3.14 1 && \
    update-alternatives --install $VIRTUAL_ENV/bin/python python $VIRTUAL_ENV/bin/python3.14 1

RUN python3.14 -m ensurepip --upgrade && \
    python3.14 -m pip install --upgrade pip && \
    python3.14 -m pip install --upgrade setuptools && \
    python3.14 -m pip install certifi

USER tango

RUN python3.14 -m ensurepip

LABEL int.skao.image.team=cipa-halifax \
      int.skao.image.authors="Jason Turner <jason.turner@mda.space>, Ben Herriott <ben.herriott@mda.space>, Justin Wamback <justin.wamback@mda.space>" \
      int.skao.image.url=https://gitlab.com/ska-telescope/ska-mid-cbf/monitor-control/ska-mid-cbf-fhs-vcc \
      description="SKA Mid.CBF FHS VCC" \
      license="BSD license"

USER root

ENV LOGS_DIR=/app/logs
RUN mkdir -p $LOGS_DIR
RUN chmod -R 777 $LOGS_DIR

RUN apt-get update && \
  apt-get install -y apt-transport-https ca-certificates curl gnupg && \
  curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.31/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg && \
  chmod 644 /etc/apt/keyrings/kubernetes-apt-keyring.gpg && \
  echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.31/deb/ /' | tee /etc/apt/sources.list.d/kubernetes.list && \
  chmod 644 /etc/apt/sources.list.d/kubernetes.list

RUN apt-get update && \
  apt-get install -y kubectl

RUN python --version

USER tango

RUN python --version
