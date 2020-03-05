import datetime

from .common import Protocol, Sample


class WaveProtocol(Protocol):
    def __read_char(self, handle: int, signed: bool) -> int:
        d = self._peripheral.readCharacteristic(handle)
        return int.from_bytes(d, "little", signed=signed)

    def read(self) -> Sample:
        return Sample(
            humidity=self.__read_char(0x26, False) / 100,  # 2A6F
            short_term_radon=self.__read_char(0x16, False),  # b42e01aa-ade7-11e4-89d3-123b93f75cba
            long_term_radon=self.__read_char(0x1E, False),  # b42e0a4c-ade7-11e4-89d3-123b93f75cba
            temperature=self.__read_char(0x22, True) / 100,  # 2A6E
            collected_at=datetime.datetime.now(),
        )
