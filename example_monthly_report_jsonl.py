"""Dump the last six months of power reports as JSONL."""

import json
import sys
from datetime import date, timedelta

try:
    from config import args
except ImportError:
    print("Create a config.py with args dict containing gw_station_id, gw_account, gw_password", file=sys.stderr)
    sys.exit(1)

from pygoodwe import SingleInverter

def main() -> None:
    station_id = args["gw_station_id"]
    account = args["gw_account"]
    password = args["gw_password"]

    inv = SingleInverter(station_id, account, password, skipload=True)
    if not inv.do_login():
        print("Login failed", file=sys.stderr)
        sys.exit(1)

    today = date.today()
    for i in range(6, 0, -1):
        day = today - timedelta(days=i * 30)
        month_str = day.strftime("%Y-%m")
        result = inv.getPowerStationPowerReportByMonth(day)
        if result is None:
            print(f"No data for {month_str}", file=sys.stderr)
            continue
        print(json.dumps({"month": month_str, "data": result}, default=str))

if __name__ == "__main__":
    main()
