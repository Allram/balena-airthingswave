# Airthings Wave MQTT

> This fork no longer shares its core functionality or code with the upstream repository.
> The project isn't associated with balena.


Supports the following devices:

- Wave first generation (2900)
- Wave Plus (2930)

## About this fork

This fork provides ~~automated~~<sup>1</sup> docker image builds.
You can find it at [siku2/balena-airthingswave](https://hub.docker.com/repository/docker/siku2/balena-airthingswave).

The default `DEVICE_NAME` is now "raspberrypi3".
The image with tag "latest" is built for Raspberry Pi 3 and 4.

> I have no idea how this affects Pi Zero, but you'll probably have to build it yourself.


## Home Assistant

If you're using Home Assistant, check out [siku2/hass-mqtt-airthingswave](https://github.com/siku2/hass-mqtt-airthingswave).
It's an integration for this.


## Other changes

- Upgraded to Python 3!
- Support for Wave Plus. See the [config file](docker/config.yaml) for how to specify the device type.
- Added a tool for creating home assistant MQTT sensor configurations. See [format_sensors.py](tools/format_sensors.py)

[1]: I tried using Docker Hub builds and GitHub Actions but neither supports building for arm architectures.
I think Travis CI supports it, if you're interested.

