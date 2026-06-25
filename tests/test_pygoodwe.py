"""testing module"""

from datetime import date, timedelta
import logging
import os

import pytest

from pygoodwe import SingleInverter  # , POWERFLOW_STATUS_TEXT


if os.getenv("LOG_LEVEL", "INFO") in ("DEBUG", "INFO", "WARNING"):
    log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO"))
    logging.basicConfig(
        level=log_level,
    )

# keys of the dataset:
# dict_keys(['info', 'kpi', 'images', 'weather', 'inverter', 'hjgx',
#   'pre_powerstation_id', 'nex_powerstation_id', 'homKit', 'smuggleInfo',
#   'powerflow', 'energeStatisticsCharts', 'soc'])
# print(data['info'].keys())

# data['info'].keys(): dict_keys(['powerstation_id', 'time', 'stationname',
#   'address', 'owner_name', 'owner_phone', 'owner_email', 'battery_capacity',
#   'turnon_time', 'create_time', 'capacity', 'longitude', 'latitude',
#   'powerstation_type', 'status', 'is_stored', 'is_powerflow', 'charts_type',
#   'has_pv', 'has_statistics_charts', 'only_bps', 'only_bpu', 'time_span', 'pr_value'])
# print(data['info'].keys())
# print(json.dumps(data['info'], indent=2))


@pytest.fixture(scope="session")
def inverter() -> SingleInverter:
    """used to start up the class"""
    if os.environ.get("GOODWE_USE_CONFIG", False):
        # pylint: disable=import-outside-toplevel
        try:
            from config import args
        except ImportError:
            args = dict()
            pytest.skip("Couldn't find config.py")
        print("Using config from config.py")

        goodweinverter = SingleInverter(
            system_id=args["gw_station_id"],
            account=args["gw_account"],
            password=args["gw_password"],
            # api_url=args.get('api_url'),
        )
        assert goodweinverter.do_login()

    elif os.environ.get("GOODWE_USERNAME", False):
        print("Using Environment variables for config.")
        goodweinverter = SingleInverter(
            system_id=os.environ["GOODWE_SYSTEMID"],
            account=os.environ["GOODWE_USERNAME"],
            password=os.environ["GOODWE_PASSWORD"],
        )
        assert goodweinverter.do_login()
    else:
        print("Using cached result for tests...")
        if not os.path.exists("testdata.json"):
            pytest.skip("Could not find data file 'testdata.json'")
        goodweinverter = SingleInverter("", "", "", skipload=True)
        goodweinverter.loaddata("testdata.json")

    return goodweinverter


def test_instantiate(inverter: SingleInverter) -> None:
    """tests just setting up and pulling data"""
    assert inverter.data["info"].keys()
    assert "info" in inverter.data
    print(inverter.data)


def test_get_data_pvoutput(inverter: SingleInverter) -> None:
    """tests that getDataPvoutput works"""
    print(inverter.getDataPvoutput())


# print(gw.data['info'])
# print(gw.get_station_location())

# print(gw.data['homKit'])
# assert gw.data['homKit'].keys() == [ 'homeKitLimit', 'sn' ]

# PV flow data
# gw.data['powerflow']['pv'] = str
# gw.data['powerflow']['pv'] = '2678.67(W)'
# gw.getPVFlow()

# PV Flow Status
# if gw.data['powerflow']['pvStatus'] == -1:
#    # going out
#    pvflow_direction = POWERFLOW_STATUS_TEXT.get(gw.data['powerflow']['pvStatus'], 'Unknown')
#    pass
# else:
#    raise NotImplementedError(f"data['powerflow']['pvStatus'] of {gw.data['powerflow']['pvStatus']} isn't accounted for")
# print(f"PV flow (W): {pvflow} {pvflow_direction}")

