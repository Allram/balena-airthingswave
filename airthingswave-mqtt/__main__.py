import sys
import traceback

from . import airthingswave


def usage():
    print(f"Usage: {sys.argv[0]} <config file>")


def main():
    if len(sys.argv) < 2:
        usage()
        return False

    c = sys.argv[1]
    print("Config file: {0}".format(c))

    atw = airthingswave.AirthingsWave_mqtt(c)

    try:
        atw.publish_readings()
    finally:
        atw.mqtt_disconnect()


main()
