import contextlib
import json
import logging
import threading
from typing import Any, ContextManager, Iterable, Tuple

from paho.mqtt.client import Client as MQTTClient, MQTTMessage

__all__ = ["MQTTClient", "MQTTMessage", "connect_client", "connect", "stop_client", "publish_json_message"]

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def _restore_attr(o: object, k: Any, v: Any):
    prev = getattr(o, k)
    setattr(o, k, v)
    try:
        yield
    finally:
        setattr(o, k, prev)


@contextlib.contextmanager
def _restore_attrs(o: object, *attrs: Tuple[Any, Any]):
    cm_gen: Iterable[ContextManager] = (_restore_attr(o, k, v) for k, v in attrs)

    with contextlib.ExitStack() as stack:
        for cm in cm_gen:
            stack.enter_context(cm)

        yield


def connect_client(client: MQTTClient, host: str, port: int = None, timeout: float = None, **kwargs) -> None:
    connected_event = threading.Event()

    def trigger_event(*_):
        connected_event.set()

    with _restore_attrs(client, ("on_connect", trigger_event), ("on_disconnect", trigger_event)):
        logger.info("connecting to host %r", host)
        client.connect(host, port or 1883, **kwargs)
        triggered = connected_event.wait(timeout)

    if not triggered:
        client.disconnect()
        raise TimeoutError("connecting timed out")

    if not client.is_connected():
        raise ConnectionError("failed to connect")


def connect(host: str, port: int = None, *, client_id: str = None, timeout: float = None, **kwargs) -> MQTTClient:
    client = MQTTClient(client_id or "")
    client.loop_start()
    try:
        connect_client(client, host, port, timeout=timeout, **kwargs)
    except BaseException:
        client.loop_stop(force=True)
        raise

    return client


def stop_client(client: MQTTClient) -> None:
    logger.debug("stopping client %s", client)
    client.disconnect()
    client.loop_stop()


def publish_json_message(client: MQTTClient, topic: str, payload: Any, **kwargs) -> MQTTMessage:
    msg = client.publish(topic, json.dumps(payload), **kwargs)
    msg.wait_for_publish()
    return msg
