""" testing module """

from datetime import date, timedelta
import json
from json.decoder import JSONDecodeError

import requests
import os
import pytest
import logging


if os.getenv("LOG_LEVEL", "INFO") in ("DEBUG", "INFO", "WARNING"):
    log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO"))
    logging.basicConfig(
        level=log_level,
    )

# keys of the dataset:
# dict_keys(['info', 'kpi', 'images', 'weather', 'inverter', 'hjgx',
#   'pre_powerstation_id', 'nex_powerstation_id', 'homKit', 'smuggleInfo',
#   'powerflow', 'energeStatisticsCharts', 'soc'])
#print(data['info'].keys())

# data['info'].keys(): dict_keys(['powerstation_id', 'time', 'stationname',
#   'address', 'owner_name', 'owner_phone', 'owner_email', 'battery_capacity',
#   'turnon_time', 'create_time', 'capacity', 'longitude', 'latitude',
#   'powerstation_type', 'status', 'is_stored', 'is_powerflow', 'charts_type',
#   'has_pv', 'has_statistics_charts', 'only_bps', 'only_bpu', 'time_span', 'pr_value'])
#print(data['info'].keys())
#print(json.dumps(data['info'], indent=2))

from pygoodwe import SingleInverter #, POWERFLOW_STATUS_TEXT

@pytest.fixture(scope="session")
def inverter():
    """ used to start up the class """
    if os.environ.get("GOODWE_USE_CONFIG", False):
        #pylint: disable=import-outside-toplevel
        from config import args
        logging.info("Using config from config.py")

        goodweinverter = SingleInverter(
            system_id=args.get('gw_station_id'),
            account=args.get('gw_account'),
            password=args.get('gw_password'),
            # api_url=args.get('api_url'),
        )
    elif os.environ.get('GOODWE_USERNAME', False):
        logging.info("Using Environment variables for config.")
        goodweinverter = SingleInverter(system_id=os.getenv('GOODWE_SYSTEMID'),
                            account=os.getenv('GOODWE_USERNAME'),
                            password=os.getenv('GOODWE_PASSWORD'),
                            )
    else:
        logging.info("Using cached result for tests...")
        goodweinverter = SingleInverter("","","", skipload=True)
        goodweinverter.loaddata('testdata.json')

    assert goodweinverter.do_login()

    return goodweinverter


def test_instantiate(inverter):
    """ tests just setting up and pulling data """
    assert inverter.data['info'].keys()
    assert "info" in inverter.data
#print(gw.data['info'])
#print(gw.get_station_location())

#print(gw.data['homKit'])
#assert gw.data['homKit'].keys() == [ 'homeKitLimit', 'sn' ]

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


def test_get_temperature(inverter):
    """ tests getting the temp """
    assert isinstance(inverter.get_inverter_temperature(), float)
    assert inverter.get_inverter_temperature()

# Grid flow status
def test_flow_status(inverter):
    """ tests flow status """
    if inverter.data['powerflow']['grid'].endswith('(W)'):
        gridflow = float(inverter.data['powerflow']['grid'][:-3])
    else:
        gridflow = float(inverter.data['powerflow']['grid'])
    if inverter.data['powerflow']['gridStatus'] == 1:
        gridflow_direction = "Exporting"
    else:
        raise NotImplementedError(f"gw.data['powerflow']['gridStatus'] == {inverter.data['powerflow']['gridStatus']}")
    assert isinstance(gridflow, float)
    assert gridflow_direction

# TODO: gw.data['powerflow']['hasEquipment']  - bool
def test_hasequipment_value(inverter):
    assert isinstance(inverter.data['powerflow']['hasEquipment'], bool)
    #print(f"Hasequipment: {gw.data['powerflow']['hasEquipment']}")


# WTF is smuggle.
# print(json.dumps(gw.data['smuggleInfo'], indent=2))
# {
#   "isAllSmuggle": false,
#   "isSmuggle": false,
#   "descriptionText": null,
#   "sns": null
# }

def test_hjgx_exists(inverter):
    """ tests that the hjgx data is there """
    # print(json.dumps(gw.data['hjgx'], indent=2))
    # {
    #   "co2": 0.4837444,
    #   "tree": 26.51618,
    #   "coal": 0.1960208
    # }
    assert set(inverter.data.get('hjgx').keys()) == set(['co2', 'tree', 'coal'])


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

def test_getvoltage(inverter):
    #print(f"Current voltage: {gw.getVoltage()}")

    assert isinstance(inverter.getVoltage(), float)

def test_getDayDetailedReadingsExcel(inverter, tmpdir_factory):
    """ test downloading xls data """
    filename = tmpdir_factory.mktemp("data").join("data.xls")
    if os.environ.get("GOODWE_USE_CONFIG", False):
        yesterday = date.today() - timedelta(days=1)
        # yesterday_str = yesterday.strftime("%Y-%m-%d")
        assert inverter.getDayDetailedReadingsExcel(date=yesterday, filename=filename, max_tries=1, timeout=10)
        assert os.path.exists(filename)
    else:
        pytest.skip()
    assert True

