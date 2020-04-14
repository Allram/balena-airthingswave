FROM python:3.8-alpine

# install runtime dependencies
RUN apk --update add --no-cache \
    glib-dev

# dependencies required to build bluepy-helper
RUN apk --update add --virtual build-dependencies --no-cache \
    gcc \
    libc-dev \
    libcap \
    make

RUN pip install \
    bluepy \
    paho-mqtt

RUN bluepy_path=$(find /usr/local/lib -name bluepy-helper) && \
    setcap 'cap_net_raw,cap_net_admin+eip' $bluepy_path && \
    chmod +x $bluepy_path

RUN apk del build-dependencies

WORKDIR /airthingswave
COPY airthingswave airthingswave

ENTRYPOINT ["python", "-m", "airthingswave"]
