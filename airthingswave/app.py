import datetime
import json
import logging
import threading
import time
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, TypeVar, Union

from . import events, mqtt_helper
from .device import Wave
from .discovery import WaveFinder
from .protocols import Sample

logger = logging.getLogger(__name__)

T = TypeVar("T")

S_MIN = 60
S_HOUR = 60 * S_MIN


class Task:
    __slots__ = ("name", "run_interval", "func",
                 "__run_lock", "__next_run_at")
    name: str
    run_interval: float
    func: Callable[[], None]
    __next_run_at: Optional[float]

    def __init__(self, func: Callable[[], None], interval: float, *, name: str = None) -> None:
        if name is None:
            name = func.__qualname__
        self.name = name
        self.run_interval = interval
        self.func = func

        self.__run_lock = threading.Lock()
        self.__next_run_at = None

    def __repr__(self) -> str:
        return f"{type(self).__qualname__}({self.func!r}, {self.run_interval!r}, name={self.name!r})"

    def __str__(self) -> str:
        td = datetime.timedelta(seconds=self.run_interval)
        return f"<{self.name} [{td}]>"

    @property
    def running(self) -> bool:
        return self.__run_lock.locked()

    def __run(self) -> None:
        should_log = logger.isEnabledFor(logging.INFO)

        if should_log:
            start_time = time.time()

        logger.info("running %s", self)
        try:
            self.func()
        except Exception:
            logger.exception("error while running %s", self)

        if should_log:
            td = datetime.timedelta(seconds=time.time() - start_time)
            logger.info("%s finished, took %s", self, td)

        self.__schedule_next_run(time.time())

    def run(self) -> None:
        with self.__run_lock:
            self.__run()

    def __schedule_next_run(self, t: float) -> None:
        self.__next_run_at = t + self.run_interval

    def __is_past_next_run(self, t: Optional[float]) -> bool:
        if self.__next_run_at is None:
            return True

        if t is None:
            t = time.time()

        return t >= self.__next_run_at

    def run_if_not_running(self) -> None:
        if not self.running:
            self.run()

    def maybe_run(self, now: float = None) -> None:
        if self.__is_past_next_run(now):
            self.run_if_not_running()

    def get_next_run(self, now: float = None) -> float:
        if now is None:
            now = time.time()

        if self.__is_past_next_run(now):
            self.__schedule_next_run(now)

        return self.__next_run_at


IntOrStr = Union[str, int]


