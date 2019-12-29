"""
Tool for easily creating sensor configurations for wave devices.

Usage:

    format_sensors.py [device name]...

Use a "+" at the end of the device name to indicate that it is a wave+ device.
This will output the additional sensors only supported by wave plus.
"""

import dataclasses
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
    SensorInfo("voc", "ppm", ICON_CLOUD),
)


SENSOR_TEMPLATE = """
- platform: mqtt
  state_topic: "{device}/{topic}"
  name: "{device}/{topic}"
""".strip()

SENSOR_VALID_KEYS = {"unit_of_measurement", "icon", "device_class"}


def format_sensor(device: str, info: SensorInfo) -> str:
    s = SENSOR_TEMPLATE.format(device=device, topic=info.topic)

    info_dict = dataclasses.asdict(info)
    for name, value in info_dict.items():
        if name not in SENSOR_VALID_KEYS:
            continue

        if value:
            s += f"\n  {name}: \"{value}\""

    return s


def format_sensors(device: str, plus: bool) -> str:
    attrs = ATTRIBUTES_PLUS if plus else ATTRIBUTES
    return "\n".join(map(lambda i: format_sensor(device, i), attrs))


def main() -> None:
    import sys
    devices = sys.argv[1:]

    sensors = []

    for device in devices:
        plus = False
        if device.endswith("+"):
            device = device[:-1]
            plus = True

        sensors.append(format_sensors(device, plus))

    print("\n\n".join(sensors))


if __name__ == "__main__":
    main()