def test_report(inverter, tmpdir_factory):
    """manually doing it"""
    # Request URL: https://www.semsportal.com/GopsApi/Post?s=v1/ReportData/GetPowerStationPowerReportByMonth
    # str: {"api":"v1/ReportData/GetPowerStationPowerReportByMonth","param":{"date":"2021-12-21","pw_areacode":"","org_id":"","page_index":1,"page_size":1,"is_report":2}}

    payload = {
        "str" :  json.dumps({
           "api" : "v1/ReportData/GetPowerStationPowerReportByMonth",
            "param" : {
                "date" : (date.today()-timedelta(days=1)).strftime("%Y-%m-%d"),
                "pw_areacode" : "",
                "org_id" : "",
                "page_index" : 1,
                "page_size" : 8,
                "is_report" : 1,
            },
        })
    }
    headers = dict(inverter.headers)
    headers["Referer"] = "https://www.semsportal.com/Statement/PowerDataByMonth"
    headers["X-Requested-With"] = "XMLHttpRequest"

    inverter.do_login()
    # logging.error(json.dumps(inverter.headers))
    url = "https://www.semsportal.com/GopsApi/Post?s=v1/ReportData/GetPowerStationPowerReportByMonth"
    response = inverter.session.post(url=url,
                                     data=payload,
                                     headers=headers,
                                     cookies=inverter.session.cookies,
                                     )
    response.raise_for_status()

    try:
        responsedata = response.json()
    except JSONDecodeError as error_message:
        logging.error("JSON Decode error: %s\n%s", error_message, response.content)
        pytest.fail()
    if responsedata.get("hasError"):
        pytest.fail()
    if responsedata.get('msg').lower() not in ("success", "successful"):
        logging.error("Failed pulling the download ID!")
        logging.error(response.request.url)
        logging.error("Req headers: %s", json.dumps(response.request.headers, default=str))
        logging.error(responsedata)
        logging.error(inverter.session.cookies)

        pytest.fail()


    download_id = responsedata.get("data",{}).get("qry_id", {})
    print(f"Download ID: {download_id}")

    # Response
    # {
    #   "hasError": false,
    #   "code": 0,
    #   "msg": "Successful",
    #   "data": {
    #     "record": 1,
    #     "list": [
    #       {
    #         "pw_id": "<station_id>",
    #         "pw_name": "<name>",
    #         "capacity": 1.0,
    #         "address": "<address>",
    #         "owner_id": "<uuid>",
    #         "owner_name": null,
    #         "email": "user@example.com",
    #         "month_power": 663.3,
    #         "avg_day_power": 31.6,
    #         "total_power": 1.2,
    #         "power_list": null
    #       }
    #     ],
    #     "qry_id": "<download_id>"
    #   },
    #   "components": {
    #     "para": null,
    #     "langVer": 125,
    #     "timeSpan": 0,
    #     "api": "http://localhost:82/api/v1/ReportData/GetPowerStationPowerReportByMonth",
    #     "msgSocketAdr": ""
    #   }
    # }

    response = requests.post(url="https://www.semsportal.com/GopsApi/Post",
        params={
            "s": "v1/ReportData/GetStationPowerDataFilePath",
            },
        data = {
            "api" : "v1/ReportData/GetStationPowerDataFilePath",
            "param" : {
                "id" : download_id,
            }
        },
    )
    response.raise_for_status()

    try:
        responsedata = response.json()
    except JSONDecodeError as error_message:
        logging.error("JSON Decode error: %s\n%s", error_message, response.content)
        pytest.fail()
    if responsedata.get("hasError"):
        pytest.fail()
    if responsedata.get('msg').lower() not in ("success", "successful"):
        logging.error("Failed!")
        pytest.fail()

    download_url = responsedata.get("data",{}).get("file_path", False)
    if not download_url:
        logging.error("Failed to get download URL from data:\n%s", responsedata.content)
        # return False
        pytest.fail()

    # Request URL: https://www.semsportal.com/GopsApi/Post?s=v1/ReportData/GetStationPowerDataFilePath
    # str: {"api":"v1/ReportData/GetStationPowerDataFilePath",
    #       "param":{"id":"<download_id>"}
    # }

    # Response
    # {
    #     "hasError": false,
    #     "code": 0,
    #     "msg": "Successful",
    #     "data": {
    #         "file_path": "<download_url>"
    #     },
    #     "components": {
    #         "para": null,
    #         "langVer": 125,
    #         "timeSpan": 0,
    #         "api": "http://localhost:82/api/v1/ReportData/GetStationPowerDataFilePath",
    #         "msgSocketAdr": ""
    #     }
    # }