# Battery flow status
# if gw.data['powerflow']['bettery'].endswith('(W)'):
#    batteryflow = float(gw.data['powerflow']['bettery'][:-3])
# else:
#    batteryflow = float(gw.data['powerflow']['bettery'])
# batteryflow_direction = POWERFLOW_STATUS_TEXT.get(gw.data['powerflow']['betteryStatus'],'Unknown')
# print(f"Battery flow (W): {batteryflow} {batteryflow_direction}")

# Load status

# print(f"House flow (W): {loadflow} {loadflow_direction}")


def test_get_temperature(inverter: SingleInverter) -> None:
    """tests getting the temp"""
    assert isinstance(inverter.get_inverter_temperature(), float)
    assert inverter.get_inverter_temperature()


# Grid flow status
def test_flow_status(inverter: SingleInverter) -> None:
    """tests flow status"""
    if inverter.data["powerflow"]["grid"].endswith("(W)"):
        gridflow = float(inverter.data["powerflow"]["grid"][:-3])
    else:
        gridflow = float(inverter.data["powerflow"]["grid"])
    if inverter.data["powerflow"]["gridStatus"] == 1:
        gridflow_direction = "Exporting"
    else:
        raise NotImplementedError(f"gw.data['powerflow']['gridStatus'] == {inverter.data['powerflow']['gridStatus']}")
    assert isinstance(gridflow, float)
    assert gridflow_direction


# TODO: gw.data['powerflow']['hasEquipment']  - bool
def test_hasequipment_value(inverter: SingleInverter) -> None:
    """tests that the instance has a value for powerflow-hasequipment"""
    assert isinstance(inverter.data["powerflow"]["hasEquipment"], bool)
    # print(f"Hasequipment: {gw.data['powerflow']['hasEquipment']}")


# WTF is smuggle.
# print(json.dumps(gw.data['smuggleInfo'], indent=2))
# {
#   "isAllSmuggle": false,
#   "isSmuggle": false,
#   "descriptionText": null,
#   "sns": null
# }


def test_hjgx_exists(inverter: SingleInverter) -> None:
    """tests that the hjgx data is there"""
    # print(json.dumps(gw.data['hjgx'], indent=2))
    # {
    #   "co2": 0.4837444,
    #   "tree": 26.51618,
    #   "coal": 0.1960208
    # }
    if "hjgx" in inverter.data:
        assert set(inverter.data["hjgx"].keys()) == set(["co2", "tree", "coal"])


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

# print(json.dumps(gw.data['inverter'],indent=2))


def test_getvoltage(inverter: SingleInverter) -> None:
    """tests the getvoltage functino"""
    assert isinstance(inverter.getVoltage(), float)


# pylint: disable=invalid-name
def test_getDayDetailedReadingsExcel(
    inverter: SingleInverter,
    tmpdir_factory: pytest.TempdirFactory,
) -> None:
    """test downloading xls data"""
    filename = os.path.join(tmpdir_factory.mktemp("data"), "data.xls")
    if os.environ.get("GOODWE_USE_CONFIG", False):
        yesterday = date.today() - timedelta(days=1)
        # yesterday_str = yesterday.strftime("%Y-%m-%d")
        assert inverter.getDayDetailedReadingsExcel(
            export_date=yesterday,
            filename=str(filename),
            timeout=10,
        )
        assert os.path.exists(filename)
    else:
        pytest.skip()
    assert True


def test_getPowerStationPowerReportByMonth(
    inverter: SingleInverter,
) -> None:
    """monthly power report endpoint returns data for a known month"""
    if not os.environ.get("GOODWE_USE_CONFIG", False):
        pytest.skip()
    result = inverter.getPowerStationPowerReportByMonth(date(2024, 1, 1))
    assert result is not None
    assert "list" in result
    assert len(result["list"]) >= 1
    entry = result["list"][0]
    assert entry["pw_id"] == inverter.system_id
    assert isinstance(entry.get("month_power"), (int, float))
    assert isinstance(entry.get("avg_day_power"), (int, float))
    assert isinstance(entry.get("total_power"), (int, float))
