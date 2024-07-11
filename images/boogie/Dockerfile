FROM ubuntu:22.04

ENV local_cert_path="/certs"
ENV img_cert_folder="own-certificates"
ENV primary_cert_name="MDA-cert-bundle"

# Set the timezone to avoid geolocation setting
ENV TZ=Etc/GMT
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

#copy over pip file to allow python extension downloads
COPY /pip.conf /etc/pip.conf

# ###########################################
# # init packages / setup
# ###########################################
RUN apt-get update && apt-get -y upgrade

RUN apt-get --reinstall install ca-certificates -y
RUN update-ca-certificates --fresh

# ###########################################
# # Certificate setup
# ###########################################
RUN mkdir /tmp/tmp_certs /usr/local/share/ca-certificates/${img_cert_folder}
COPY ${local_cert_path} /tmp/tmp_certs
# recursively copy over all local certificate files (and ignore all other files)
RUN find /tmp/tmp_certs -type f \( -iname \*.cer -o -iname \*.crt -o -iname \*.pem \) -execdir cp {} /usr/local/share/ca-certificates/${img_cert_folder}/ \;
# update all cert file extensions to .crt
RUN (cd /usr/local/share/ca-certificates/${img_cert_folder} ; for f in *.cer; do mv -- "$f" "${f%.cer}.crt" 2>/dev/null || true ; done ; for f in *.pem; do mv -- "$f" "${f%.pem}.crt" 2>/dev/null || true ; done)
RUN rm -rf /tmp/tmp_certs

RUN update-ca-certificates && \
    echo export SSL_CERT_DIR=/etc/ssl/certs >> /etc/bash.bashrc && \
    echo export CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt >> /etc/bash.bashrc

# set specific primary cert env var
RUN echo export HTTPLIB2_CA_CERT=/usr/local/share/ca-certificates/${img_cert_folder}/${primary_cert_name}.crt >> /etc/bash.bashrc

#RUN cat /usr/local/share/ca-certificates/${img_cert_folder}/${primary_cert_name}.crt | sudo tee -a /etc/ssl/certs/ca-certificates.crt


RUN update-ca-certificates

ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

RUN apt-get update && apt-get install -y build-essential curl software-properties-common git vim

# # ############################################
# # # Python 3.12
# # ############################################
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update && apt install python3.12 python3.12-dev python3.12-distutils python3.12-venv -y && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1 

RUN python3.12 -m ensurepip --upgrade && \
    python3.12 -m pip install --upgrade pip && \
    python3.12 -m pip install --upgrade setuptools && \
    python3.12 -m pip install certifi

# # # ############################################
# # # # Poetry - update to use latest version 
# # # ############################################
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python3 -
RUN rm -f /usr/local/bin/poetry
RUN ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

RUN poetry config virtualenvs.create false

WORKDIR /opt

# Get boogie and rm the last line of the __init__.py in the ../sardara/widgets folder as it causes the program to crash when it runs looking for a custom module that doesn't exist
RUN git clone https://gitlab.com/nurbldoff/boogie.git && sed -i '$ d' /opt/boogie/boogie/plugins/sardana/widgets/__init__.py

WORKDIR /opt/boogie

RUN pip install .

WORKDIR /opt

ENV TANGO_HOST=127.0.0.1:10000
