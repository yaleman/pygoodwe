#!/usr/bin/env python3

import json
import os
import pytest
# keys of the dataset:
# dict_keys(['info', 'kpi', 'images', 'weather', 'inverter', 'hjgx', 'pre_powerstation_id', 'nex_powerstation_id', 'homKit', 'smuggleInfo', 'powerflow', 'energeStatisticsCharts', 'soc'])
#print(data['info'].keys())

# data['info'].keys(): dict_keys(['powerstation_id', 'time', 'stationname', 'address', 'owner_name', 'owner_phone', 'owner_email', 'battery_capacity', 'turnon_time', 'create_time', 'capacity', 'longitude', 'latitude', 'powerstation_type', 'status', 'is_stored', 'is_powerflow', 'charts_type', 'has_pv', 'has_statistics_charts', 'only_bps', 'only_bpu', 'time_span', 'pr_value'])
#print(data['info'].keys())
#print(json.dumps(data['info'], indent=2))

from pygoodwe import SingleInverter, POWERFLOW_STATUS_TEXT

def instantiate_class():
    """ used to start up the class """
    if os.environ.get('GOODWE_USERNAME', False):
        gw = SingleInverter(system_id=os.getenv('GOODWE_SYSTEMID'),
                            account=os.getenv('GOODWE_USERNAME'), 
                            password=os.getenv('GOODWE_PASSWORD'),
                            )
    else:
        gw = SingleInverter("","","", skipload=True)
        gw.loaddata('testdata.json')
    return gw


def test_instantiate():
    gw = instantiate_class()
    assert gw.data['info'].keys()
#print(gw.data['info'])
#print(gw.get_station_location())

#print(gw.data['homKit'])
#assert gw.data['homKit'].keys() == [ 'homeKitLimit', 'sn' ]

gw = instantiate_class()

POWERFLOW_STATUS_TEXT = { 
    -1 : "Outward",
}

# PV flow data
# gw.data['powerflow']['pv'] = str
# gw.data['powerflow']['pv'] = '2678.67(W)'
# gw.getPVFlow()

# PV Flow Status
#if gw.data['powerflow']['pvStatus'] == -1:
#    # going out
#    pvflow_direction = POWERFLOW_STATUS_TEXT.get(gw.data['powerflow']['pvStatus'], 'Unknown')
#    pass
#else:
#    raise NotImplementedError(f"data['powerflow']['pvStatus'] of {gw.data['powerflow']['pvStatus']} isn't accounted for")
#print(f"PV flow (W): {pvflow} {pvflow_direction}")

# Battery flow status
#if gw.data['powerflow']['bettery'].endswith('(W)'):
#    batteryflow = float(gw.data['powerflow']['bettery'][:-3])
#else:
#    batteryflow = float(gw.data['powerflow']['bettery'])
#batteryflow_direction = POWERFLOW_STATUS_TEXT.get(gw.data['powerflow']['betteryStatus'],'Unknown')
#print(f"Battery flow (W): {batteryflow} {batteryflow_direction}")

# Load status

#print(f"House flow (W): {loadflow} {loadflow_direction}")

# Grid flow status
def test_flow_status():
    gw = instantiate_class()
    if gw.data['powerflow']['grid'].endswith('(W)'):
        gridflow = float(gw.data['powerflow']['grid'][:-3])
    else:
        gridflow = float(gw.data['powerflow']['grid'])
    if gw.data['powerflow']['gridStatus'] == 1:
        gridflow_direction = "Exporting"
    else:
        raise NotImplementedError(f"gw.data['powerflow']['gridStatus'] == {gw.data['powerflow']['gridStatus']}")
    assert gridflow_direction
#print(f"Grid flow (W): {gridflow} {gridflow_direction}")

# TODO: gw.data['powerflow']['hasEquipment']  - bool
def test_hasequipment_value():
    gw = instantiate_class()
    assert isinstance(gw.data['powerflow']['hasEquipment'], bool)
    #print(f"Hasequipment: {gw.data['powerflow']['hasEquipment']}")
    

# WTF is smuggle.
# print(json.dumps(gw.data['smuggleInfo'], indent=2))
# {
#   "isAllSmuggle": false,
#   "isSmuggle": false,
#   "descriptionText": null,
#   "sns": null
# }

def test_hjgx_exists():
    gw = instantiate_class()
    # print(json.dumps(gw.data['hjgx'], indent=2))
    # {
    #   "co2": 0.4837444,
    #   "tree": 26.51618,
    #   "coal": 0.1960208
    # }
    assert set(gw.data.get('hjgx').keys()) == set(['co2', 'tree', 'coal'])


# print(json.dumps(gw.data['kpi'], indent=2))
# {
#   "pac": 2678.67, # current PV power generation
#   "power": 30.0, # kwh today
#   "total_power": 485.2, # lifetime of system
#   "day_income": 6.6, # today $ profit
#   "total_income": 106.74, # Lifetime income
#   "yield_rate": 0.22, # I think this is configurable?
#   "currency": "AUD" # confgurable
# }

#print(json.dumps(gw.data['inverter'],indent=2))

def test_getvoltage():
    #print(f"Current voltage: {gw.getVoltage()}")
    gw = instantiate_class()

    assert isinstance(gw.getVoltage(), float)
