# Airthings Wave MQTT

> This fork no longer shares its core functionality or code with the upstream repository.
> The project isn't associated with balena.


Supports the following devices:

- Wave first generation (2900)
- Wave Plus (2930)

The program automatically searches for new devices every 24 hours.
It then publishes the readings of each device it knows about every 30 minutes.
The topic is `wave/{SERIAL NUMBER}/sample`.
If there's an error with one of the devices it will publish an error to `wave/{SERIAL NUMBER}/error`.
Please see [Error Payloads](#error-payloads) for a list of errors.


## Running

### With Docker

The image tag is `siku2/balena-airthingswave`.
To access the Bluetooth stack the container needs certain privileges such as `NET_ADMIN` capability and access to the host network. 

The following command gets you up and running.
Please note that you need to replace `<MQTT BROKER>` with the hostname of your MQTT broken.
```shell script
docker run --env MQTT_HOST=<MQTT BROKER> --cap-add NET_ADMIN --net host siku2/balena-airthingswave 
```

You can pass command line arguments as the command like so:
```shell script
docker run --cap-add NET_ADMIN --net host siku2/balena-airthingswave --host <MQTT BROKER> --verbose
```

Use the [`command`](https://docs.docker.com/compose/compose-file/#command) key if you're using docker compose.

See the [Configuration](#configuration) section for more information about the command line arguments.

### Manually

You need Python 3.8!

First, install the dependencies:
```shell script
pip install bluepy paho-mqtt
```

Make sure that you're in the "balena-airthingswave" directory.
By default it tries to connect to `localhost:1883`. This is most likely not the right address.
Use the `--host` argument to specify which host to connect to:
```shell script
python -m airthingswave --host <MQTT BROKER>
```

See the [Configuration](#configuration) section for more information about the command line arguments.


## Configuration

Currently the only way to configure the program is by passing command line arguments.
Some settings can also be set using environment variables.

The following is the output of `python -m wave --help`.
```shell script
usage: airthingswave [-h] [-H HOST] [--client-id airthings-wave] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -H HOST, --host HOST  MQTT host. Env: $MQTT_HOST
  --client-id airthings-wave
                        Client ID to use for MQTT. Env: $MQTT_CLIENT_ID
  -v, --verbose         increase output verbosity
```
Settings with support for environment variables are labeled like this: "Env: $VARIABLE".


## Error Payloads

### connection-failed

This error is published if the program couldn't connect to a device.

## Commands

Commands may be sent to the topic `wave/command`.

### Discover

```json
{
  "method": "discover"
}
```

### Update

```json
{
  "method": "update"
}
```