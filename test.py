#!/usr/bin/env python3

import json
from config import args
from pygoodwe.api import API

gw = API(
        system_id=args.get('gw_station_id'), 
        account=args.get('gw_account'), 
        password=args.get('gw_password'),
        lang='en',
        )
gw.getCurrentReadings(raw=True)

# battery state of charge
print(f"Current SOC: {gw.get_battery_soc()}")

#print(json.dumps(gw.data))
print(f"Are the batteries full? {gw.are_batteries_full(fullstate=90.0)}")
