#!/usr/bin/env python3
"""Read the current values from one SEMS+ station."""

from config import args
from pygoodwe import SingleInverter


def main() -> None:
    inverter = SingleInverter(
        system_id=args["gw_station_id"],
        account=args["gw_account"],
        password=args["gw_password"],
    )
    print(f"PV power: {inverter.getPVFlow()} W")
    print(f"Load power: {inverter.getLoadFlow()} W")
    if inverter.data.get("soc"):
        print(f"Battery charge: {inverter.get_battery_soc()}%")


if __name__ == "__main__":
    main()
