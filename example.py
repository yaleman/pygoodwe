"""example script showing how you can run things"""

import json
from functools import lru_cache

# copy config.py.example to config.py and fill in your details
from config import args

from pygoodwe import SingleInverter


@lru_cache()
def get_single_inverter(args=args):  # pylint: disable=redefined-outer-name,dangerous-default-value
    """test fixture"""
    print("Single Inverter")
    goodwe = SingleInverter(
        system_id=args.get("gw_station_id", "1"),
        account=args.get("gw_account", "thiswillnotwork"),
        password=args.get("gw_password", "thiswillnotwork"),
    )
    # print("Grabbing data")
    goodwe.getCurrentReadings()
    return goodwe


def test_get_temperature():
    """tests getting the temp"""
    goodwe = get_single_inverter()
    assert goodwe.get_inverter_temperature()


# print("Multi Inverter")
# gw = API(
#         system_id=args.get('gw_station_id', '1'),
#         account=args.get('gw_account', 'thiswillnotwork'),
#         password=args.get('gw_password', 'thiswillnotwork'),
#         )
# # print("Grabbing data")
# gw.getCurrentReadings(raw=True)

# print(f"Temperature: {gw.get_inverter_temperature()}")

# battery state of charge
# print(f"Current SOC: {gw.get_battery_soc()}")

inverter = get_single_inverter()
print(f"Available fields in data: {inverter.data.keys()}")

print(json.dumps(inverter.data.get("inverter", {}).get("battery"), indent=2))
batterydata = inverter.data.get("inverter", {}).get("battery", "").split("/")
if batterydata:
    voltage = float(batterydata[0][:-1])
    print(f"Battery voltage is: {voltage}")
# print(json.dumps(gw.data))
# print(f"Are the batteries full? {gw.are_batteries_full(fullstate=90.0)}")

# print(gw.data.keys())
# print(json.dumps(gw.data['inverter']))
# print(json.dumps(gw.data))

# print(f"PV Flow: {gw.getPVFlow()}")
# print(f"Voltage: {gw.getVoltage()}")

# print("Getting XLS file - this doesn't work!")
# inverter.getDayDetailedReadingsExcel(date.today() - timedelta(days=1))
