FROM ubuntu:22.04

RUN apt-get update && apt install -y git apt-utils software-properties-common build-essential

RUN git clone https://gitlab.com/nurbldoff/boogie.git

RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update && apt install python3.10 python3.10-dev python3.10-distutils python3.10-venv python3-pip -y

RUN python3.10 -m pip install --upgrade pip && \
    python3.10 -m pip install --upgrade setuptools && \
    python3.10 -m pip install certifi

WORKDIR boogie

RUN python3.10 -m pip install .
