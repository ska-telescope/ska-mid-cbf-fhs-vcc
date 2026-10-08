FROM python:3.14-slim

ARG ci_poetry_version

RUN apt-get update && apt-get -y install curl build-essential git
RUN pip install --upgrade pip

ENV PATH /opt/poetry/bin:$PATH

RUN mkdir -p /ska-mid-cbf-fhs-vcc/

COPY . /ska-mid-cbf-fhs-vcc

WORKDIR /ska-mid-cbf-fhs-vcc/

RUN git submodule init
RUN git submodule update

ENV PIP_REQUESTS_TIMEOUT 30

RUN pip install uv
RUN uv venv --python 3.14
RUN uv sync --active
RUN ls -la
