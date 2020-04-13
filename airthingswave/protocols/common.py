import abc
import dataclasses
from types import TracebackType
from typing import ContextManager, Optional, Type, TypeVar, Iterator, Tuple, Any, Dict, MutableMapping, Callable
import datetime
from bluepy.btle import Peripheral

__all__ = ["Sample", "Protocol"]

KT = TypeVar("KT")
VT = TypeVar("VT")


def _dict_map_item(d: MutableMapping[KT, VT], key: KT, transformer: Callable[[VT], Any]) -> None:
    try:
        value = d[key]
    except KeyError:
        pass
    else:
        d[key] = transformer(value)


@dataclasses.dataclass()
class Sample:
    humidity: Optional[float] = None
    light_level: Optional[int] = None
    orientation: Optional[int] = None
    wave_count: Optional[int] = None
    short_term_radon: Optional[int] = None
    long_term_radon: Optional[int] = None
    temperature: Optional[float] = None
    pressure: Optional[float] = None
    co2: Optional[int] = None
    voc: Optional[int] = None
    collected_at: Optional[datetime.datetime] = None

    def __str__(self) -> str:
        fields = ", ".join(f"{k} = {v}" for k, v in self.iter_existing_items())
        return f"Sample({fields})"

    def iter_existing_items(self) -> Iterator[Tuple[str, Any]]:
        for k, v in self.__dict__.items():
            if v is not None:
                # no need to clone because all values are primitives
                yield k, v

    def as_dict(self) -> Dict[str, Any]:
        return dict(self.iter_existing_items())

    def as_json_object(self) -> Dict[str, Any]:
        data = self.as_dict()
        _dict_map_item(data, "collected_at", lambda dt: dt.isoformat())
        return data


T = TypeVar("T")


class Protocol(ContextManager, abc.ABC):
    __slots__ = ("_peripheral",)

    def __init__(self, peripheral: Peripheral) -> None:
        self._peripheral = peripheral

    def __enter__(self: T) -> T:
        return self

    def __exit__(self,
                 exc_type: Optional[Type[BaseException]],
                 exc_val: Optional[BaseException],
                 exc_tb: Optional[TracebackType]) -> None:
        self.disconnect()

    def disconnect(self) -> None:
        self._peripheral.disconnect()

    @abc.abstractmethod
    def read(self) -> Sample:
        ...
