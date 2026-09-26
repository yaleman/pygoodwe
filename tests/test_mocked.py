"""mocked tests"""

import json
from datetime import date
from pathlib import Path

import pytest
import requests
import requests_mock

from pygoodwe import API, SingleInverter
from pygoodwe.sems_plus import LOGIN_URL, FailureKind, SemsPlusError


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


def test_login_fail_has_no_classic_fallback(
    mocked_session: tuple[requests.Session, requests_mock.Adapter],
    mocked_inverter: SingleInverter,
) -> None:
    session, adapter = mocked_session
    adapter.register_uri("POST", LOGIN_URL, json={"code": "C0602", "data": None})
    mocked_inverter.session = session

    assert not mocked_inverter.do_login()
    assert [request.url for request in adapter.request_history] == [LOGIN_URL]


def test_login_success_uses_web_token_and_gateway(
    mocked_session: tuple[requests.Session, requests_mock.Adapter],
    mocked_inverter: SingleInverter,
) -> None:
    session, adapter = mocked_session
    token = {"uid": "u1", "token": "secret", "client": "semsPlusWeb"}
    adapter.register_uri("POST", LOGIN_URL, json={"code": 0, "data": token})
    mocked_inverter.session = session

    assert mocked_inverter.do_login()
    assert mocked_inverter.token == json.dumps(token)
    assert mocked_inverter.headers["Token"] == json.dumps(token)
    assert mocked_inverter.base_url == "https://eu-gateway.semsportal.com/web/sems"
    assert [request.url for request in adapter.request_history] == [LOGIN_URL]


def test_readings_failure_has_no_classic_fallback(
    mocked_session: tuple[requests.Session, requests_mock.Adapter],
    mocked_inverter: SingleInverter,
) -> None:
    session, adapter = mocked_session
    adapter.register_uri("POST", LOGIN_URL, json={"code": "C0602", "data": None})
    mocked_inverter.session = session

    with pytest.raises(SemsPlusError) as failure:
        mocked_inverter.get_current_readings()
    assert failure.value.kind is FailureKind.AUTH
    assert [request.url for request in adapter.request_history] == [LOGIN_URL]


def test_legacy_call_is_explicitly_unsupported(mocked_inverter: SingleInverter) -> None:
    with pytest.raises(NotImplementedError, match="Classic API routes"):
        mocked_inverter.call("v2/PowerStation/GetMonitorDetailByPowerstationId", {})


def test_no_inverter_response_uses_existing_retry_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    api = API("station", "user", "password", skipload=True)

    class EmptyThenReady:
        api_base = "https://gateway.example.com/web/sems"

        def __init__(self) -> None:
            self.token = {"token": "ready"}
            self.attempts = 0

        def readings(self, _station_id: str) -> dict[str, object]:
            self.attempts += 1
            if self.attempts < 3:
                raise SemsPlusError(FailureKind.NO_INVERTERS, "no inverters")
            return {"inverter": [{"sn": "SN1"}]}

    client = EmptyThenReady()
    waits: list[int] = []
    monkeypatch.setattr(api, "_web_client", lambda: client)
    monkeypatch.setattr("pygoodwe.time.sleep", waits.append)

    assert api.get_current_readings(maxretries=3, delay=7)["inverter"] == [{"sn": "SN1"}]
    assert client.attempts == 3
    assert waits == [7, 7]


def test_no_inverter_response_stops_at_retry_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    api = API("station", "user", "password", skipload=True)

    class AlwaysEmpty:
        def readings(self, _station_id: str) -> dict[str, object]:
            raise SemsPlusError(FailureKind.NO_INVERTERS, "no inverters")

    monkeypatch.setattr(api, "_web_client", lambda: AlwaysEmpty())
    with pytest.raises(SemsPlusError) as failure:
        api.get_current_readings(retry=5, maxretries=5)
    assert failure.value.kind is FailureKind.NO_INVERTERS


def test_parse_value_invalid_returns_zero() -> None:
    assert API("1", "user", "pass", skipload=True).parseValue("not-a-number", "W") == 0.0


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


def test_report_and_export_fail_without_classic_requests(mocked_inverter: SingleInverter) -> None:
    with pytest.raises(NotImplementedError, match="daily Excel export"):
        mocked_inverter.getDayDetailedReadingsExcel(date(2024, 1, 2))
    with pytest.raises(NotImplementedError, match="monthly reports"):
        mocked_inverter.getPowerStationPowerReportByMonth(date(2024, 1, 1))
