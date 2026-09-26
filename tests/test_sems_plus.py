"""SEMS+ Web request and mapping contracts."""

import base64
import hashlib
import json
import logging

import pytest
import requests
import requests_mock

from pygoodwe import API, SingleInverter
from pygoodwe.sems_plus import GATEWAY_URL, LOGIN_URL, FailureKind, SemsPlusClient, SemsPlusError


@pytest.fixture()
def web() -> tuple[SemsPlusClient, requests_mock.Adapter]:
    session = requests.Session()
    adapter = requests_mock.Adapter()
    session.mount("https://", adapter)
    client = SemsPlusClient(session, "user", "password", logging.getLogger(__name__))
    adapter.register_uri("POST", LOGIN_URL, json={"code": 0, "data": {"uid": "u1", "token": "secret", "client": "semsPlusWeb"}})
    return client, adapter


def response(data: object) -> dict[str, object]:
    return {"code": "00000", "data": data}


def test_web_login_hashes_password_and_signs_request(web: tuple[SemsPlusClient, requests_mock.Adapter]) -> None:
    client, adapter = web
    client.login()
    request = adapter.request_history[0]
    expected = base64.b64encode(hashlib.md5(b"password", usedforsecurity=False).hexdigest().encode()).decode()
    assert json.loads(request.body)["pwd"] == expected
    signature = base64.b64decode(request.headers["X-Signature"]).decode()
    digest, timestamp = signature.split("@")
    assert digest == hashlib.sha256(f"{timestamp}@@".encode()).hexdigest()
    assert client.api_base == GATEWAY_URL


def test_web_request_renews_rejected_session(web: tuple[SemsPlusClient, requests_mock.Adapter]) -> None:
    client, adapter = web
    adapter.register_uri("GET", GATEWAY_URL + "/resource", response_list=[{"status_code": 401}, {"json": response({"ok": True})}])
    assert client.request("/resource") == {"ok": True}
    assert [request.method for request in adapter.request_history] == ["POST", "GET", "POST", "GET"]
    assert "X-Signature" in adapter.request_history[-1].headers


def test_web_rate_limit_is_not_retried(web: tuple[SemsPlusClient, requests_mock.Adapter]) -> None:
    client, adapter = web
    adapter.register_uri("GET", GATEWAY_URL + "/resource", json={"code": "GY0429"})
    with pytest.raises(SemsPlusError) as failure:
        client.request("/resource")
    assert failure.value.kind is FailureKind.RATE_LIMIT
    assert len(adapter.request_history) == 2


def register_readings(adapter: requests_mock.Adapter, *, restricted: bool = False, telemetry_denied: bool = False, multiple: bool = False) -> None:
    serials = ["SN1", "SN2"] if multiple else ["SN1"]
    adapter.register_uri(
        "GET",
        GATEWAY_URL + "/sems-plant/api/stations/device/all-status?stationId=station",
        json=response(
            {
                "deviceDetailList": [
                    {"deviceType": "INVERTER", "statusDetailList": [{"snList": serials, "detailMap": {sn: {"name": sn} for sn in serials}}]}
                ]
            }
        ),
    )
    adapter.register_uri(
        "GET",
        GATEWAY_URL + "/sems-plant/api/stations/flow?stationId=station",
        json=response({"pAc": 2.5, "pSystem": 2.7, "pGrid": 0.4, "pConsum": 1.8, "pBat": -0.1, "soc": 72}),
    )
    for serial in serials:
        suffix = "?deviceType=INVERTER&pwId=station"
        telemetry = [{"factors": [{"code": "Vac", "data": 230}, {"code": "Temperature", "data": 31}, {"code": "pAc", "data": 1.2}]}]
        counters = [{"factors": [{"code": "proPvStatsToday", "data": 5}, {"code": "proPvStatsTotal", "data": 200}]}]
        adapter.register_uri(
            "GET",
            GATEWAY_URL + f"/sems-plant/api/equipments/{serial}/telemetry{suffix}",
            json={"code": "DENIED"} if restricted or telemetry_denied else response(telemetry),
        )
        adapter.register_uri(
            "GET",
            GATEWAY_URL + f"/sems-plant/api/equipments/{serial}/telecounting{suffix}",
            json={"code": "DENIED"} if restricted else response(counters),
        )


