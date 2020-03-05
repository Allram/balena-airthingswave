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

RUN apk del build-dependencies

WORKDIR /airthingswave
COPY wave/ wave

ENTRYPOINT ["python", "-m", "wave"]
