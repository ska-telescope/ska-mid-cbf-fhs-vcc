ARG BUILD_IMAGE=harbor.skao.int/production/ska-build-python:0.3.1
ARG BASE_IMAGE=harbor.skao.int/production/ska-tango-images-tango-python:0.3.0
FROM $BUILD_IMAGE AS build

ENV VIRTUAL_ENV=/app \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1


RUN set -xe; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        python3-venv; \
    python3 -m venv $VIRTUAL_ENV; \
    mkdir /build; \
    ln -s $VIRTUAL_ENV /build/.venv

ENV PATH=$VIRTUAL_ENV/bin:$PATH

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
RUN sed -i 's|^ska-mid-cbf-fhs-common\s*=\s*.*$|ska-mid-cbf-fhs-common = "0.1.2"|g' pyproject.toml

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

ENV VIRTUAL_ENV=/app
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY --from=build $VIRTUAL_ENV $VIRTUAL_ENV

LABEL int.skao.image.team=cipa-halifax \
      int.skao.image.authors=jason.turner@mda.space \
      int.skao.image.url=gitlab \
      description="desc" \
      license=licence

USER root

RUN rm -rf /app/lib/python3.10/site-packages/ska_mid_cbf_fhs_common/*
COPY ./temp-common/src/ska_mid_cbf_fhs_common /app/lib/python3.10/site-packages/ska_mid_cbf_fhs_common
RUN chmod -R 777 /app/lib/python3.10/site-packages/ska_mid_cbf_fhs_common

RUN apt-get update && \
  apt-get install -y apt-transport-https ca-certificates curl gnupg && \
  curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.31/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg && \
  chmod 644 /etc/apt/keyrings/kubernetes-apt-keyring.gpg && \
  echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.31/deb/ /' | tee /etc/apt/sources.list.d/kubernetes.list && \
  chmod 644 /etc/apt/sources.list.d/kubernetes.list

RUN apt-get update && \
  apt-get install -y kubectl

USER tango 
