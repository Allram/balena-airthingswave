import argparse
import logging
import os
import sys
from typing import Any
from urllib import parse as urlparse

from . import mqtt_helper
from .app import App


def url_arg(s: str) -> urlparse.SplitResult:
    return urlparse.urlsplit(s)


def env(key: str, default: Any = None) -> Any:
    return os.getenv(key, default)


def get_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wave")
    parser.add_argument("-H", "--host", type=url_arg,
                        default=env("MQTT_HOST", "localhost"),
                        help="MQTT host. Env: $MQTT_HOST")
    parser.add_argument("--client-id", default=env("MQTT_CLIENT_ID", "airthings-wave"),
                        help="Client ID to use for MQTT. Env: $MQTT_CLIENT_ID",
                        metavar="airthings-wave")

    parser.add_argument("-v", "--verbose", action="store_true", help="increase output verbosity")
    return parser


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("{levelname:5} [{name}]: {message}", style="{"))

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)


def main():
    parser = get_argument_parser()
    args = parser.parse_args()

    setup_logging(args.verbose)

    mqtt_url: urlparse.SplitResult = args.host
    client = mqtt_helper.connect(mqtt_url.hostname or mqtt_url.path, mqtt_url.port, client_id=args.client_id)

    try:
        App(client).run()
    except KeyboardInterrupt:
        logging.info("stopping")
    finally:
        mqtt_helper.stop_client(client)


if __name__ == "__main__":
    main()
