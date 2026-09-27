FROM artefact.skao.int/ska-build-python:1.0.0 AS builder
WORKDIR /app

# Install the application dependencies with uv, then the application itself with
# pip to ensure device server scripts are generated properly.
# Since pipeline infrastructure is set up to use the application image for the
# k8s-test runner pod, we also install pip in .venv and export test dependencies
# to be used at test runtime.
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --no-default-groups --no-install-project && \
    uv pip install . && \
    uv pip install pip

# Using ska-base-images for its Python 3.14 runtime instead of ska-tango-images
# means we have to perform the runtime dependencies installation ourselves.
FROM artefact.skao.int/ska-tango-images-tango-admin:1.28.1 AS tools
FROM artefact.skao.int/ska-python-py314:1.0.0 AS runtime
COPY --from=tools /usr/local/ /usr/local/
COPY --from=tools /runtime_deps.txt /runtime_deps.txt
RUN set -xe; \
    apt-get update && \
    apt-get install -y --no-install-recommends sudo; \
    xargs apt-get install -y --no-install-recommends < /runtime_deps.txt; \
    rm -rf /var/lib/apt/lists/*

# Copy in application data as well as the list of test dependencies.
COPY pyproject.toml /app/pyproject.toml
COPY --from=builder /app/.venv /app/.venv

# Create default tango user.
RUN groupadd -g 10001 tango && \
    useradd -u 10001 -g tango -ms /bin/bash tango && \
    usermod -aG sudo tango && \
    echo "tango ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    chown -R tango:tango /app

USER tango
ENV PATH="/app/.venv/bin:${PATH}"
WORKDIR /app
