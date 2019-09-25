__version__ = "0.0.1"

__all__ = []

import json
from .api import API
import logging
from datetime import datetime
import argparse
import sys
import time

def run_once(args):
    #global last_eday_kwh

    # Check if we only want to run during daylight
    #if args.city:
    #    a = Astral()
    #    sun = a[args.city].sun(local=True)
    #    now = datetime.time(datetime.now())
    #    if now < sun['dawn'].time() or now > sun['dusk'].time():
    #        logging.debug("Skipped upload as it's night")
    #        return

    # Fetch the last reading from GoodWe
    gw = API(
        system_id=args.get('gw_station_id'), 
        account=args.get('gw_account'), 
        password=args.get('gw_password'),
        lang='en',
        )
    data = gw.getCurrentReadings()

    # Check if we want to abort when offline
    #if args.get('skip_offline'):
    #    if data['status'] == 'Offline':
    #        logging.debug("Skipped upload as the inverter is offline")
    #        return

    # Append reading to CSV file
    if args.get('csv'):
        raise NotImplementedError("Haven't done the CSV thing yet.")
    #    if data['status'] == 'Offline':
    #        logging.debug("Don't append offline data to CSV file")
    #    else:
    #        locale.setlocale(locale.LC_ALL, locale.getlocale())
    #        csv = gw_csv.GoodWeCSV(args.csv)
    #        csv.append(data)

    # Submit reading to PVOutput, if they differ from the previous set
    #eday_kwh = data['eday_kwh']
    #if data['pgrid_w'] == 0 and abs(eday_kwh - last_eday_kwh) < 0.001:
    #    logging.debug("Ignore unchanged reading")
    #else:
    #    last_eday_kwh = eday_kwh

    #if args.darksky_api_key:
    #    ds = ds_api.DarkSkyApi(args.darksky_api_key)
    #    data['temperature'] = ds.get_temperature(data['latitude'], data['longitude'])
        
    #voltage = data['grid_voltage']
    if args.get("pv_voltage"):
        #voltage=data['pv_voltage']
        pass
    return data
    #pvo = pvo_api.PVOutputApi(args.pvo_system_id, args.pvo_api_key)
    #pvo.add_status(data['pgrid_w'], last_eday_kwh, data.get('temperature'), voltage)


#def copy(args):
    # Fetch readings from GoodWe
    #date = datetime.strptime(args.date, "%Y-%m-%d")

    #gw = API(args.gw_station_id, args.gw_account, args.gw_password)
    #data = gw.getDayReadings(date)

    #if args.darksky_api_key:
    #    ds = ds_api.DarkSkyApi(args.darksky_api_key)
    #    temperatures = ds.get_temperature_for_day(data['latitude'], data['longitude'], date)
    #else:
    #    temperatures = None
    #temperatures = None
    # Submit readings to PVOutput
    #pvo = pvo_api.PVOutputApi(args.pvo_system_id, args.pvo_api_key)
    #pvo.add_day(data['entries'], temperatures)

