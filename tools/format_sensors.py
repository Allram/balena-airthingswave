"""
Tool for easily creating sensor configurations for wave devices.
Outputs the YAML configuration for the devices to the console.

This is only really useful if you have multiple wave devices and you can't be bothered to write all the configuration manually.

Usage:

    python format_sensors.py [device name]...

Use a "+" at the end of the device name to indicate that it is a wave+ device.
This will output the additional sensors only supported by wave plus.

This requires at least python 3.7.
"""

import dataclasses
import re
from argparse import ArgumentParser, ArgumentTypeError
from typing import Any, Dict, List, Optional

DEVICE_CLASS_BATTERY = "battery"
DEVICE_CLASS_HUMIDITY = "humidity"
DEVICE_CLASS_ILLUMINANCE = "illuminance"
DEVICE_CLASS_SIGNAL_STRENGTH = "signal_strength"
DEVICE_CLASS_TEMPERATURE = "temperature"
DEVICE_CLASS_TIMESTAMP = "timestamp"
DEVICE_CLASS_PRESSURE = "pressure"
DEVICE_CLASS_POWER = "power"

TEMP_CELSIUS = "°C"

ICON_CLOUD = "mdi:cloud"


@dataclasses.dataclass()
class SensorInfo:
    topic: str
    unit_of_measurement: Optional[str] = None
    icon: Optional[str] = None
    device_class: Optional[str] = None


ATTRIBUTES = (
    SensorInfo("humidity", "%", device_class=DEVICE_CLASS_HUMIDITY),
    SensorInfo("radon_short", "Bq/m3", ICON_CLOUD),
    SensorInfo("radon_long", "Bq/m3", ICON_CLOUD),
    SensorInfo("temperature", TEMP_CELSIUS,
               device_class=DEVICE_CLASS_TEMPERATURE),
)

ATTRIBUTES_PLUS = ATTRIBUTES + (
    SensorInfo("light", "lm", device_class=DEVICE_CLASS_ILLUMINANCE),
    SensorInfo("pressure", "mbar", "mdi:gauge", DEVICE_CLASS_PRESSURE),
    SensorInfo("co2", "ppm", ICON_CLOUD),
    SensorInfo("voc", "ppb", ICON_CLOUD),
)


SENSOR_TEMPLATE = """
- platform: mqtt
  state_topic: "{device}/{topic}"
  name: "{device}/{topic}"
""".strip()

SENSOR_VALID_KEYS = {"unit_of_measurement", "icon", "device_class"}


@dataclasses.dataclass()
class SensorOptions:
    expire_after: Optional[int] = None
    force_update: bool = True


def format_sensor(device: str, info: SensorInfo, options: SensorOptions) -> str:
    s = SENSOR_TEMPLATE.format(device=device, topic=info.topic)

    info_dict = dataclasses.asdict(info)
    for name, value in info_dict.items():
        if name not in SENSOR_VALID_KEYS:
            continue

        if value:
            s += f"\n  {name}: \"{value}\""

    if options.force_update:
        s += f"\n  force_update: true"

    if options.expire_after:
        s += f"\n  expire_after: {options.expire_after}"

    return s


def format_sensors(device: str, plus: bool, options: SensorOptions) -> str:
    attrs = ATTRIBUTES_PLUS if plus else ATTRIBUTES
    return "\n".join(map(lambda i: format_sensor(device, i, options), attrs))


TIME_PATTERN = re.compile(
    r"^((?P<h>\d+?)hr?)?((?P<m>\d+?)m)?((?P<s>\d+?)s?)?$")


def _parse_time(s: str) -> int:
    match = TIME_PATTERN.match(s)
    if not match:
        raise ArgumentTypeError(f"invalid time format: {s!r}")

    def get(key: str, fac: int) -> int:
        v = match[key]
        if v is None:
            return 0

        return int(v) * fac

    return get("h", 60 * 60) + get("m", 60) + get("s", 1)


def get_arg_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="A tool for creating the home-assistant sensor configuration."
    )

    parser.add_argument(
        "devices", metavar="device", nargs="*",
        help="Device ID. Add + to the end of the id to indicate that the device is a wave plus. (ex: \"bedroom+\")"
    )

    parser.add_argument(
        "--no-force-update", action="store_true", default=False,
        help="Disable the force_update setting."
    )

    parser.add_argument(
        "--expire", type=_parse_time,
        help="Defines the number of seconds after which the value expires if it's not updated."
    )

    parser.add_argument(
        "--clipboard", action="store_true", default=False,
        help="Write the result to the clipboard."
    )

    return parser


def write_clipboard(content: str) -> None:
    try:
        import pyperclip
    except ImportError:
        pass
    else:
        pyperclip.copy(content)
        return

    raise ImportError(
        "clipboard functionality requires pyperclip to be installed") from None


def main() -> None:
    parser = get_arg_parser()
    args = parser.parse_args()

    options = SensorOptions(expire_after=args.expire,
                            force_update=not args.no_force_update)

    sensors = []
    for device in args.devices:
        plus = False
        if device.endswith("+"):
            device = device[:-1]
            plus = True

        sensors.append(format_sensors(device, plus, options))

    result = "\n\n".join(sensors)

    if args.clipboard:
        write_clipboard(result)

    print(result)


if __name__ == "__main__":
    main()
