FROM python:3.14-slim

ARG ci_poetry_version

RUN apt-get update && apt-get -y install curl build-essential git
RUN pip install --upgrade pip

ENV POETRY_HOME=/opt/poetry
ENV POETRY_VERSION=$ci_poetry_version
RUN mkdir -p $POETRY_HOME && curl -sSL https://raw.githubusercontent.com/python-poetry/install.python-poetry.org/main/install-poetry.py --output $POETRY_HOME/install-poetry.py
RUN cd $POETRY_HOME && POETRY_VERSION=${POETRY_VERSION} python3.14 install-poetry.py --yes
RUN /opt/poetry/bin/poetry --help

RUN ln -sfn /opt/poetry/bin/poetry /usr/local/bin/poetry
ENV PATH /opt/poetry/bin:$PATH

RUN mkdir -p /ska-mid-cbf-fhs-vcc/

COPY . /ska-mid-cbf-fhs-vcc

WORKDIR /ska-mid-cbf-fhs-vcc/

RUN git submodule init
RUN git submodule update

ENV PIP_REQUESTS_TIMEOUT 30
ENV POETRY_REQUESTS_TIMEOUT 30

RUN poetry config virtualenvs.in-project true
RUN poetry config virtualenvs.create true
RUN poetry env use 3.14
RUN poetry lock && poetry install --all-groups --all-extras --no-root
RUN ls -la
