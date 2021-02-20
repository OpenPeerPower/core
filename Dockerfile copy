ARG BUILD_FROM
FROM ${BUILD_FROM}

# Synchronize with openpeerpower/core.py:async_stop
ENV \
    S6_SERVICES_GRACETIME=220000

WORKDIR /usr/src

## Setup Open Peer Power
COPY . openpeerpower/
RUN \
    pip3 install --no-cache-dir --no-index --only-binary=:all: --find-links "${WHEELS_LINKS}" \
    -r openpeerpower/requirements_all.txt \
    && pip3 install --no-cache-dir --no-index --only-binary=:all: --find-links "${WHEELS_LINKS}" \
    -e ./openpeerpower \
    && python3 -m compileall openpeerpower/openpeerpower

# Open Peer Power S6-Overlay
COPY rootfs /

WORKDIR /config