class App:
    _devices: List[Wave]

    def __init__(self, mqtt_client: mqtt_helper.MQTTClient) -> None:
        if not mqtt_client.is_connected():
            raise ValueError("mqtt client must be connected")

        self._mqtt_client = mqtt_client
        self.__mqtt_prefix = "wave/"

        self.__update_loop_running = False

        self._read_task = Task(self.__read, 30 * S_MIN, name="Read Wave")
        self._discover_task = Task(self.__discover, 24 * S_HOUR, name="Discovery")

        self._devices = []

    def __publish_samples(self, samples: List[Tuple[Wave, Optional[Sample]]]) -> None:
        logger.info("publishing %s sample(s)", len(samples))
        mqtt = self._mqtt_client
        prefix = f"{self.__mqtt_prefix}device/"

        expires_at = datetime.datetime.fromtimestamp(self._read_task.get_next_run(), tz=datetime.timezone.utc)
        expires_at_str = expires_at.isoformat()

        for client, sample in samples:
            client_prefix = f"{prefix}{client.serial_number}/"

            if sample is not None:
                data = sample.as_json_object()
                data["model_name"] = client.model.model_name
                data["expires_at"] = expires_at_str

                mqtt_helper.publish_json_message(
                    mqtt,
                    f"{client_prefix}sample",
                    data,
                    qos=1, retain=True
                )
            else:
                # TODO maybe use a global error topic and include the device id.
                mqtt_helper.publish_json_message(
                    mqtt,
                    f"{client_prefix}error",
                    error_payload("connection-failed", "Failed to connect to wave device")
                )

    def __read(self, *, devices: Iterable[Wave] = None) -> None:
        if devices is None:
            devices = self._devices
            if not devices:
                logger.warning("no devices to read")
                self.__wait_until_discover()

        samples = []
        for device in devices:
            sample = None
            try:
                with events.timeout_interrupt(60):
                    sample = _read_device_sample(device)
            except TimeoutError:
                logger.error("timed-out while reading device %s", device)
            except Exception:
                logger.exception("failed to read device %s", device)

            samples.append((device, sample))

        self.__publish_samples(samples)

    def __log_discovery(self, devices: Set[Wave]) -> None:
        if logger.isEnabledFor(logging.WARNING):
            prev_devices = set(self._devices)

            if logger.isEnabledFor(logging.INFO):
                added = devices - prev_devices
                logger.info("%s new device(s):\n  %s", len(added), ", ".join(map(str, added)))

            removed = prev_devices - devices
            if removed:
                logger.warning("%s removed device(s):\n  %s", len(removed), ", ".join(map(str, removed)))

    def __discover(self) -> None:
        finder = WaveFinder()
        devices = set(finder.scan())
        if devices:
            logger.debug("found %s devices", len(devices))
            self.__log_discovery(devices)
        else:
            logger.warning("no devices found")

        self._devices = list(devices)

    def __wait_until_discover(self) -> None:
        logger.info("waiting until devices discovered")
        max_fail_streak = 3
        fail_streak = 0
        while True:
            try:
                self.__discover()
            except Exception:
                fail_streak += 1
                if fail_streak >= max_fail_streak:
                    logger.warning(f"failed {fail_streak} time(s) in a row, aborting")
                    raise

                logger.exception(f"discovery failed {fail_streak} time(s) in a row (max {max_fail_streak})")
            else:
                fail_streak = 0

            if self._devices:
                break

            logger.info("retrying in a minute")
            time.sleep(S_MIN)

    def __run_tasks(self) -> None:
        self._discover_task.maybe_run()
        self._read_task.maybe_run()

    def __update_loop(self) -> None:
        read = self._read_task
        discover = self._discover_task

        logger.info("initial task run")
        self.__run_tasks()

        while True:
            now = time.time()
            sleep_time = min(read.get_next_run(now), discover.get_next_run(now)) - now
            if logger.isEnabledFor(logging.INFO):
                td = datetime.timedelta(seconds=sleep_time)
                logger.info("sleeping for %s", td)

            time.sleep(sleep_time)
            self.__run_tasks()

    def run(self) -> None:
        assert not self.__update_loop_running
        self.__update_loop_running = True

        self.__mqtt_subscribe()

        try:
            self.__update_loop()
        finally:
            self.__update_loop_running = False

    def __mqtt_subscribe(self) -> None:
        mqtt_client = self._mqtt_client

        assert mqtt_client.on_message is None
        mqtt_client.on_message = self.__handle_message
        mqtt_client.subscribe(f"{self.__mqtt_prefix}command")

    def __handle_message(self, client: mqtt_helper.MQTTClient, userdata: Any, msg: mqtt_helper.MQTTMessage) -> None:
        if msg.topic.endswith("command"):
            self.__run_command(json.loads(msg.payload))
        else:
            logger.debug("unhandled message: %s", msg)

    def __run_command(self, cmd: Dict[str, Any]) -> None:
        logger.debug("executing command %s", cmd)
        method = cmd["method"]

        try:
            handler = getattr(self, f"_cmd_{method}")
        except AttributeError:
            logger.warning("unknown command method: %r", method)
            return

        try:
            handler(cmd)
        except Exception:
            logger.exception("command caused error: %r", cmd)

    def _cmd_discover(self, cmd: Dict[str, Any]) -> None:
        self._discover_task.run_if_not_running()

    def _cmd_update(self, cmd: Dict[str, Any]) -> None:
        if self._read_task.running:
            return

        # using .get instead of try-except because the value might be null
        device_ids: Union[IntOrStr, List[IntOrStr], None] = cmd.get("devices")
        if device_ids is None:
            self._read_task.run_if_not_running()
            return

        if isinstance(device_ids, (str, int)):
            serial_numbers = {device_ids}
        else:
            serial_numbers = set(map(str, device_ids))

        self.__read(devices=(dev for dev in self._devices if dev.serial_number in serial_numbers))


def _read_device_sample(device: Wave) -> Sample:
    with device.connect() as proto:
        return proto.read()


def error_payload(error_type: str, message: str = None) -> Dict[str, Any]:
    return {
        "error": error_type,
        "message": message,
    }
