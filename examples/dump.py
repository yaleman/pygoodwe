"""dumps the raw JSON response from the API"""

import json

from config import args
from pygoodwe import API


def main() -> None:
    """dumps the raw data"""
    goodwe: API = API(
        system_id=args.get("gw_station_id", "1"),
        account=args.get("gw_account", "thiswillnotwork"),
        password=args.get("gw_password", "thiswillnotwork"),
    )
    goodwe.getCurrentReadings()
    print(json.dumps(goodwe.data, indent=4))


if __name__ == "__main__":
    main()
