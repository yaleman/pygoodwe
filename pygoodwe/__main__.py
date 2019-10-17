#!/usr/bin/env python3

import sys
import logging
import argparse
import locale
import time
import pygoodwe
from datetime import datetime
from astral import Astral

__version__ = "0.0.1"
__author__ = "James Hodgkinson"
__copyright__ = "Copyright 2019-, James Hodgkinson"
__license__ = "MIT"
__email__ = "james@terminaloutcomes.com"

last_eday_kwh = 0


def run():
    raise NotImplementedError("Please do not use this yet")
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Query GOODWE station data")
    parser.add_argument(
        "--gw-station-id", help="GOODWE station ID", metavar="ID", required=True
    )
    parser.add_argument(
        "--gw-account", help="GOODWE account", metavar="ACCOUNT", required=True
    )
    parser.add_argument(
        "--gw-password", help="GOODWE password", metavar="PASSWORD", required=True
    )
    parser.add_argument(
        "--log",
        help="Set log level (default info)",
        choices=["debug", "info", "warning", "critical"],
        default="info",
    )
    parser.add_argument(
        "--date", help="Copy all readings (max 14/90 days ago)", metavar="YYYY-MM-DD"
    )
    parser.add_argument(
        "--pv-voltage",
        help="Send pv voltage instead of grid voltage",
        action="store_true",
    )
    parser.add_argument(
        "--skip-offline",
        help="Skip uploads when inverter is offline",
        action="store_true",
    )
    parser.add_argument("--city", help="Skip uploads from dusk till dawn")
    parser.add_argument(
        "--csv",
        help="Append readings to a Excel compatible CSV file, DATE in the name will be replaced by the current date",
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s " + __version__
    )
    args = parser.parse_args()

    # Configure the logging
    loglevel = getattr(logging, args.log.upper(), None)
    if not isinstance(loglevel, int):
        raise ValueError("Invalid log level: %s" % loglevel)
    logging.basicConfig(format="%(levelname)-8s %(message)s", level=loglevel)

    # Check if we're running the supported Python version
    if sys.version_info[0] != 3:
        logging.error("Please use Python 3 to run this script")
        sys.exit()

    startTime = datetime.now()

    # TODO: make all this work...
    while True:
        try:
            pygoodwe.run_once(args)
        except Exception as exp:
            logging.error(exp)
            time.sleep(30)

        if args.pvo_interval is None:
            break

        interval = args.pvo_interval * 60
        time.sleep(interval - (datetime.now() - startTime).seconds % interval)


if __name__ == "__main__":
    run()
