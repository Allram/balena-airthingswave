import dataclasses
import enum
import logging
from typing import Callable, Tuple

from bluepy.btle import Peripheral

from . import events
from .protocols import Protocol, WavePlusProtocol, WaveProtocol

logger = logging.getLogger(__name__)


class Model(enum.Enum):
    WAVE = "2900"
    WAVE_MINI = "2920"
    WAVE_PLUS = "2930"
    WAVE_SECOND_GEN = "2950"

    @property
    def model_name(self) -> str:
        return _MODEL_NAME_MAP[self]

    @property
    def protocol_factory(self) -> Callable[[Peripheral], Protocol]:
        return _MODEL_PROTO_FACTORY_MAP[self]

    @classmethod
    def from_serial_number(cls, sn: str):
        return cls(sn[:4])


_MODEL_PROTO_FACTORY_MAP = {
    Model.WAVE: WaveProtocol,
    Model.WAVE_PLUS: WavePlusProtocol,
}

_MODEL_NAME_MAP = {
    Model.WAVE: "Wave",
    Model.WAVE_MINI: "Wave Mini",
    Model.WAVE_PLUS: "Wave Plus",
    Model.WAVE_SECOND_GEN: "Wave 2nd gen",
}


@dataclasses.dataclass()
class Wave:
    model: Model
    serial_number: str
    mac_addr: str

    def __str__(self) -> str:
        return f"<{self.model.model_name} {self.serial_number}>"

    def _id_tuple(self) -> Tuple[str, str]:
        return self.serial_number, self.mac_addr

    def __hash__(self) -> int:
        return hash(self._id_tuple())

    def __eq__(self, other: "Wave") -> bool:
        return self._id_tuple() == other._id_tuple()

    def connect_peripheral(self, timeout: float = 5) -> Peripheral:
        logger.debug("connecting to %s", self)
        p = Peripheral()
        with events.timeout_interrupt(timeout):
            p.connect(self.mac_addr)

        return p

    def connect(self) -> Protocol:
        peripheral = self.connect_peripheral()
        return self.model.protocol_factory(peripheral)
