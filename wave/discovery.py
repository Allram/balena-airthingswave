import logging
import struct
import threading
import time
from typing import List

from bluepy.btle import DefaultDelegate, ScanEntry, Scanner

from .device import Model, Wave

__all__ = ["WaveFinder"]

logger = logging.getLogger(__name__)

AIRTHINGS_MANUFACTURER_MAGIC = 0x0334

_MANU_DATA_STRUCT = struct.Struct("<HL")


def parse_serial_number(manufacturer: bytes) -> str:
    try:
        magic, sn = _MANU_DATA_STRUCT.unpack(manufacturer[:6])
    except struct.error as e:
        raise ValueError from e

    if magic != AIRTHINGS_MANUFACTURER_MAGIC:
        raise ValueError("not an Airthings device")

    return str(sn)


class WaveFinder(DefaultDelegate):
    _devices: List[Wave]

    def __init__(self) -> None:
        super().__init__()
        self._scanner = Scanner().withDelegate(self)
        self._lock = threading.Lock()

        self._devices = []
        self._max_timeout = 5
        self._poll_interval = 1
        self.__timeout_at = None

    def handleDiscovery(self, scan_entry: ScanEntry, is_new_dev: bool, is_new_data: bool):
        if not (is_new_dev and scan_entry.connectable):
            return

        manufacturer = scan_entry.getValue(ScanEntry.MANUFACTURER)
        if manufacturer is None:
            return

        try:
            sn = parse_serial_number(manufacturer)
        except ValueError:
            return

        try:
            model = Model.from_serial_number(sn)
        except ValueError as e:
            logger.warning("encountered unknown Airthings devices", exc_info=e)
            return

        device = Wave(model, sn, scan_entry.addr)
        logger.debug("discovered device: %s at %s", device, device.mac_addr)
        self._devices.append(device)
        self.__timeout_at = time.time() + self._max_timeout

    def _clear(self) -> None:
        self.__timeout_at = None
        self._devices.clear()

    def __scan_until_timeout(self) -> None:
        logger.info("starting scan")
        self._scanner.start()
        self._last_discovery = None
        self.__timeout_at = time.time() + self._max_timeout

        try:
            while self.__timeout_at > time.time():
                self._scanner.process(self._poll_interval)
        finally:
            self._scanner.stop()

        logger.info("scan finished, found %s devices", len(self._devices))

    def scan(self) -> List[Wave]:
        with self._lock:
            self._clear()
            self.__scan_until_timeout()

        return self._devices
