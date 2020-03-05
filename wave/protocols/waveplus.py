import datetime
import struct

from .common import Protocol, Sample

U8_MAX = 0xF

# INDEX       DESCRIPTION                       FORMAT
# 0         : ???                               x
# 1         : humidity * 2                      b
# 2         : light level                       b
# 3         : orientation << 4 | wave count     b
# 4, 5      : short term radon                  H
# 6, 7      : long term radon                   H
# 8, 9      : temperature celsius * 100         H
# 10, 11    : pressure * 2                      H
# 12, 13    : co2                               H
# 14, 15    : voc                               H
READINGS_STRUCT = struct.Struct("<xbbbHHHHHHxxxx")


def sample_from_readings(readings: bytes) -> Sample:
    hum, light, owc, sh_rad, lo_rad, temp, pressure, co2, voc = READINGS_STRUCT.unpack(readings)
    return Sample(
        humidity=hum / 2,
        light_level=light,
        orientation=(owc >> 4) & U8_MAX,
        wave_count=owc & U8_MAX,
        short_term_radon=sh_rad,
        long_term_radon=lo_rad,
        temperature=temp / 100,
        pressure=pressure / 2,
        co2=co2,
        voc=voc,
        collected_at=datetime.datetime.now(),
    )


class WavePlusProtocol(Protocol):
    def read(self) -> Sample:
        readings = self._peripheral.readCharacteristic(0xD)
        return sample_from_readings(readings)
