#
# Dockerfile
#
# This file will be used on non balenaCloud/openBalena environments, like local
# balenaEngine/Docker builds or Docker Hub.
#
# Available base images:
#   https://www.balena.io/docs/reference/base-images/base-images/
#
# Copyright (c) 2018 René-Marc Simard
# SPDX-License-Identifier: Apache-2.0
#

# Declare pre-build variables
ARG DEVICE_NAME=raspberrypi3

# Define base image
FROM balenalib/${DEVICE_NAME}-alpine-python:3

# Declare build variables
ARG VERSION=0.2.4

# Setup application directory
WORKDIR /usr/src/app

# Install requirements
RUN apk add \
     bluez \
     g++ \
     glib-dev \
     linux-headers \
     make \
     py-setuptools

RUN pip install --no-cache-dir \
     bluepy \
     paho-mqtt \
     pyyaml

RUN wget www.airthings.com/tech/find_wave.py

RUN find /usr/local \
     \( -type d -a -name test -o -name tests \) \
     -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
     -exec rm -rf '{}' +

RUN apk del \
     g++ \
     glib-dev \
     linux-headers \
     make \
     py-setuptools

COPY ["airthingswave-mqtt/", "airthingswave-mqtt"]

# Copy project files in their proper locations
ARG CRON_PERIOD=hourly
COPY ["docker/crontask.sh", "/etc/periodic/${CRON_PERIOD}/airthingswave-mqtt"]
COPY ["docker/docker-entrypoint.sh", "/usr/local/bin/"]
COPY ["docker/config.yaml", "docker/start.sh", "README.md", "./"]

RUN chmod +x \
     "/etc/periodic/${CRON_PERIOD}/airthingswave-mqtt" \
     "/usr/local/bin/docker-entrypoint.sh" \
     "start.sh"

ENTRYPOINT ["docker-entrypoint.sh"]

# Start the main loop
#CMD ["crond", "-f", "-d", "8"]
CMD ["/usr/src/app/start.sh"]