def test_live_mapping_preserves_single_inverter_getters(web: tuple[SemsPlusClient, requests_mock.Adapter]) -> None:
    client, adapter = web
    register_readings(adapter)
    inverter = SingleInverter("station", "user", "password", skipload=True)
    inverter.session = client.session
    data = inverter.get_current_readings()
    assert isinstance(data["inverter"], dict)
    assert inverter.getPVFlow() == 2700
    assert inverter.getLoadFlow() == 1800
    assert inverter.getVoltage() == 230
    assert inverter.get_inverter_temperature() == 31
    assert inverter.get_battery_soc() == 72
    assert inverter.get_day_power() == 5
    assert inverter.get_total_power() == 200
    assert data["inverter"]["invert_full"]["pac"] == 1200
    assert data["inverter"]["invert_full"]["pmeter"] == 400


def test_multiple_inverters_do_not_receive_station_power(web: tuple[SemsPlusClient, requests_mock.Adapter]) -> None:
    client, adapter = web
    register_readings(adapter, multiple=True)
    result = client.readings("station")
    assert len(result["inverter"]) == 2
    assert result["kpi"]["power"] == 10
    assert all("pmeter" not in item["invert_full"] for item in result["inverter"])
    assert all(item["invert_full"]["pac"] == 1200 for item in result["inverter"])


def test_restricted_device_details_preserve_discovered_inverter(web: tuple[SemsPlusClient, requests_mock.Adapter]) -> None:
    client, adapter = web
    register_readings(adapter, restricted=True)
    result = client.readings("station")
    assert len(result["inverter"]) == 1
    assert result["inverter"][0]["sn"] == "SN1"
    assert result["inverter"][0]["invert_full"]["pac"] == 2500
    assert "power" not in result["kpi"]
    assert sum(request.url == LOGIN_URL for request in adapter.request_history) == 1


def test_denied_telemetry_still_fetches_counters(web: tuple[SemsPlusClient, requests_mock.Adapter]) -> None:
    client, adapter = web
    register_readings(adapter, telemetry_denied=True)
    result = client.readings("station")
    assert result["kpi"]["power"] == 5
    assert result["kpi"]["total_power"] == 200
    assert sum(request.url == LOGIN_URL for request in adapter.request_history) == 1


def test_http_403_telemetry_does_not_renew_or_skip_counters(web: tuple[SemsPlusClient, requests_mock.Adapter]) -> None:
    client, adapter = web
    register_readings(adapter)
    adapter.register_uri("GET", GATEWAY_URL + "/sems-plant/api/equipments/SN1/telemetry?deviceType=INVERTER&pwId=station", status_code=403)
    result = client.readings("station")
    assert result["kpi"]["power"] == 5
    assert sum(request.url == LOGIN_URL for request in adapter.request_history) == 1


def test_missing_grid_and_battery_still_returns_load(web: tuple[SemsPlusClient, requests_mock.Adapter]) -> None:
    client, adapter = web
    register_readings(adapter)
    adapter.register_uri(
        "GET",
        GATEWAY_URL + "/sems-plant/api/stations/flow?stationId=station",
        json=response({"pAc": 2.5, "pConsum": 1.8}),
    )
    inverter = SingleInverter("station", "user", "password", skipload=True)
    inverter.session = client.session
    data = inverter.get_current_readings()
    assert "bettery" not in data["powerflow"]
    assert inverter.getLoadFlow() == 1800
    assert inverter.loadflow_direction == "Unknown"


def test_multi_inverter_soc_is_explicitly_unavailable(web: tuple[SemsPlusClient, requests_mock.Adapter]) -> None:
    client, adapter = web
    register_readings(adapter, multiple=True)
    api = API("station", "user", "password", skipload=True)
    api.session = client.session
    api.get_current_readings()
    with pytest.raises(ValueError, match="Per-inverter state of charge is unavailable"):
        api.get_batteries_soc()
