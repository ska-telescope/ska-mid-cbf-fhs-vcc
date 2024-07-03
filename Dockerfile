ARG BUILD_IMAGE="artefact.skao.int/ska-tango-images-pytango-builder:9.4.3"
ARG BASE_IMAGE="artefact.skao.int/ska-tango-images-pytango-runtime:9.4.3"


FROM $BUILD_IMAGE AS buildenv

FROM $BASE_IMAGE

USER root

ENV local_cert_path="/certs"
ENV img_cert_folder="own-certificates"
ENV primary_cert_name="MDA-cert-bundle"

#copy over pip file to allow python extension downloads
COPY /pip.conf /etc/pip.conf

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

RUN apt-get update && apt-get install -y build-essential

# # # ############################################
# # # # Poetry - update to use latest version 
# # # ############################################
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python3 -
RUN rm -f /usr/local/bin/poetry
RUN ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

RUN poetry config virtualenvs.create false


# Copy poetry.lock* in case it doesn't exist in the repo
COPY pyproject.toml poetry.lock* ./

# Install runtime dependencies and the app
RUN poetry install


USER tango 