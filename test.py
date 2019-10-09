#!/usr/bin/env python3

import json
from config import args
from pygoodwe import API, SingleInverter

gw = SingleInverter(
        system_id=args.get('gw_station_id'), 
        account=args.get('gw_account'), 
        password=args.get('gw_password'),
        )
print("Grabbing data")
gw.getCurrentReadings(raw=True)

# battery state of charge
print(f"Current SOC: {gw.get_battery_soc()}")

#print(json.dumps(gw.data))
print(f"Are the batteries full? {gw.are_batteries_full(fullstate=90.0)}")

#print(gw.data.keys())
#print(json.dumps(gw.data['inverter']))
#print(json.dumps(gw.data))

print(f"PV Flow: {gw.getPVFlow()}")
print(f"Voltage: {gw.getVoltage()}")