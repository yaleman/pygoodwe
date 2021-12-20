#!/usr/bin/env python3

import json
import pytest


from config import args
from pygoodwe import SingleInverter, API
from datetime import date, timedelta
from functools import lru_cache

@lru_cache()
def get_single_inverter(args=args):
    """ test fixgure """
    print("Single Inverter")
    gw = SingleInverter(
            system_id=args.get('gw_station_id', '1'),
            account=args.get('gw_account', 'thiswillnotwork'),
            password=args.get('gw_password', 'thiswillnotwork'),
            )
    # print("Grabbing data")
    gw.getCurrentReadings()
    return gw

def test_get_temperature():
    """ tests getting the temp """
    gw=get_single_inverter()
    assert gw.get_inverter_temperature()

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
#print(f"Current SOC: {gw.get_battery_soc()}")

inverter = get_single_inverter()
print(inverter.data.keys())
print(json.dumps(inverter.data.get('inverter').get('battery'), indent=2))
batterydata = inverter.data.get('inverter',{}).get('battery',"").split("/")
if batterydata:
        voltage = float(batterydata[0][:-1])
        print("Battery voltage is: {}".format(voltage))
#print(json.dumps(gw.data))
#print(f"Are the batteries full? {gw.are_batteries_full(fullstate=90.0)}")

#print(gw.data.keys())
#print(json.dumps(gw.data['inverter']))
#print(json.dumps(gw.data))

# print(f"PV Flow: {gw.getPVFlow()}")
# print(f"Voltage: {gw.getVoltage()}")

print("Getting XLS file")
inverter.getDayDetailedReadingsExcel(date.today() - timedelta(days=1))
