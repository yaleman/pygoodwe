""" mocked tests """
from datetime import date
import json
from pathlib import Path
import time

import pytest
import requests
import requests_mock

from pygoodwe import API, SingleInverter


@pytest.fixture()
def mocked_session() -> tuple[requests.Session, requests_mock.Adapter]:
    session = requests.Session()
    adapter = requests_mock.Adapter()
    session.mount("https://", adapter)
    return session, adapter


@pytest.fixture()
def mocked_inverter(
    mocked_session: tuple[requests.Session, requests_mock.Adapter],
) -> SingleInverter:
    session, _adapter = mocked_session
    goodwe = SingleInverter("1", "user", "pass", skipload=True)
    goodwe.session = session
    return goodwe


def test_login_fail(
    mocked_session: tuple[requests.Session, requests_mock.Adapter],
    mocked_inverter: SingleInverter,
) -> None:
    fail_response_body = """{
  "hasError": false,
  "code": 100005,
  "msg": "Email or password error.",
  "data": null,
  "components": {
    "para": null,
    "langVer": 179,
    "timeSpan": 0,
    "api": "http://semsportal.com:85/api/v2/Common/CrossLogin",
    "msgSocketAdr": "https://eu-xxzx.semsportal.com"
  }
}"""
    # login detail don't matter as we're mocking it
    print("setting up api")
    goodwe = mocked_inverter

    print("setting up session mock")
    session, adapter = mocked_session

    adapter.register_uri(
        method="POST",
        url=goodwe.global_url + "v2/Common/CrossLogin",
        json=json.loads(fail_response_body),
        status_code=200,
    )
    goodwe.session = session

    login_result = goodwe.do_login()

    print(f"{login_result=}")
    print(f"{adapter.request_history=}")
    assert not login_result


def test_login_success_sets_base_url_and_token(
    mocked_session: tuple[requests.Session, requests_mock.Adapter],
    mocked_inverter: SingleInverter,
) -> None:
    success_body = {
        "hasError": False,
        "code": 0,
        "msg": "success",
        "data": {"token": "abc123"},
        "api": "https://example.semsportal.com/api/",
    }
    goodwe = mocked_inverter
    session, adapter = mocked_session
    adapter.register_uri(
        method="POST",
        url=goodwe.global_url + "v2/Common/CrossLogin",
        json=success_body,
        status_code=200,
    )
    goodwe.session = session

    assert goodwe.do_login()
    assert goodwe.base_url == "https://example.semsportal.com/api/"
    assert goodwe.token == json.dumps(success_body["data"])


def test_login_request_exception(
    mocked_session: tuple[requests.Session, requests_mock.Adapter],
    mocked_inverter: SingleInverter,
) -> None:
    goodwe = mocked_inverter
    session, adapter = mocked_session
    adapter.register_uri(
        method="POST",
        url=goodwe.global_url + "v2/Common/CrossLogin",
        exc=requests.exceptions.ConnectTimeout,
    )
    goodwe.session = session

    assert not goodwe.do_login()


def test_call_success_message_returns_data(
    mocked_session: tuple[requests.Session, requests_mock.Adapter],
    mocked_inverter: SingleInverter,
) -> None:
    goodwe = mocked_inverter
    session, adapter = mocked_session
    adapter.register_uri(
        method="POST",
        url=goodwe.base_url + "v2/PowerStation/GetMonitorDetailByPowerstationId",
        json={"msg": "Success", "data": {"info": {"stationname": "Test"}}},
        status_code=200,
    )
    goodwe.session = session

    data = goodwe.call("v2/PowerStation/GetMonitorDetailByPowerstationId", {"powerStationId": "1"})
    assert data == {"info": {"stationname": "Test"}}


def test_call_relogin_then_success(
    monkeypatch: pytest.MonkeyPatch,
    mocked_session: tuple[requests.Session, requests_mock.Adapter],
    mocked_inverter: SingleInverter,
) -> None:
    goodwe = mocked_inverter
    session, adapter = mocked_session
    adapter.register_uri(
        method="POST",
        url=goodwe.base_url + "v2/PowerStation/GetMonitorDetailByPowerstationId",
        response_list=[
            {"json": {"msg": "something else"}, "status_code": 200},
            {"json": {"msg": "success", "data": {"ok": True}}, "status_code": 200},
        ],
    )
    adapter.register_uri(
        method="POST",
        url=goodwe.global_url + "v2/Common/CrossLogin",
        json={"code": 0, "msg": "success", "data": {"token": "t"}},
        status_code=200,
    )
    goodwe.session = session
    monkeypatch.setattr(time, "sleep", lambda *_args, **_kwargs: None)

    data = goodwe.call("v2/PowerStation/GetMonitorDetailByPowerstationId", {"powerStationId": "1"})
    assert data == {"ok": True}


def test_get_current_readings_missing_inverter_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    goodwe = API("1", "user", "pass", skipload=True)
    monkeypatch.setattr(goodwe, "call", lambda *_args, **_kwargs: {"info": {"stationname": "Test"}})
    with pytest.raises(SystemExit):
        goodwe.get_current_readings(retry=5, maxretries=5)


def test_parse_value_invalid_returns_zero() -> None:
    assert API.parseValue("not-a-number", "W") == 0.0


def test_single_inverter_load_flow_branches(mocked_inverter: SingleInverter) -> None:
    goodwe = mocked_inverter
    goodwe.data = {
        "powerflow": {"bettery": "0(W)", "load": "123(W)", "loadStatus": -1},
    }
    assert goodwe.getLoadFlow() == 123.0
    assert goodwe.loadflow_direction == "Importing"

    goodwe.data["powerflow"]["bettery"] = "0"
    goodwe.data["powerflow"]["load"] = "55"
    assert goodwe.getLoadFlow() == 55.0
    assert goodwe.loadflow_direction == "Importing"

    goodwe.data["powerflow"]["loadStatus"] = 1
    assert goodwe.getLoadFlow() == 55.0
    assert goodwe.loadflow_direction == "Using Battery"


def test_single_inverter_load_flow_unknown_status_raises(mocked_inverter: SingleInverter) -> None:
    goodwe = mocked_inverter
    goodwe.data = {
        "powerflow": {"bettery": "0", "load": "50", "loadStatus": 0},
    }
    with pytest.raises(ValueError):
        goodwe.getLoadFlow()


def test_single_inverter_battery_soc_missing_raises(mocked_inverter: SingleInverter) -> None:
    goodwe = mocked_inverter
    goodwe.data = {"soc": None}
    with pytest.raises(ValueError):
        goodwe.get_battery_soc()


def test_single_inverter_station_location(mocked_inverter: SingleInverter) -> None:
    goodwe = mocked_inverter
    goodwe.data = {"info": {"latitude": -33.9, "longitude": 151.2}}
    assert goodwe.get_station_location() == {"latitude": -33.9, "longitude": 151.2}


def test_single_inverter_loaddata_reduces_inverter(
    tmp_path: Path,
    mocked_inverter: SingleInverter,
) -> None:
    data = {
        "inverter": [{"invert_full": {"vac1": "230"}}],
        "info": {"time": "01/01/2024 00:00:00"},
    }
    file_path = tmp_path / "data.json"
    file_path.write_text(json.dumps(data), encoding="utf8")

    mocked_inverter.loaddata(str(file_path))
    assert isinstance(mocked_inverter.data["inverter"], dict)
    assert mocked_inverter.data["inverter"]["invert_full"]["vac1"] == "230"


def test_get_day_detailed_readings_excel_success(
    tmp_path: Path,
    mocked_inverter: SingleInverter,
) -> None:
    goodwe = mocked_inverter
    export_id = "export-id"

    with requests_mock.Mocker() as http_mock:
        http_mock.post(
            goodwe.base_url + "v1/PowerStation/ExportPowerstationPac",
            json={"msg": "success", "data": export_id},
            status_code=200,
        )
        http_mock.post(
            goodwe.base_url + "v1/ReportData/GetStationPowerDataFilePath",
            json={"msg": "success", "data": {"file_path": "https://files.example.com/file.xls"}},
            status_code=200,
        )
        http_mock.get("https://files.example.com/file.xls", content=b"binary")
        target = tmp_path / "output.xls"
        assert goodwe.getDayDetailedReadingsExcel(date(2024, 1, 2), filename=str(target))
        assert target.read_bytes() == b"binary"
