"""Tests for pygoodwe.apiv2."""

from __future__ import annotations

from typing import Any

import httpx
import pytest

import respx

from pygoodwe.apiv2.client import ApiV2, _stub_sign_token
from pygoodwe.apiv2.constants import (
    AUTH_LOGIN_PATH,
    EV_CHARGE_LOG_PATH,
    PLANT_REVENUE_OVERVIEW_PATH,
    SEMSPLUS_REGIONS,
    STATIONS_CURRENT_READINGS_PATH,
    STATIONS_LIST_PATH,
)
from pygoodwe.apiv2.exceptions import (
    ApiError,
    AuthError,
    NetworkError,
    RegionError,
    TokenExpiredError,
)
from pygoodwe.apiv2 import GoodweEv, GoodweInverter, GoodweInverters, GoodwePlant

MOCK_BASE = "https://au-semsplus.goodwe.com"


def _envelope(code: int, data: Any = None, msg: str = "") -> dict[str, Any]:
    return {"code": code, "msg": msg, "data": data}


def _token_envelope(token: str = "abc") -> dict[str, Any]:
    return _envelope(0, {"token": token})


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestBaseUrlResolution:
    @pytest.mark.parametrize("region,url", list(SEMSPLUS_REGIONS.items()))
    def test_default_regions(self, region: str, url: str) -> None:
        client = ApiV2("u", "p", region=region)
        assert client.base_url == url

    def test_resolved_region(self) -> None:
        client = ApiV2("u", "p", region="eu")
        assert client.base_url == SEMSPLUS_REGIONS["eu"]

    def test_unknown_region_raises(self) -> None:
        with pytest.raises(RegionError):
            ApiV2("u", "p", region="zz")

    def test_mqtt_url(self) -> None:
        client = ApiV2("u", "p", region="au")
        assert "au" in (client.mqtt_url or "")


class TestLogin:
    async def test_login_success(self, respx_mock: respx.MockRouter) -> None:
        respx_mock.post(MOCK_BASE + AUTH_LOGIN_PATH).mock(
            return_value=httpx.Response(200, json=_token_envelope("xyz"))
        )
        client = ApiV2("user", "pass")
        async with client:
            assert await client.do_login() is True
            assert client.token == "xyz"

    async def test_login_failure_raises_auth_error(self, respx_mock: respx.MockRouter) -> None:
        respx_mock.post(MOCK_BASE + AUTH_LOGIN_PATH).mock(
            return_value=httpx.Response(200, json=_envelope(1001, msg="bad creds"))
        )
        client = ApiV2("user", "pass")
        async with client:
            with pytest.raises(AuthError):
                await client.do_login()

    async def test_login_bad_json_raises_auth_error(self, respx_mock: respx.MockRouter) -> None:
        respx_mock.post(MOCK_BASE + AUTH_LOGIN_PATH).mock(
            return_value=httpx.Response(200, json={"not_code": 99})
        )
        client = ApiV2("user", "pass")
        async with client:
            with pytest.raises(AuthError):
                await client.do_login()


class TestCall:
    async def test_call_returns_envelope_data(self, respx_mock: respx.MockRouter) -> None:
        respx_mock.post(MOCK_BASE + AUTH_LOGIN_PATH).mock(
            return_value=httpx.Response(200, json=_token_envelope("xyz"))
        )
        respx_mock.post(MOCK_BASE + STATIONS_CURRENT_READINGS_PATH).mock(
            return_value=httpx.Response(200, json=_envelope(0, {"watts": 123}))
        )
        client = ApiV2("user", "pass")
        async with client:
            await client.do_login()
            data = await client.call(STATIONS_CURRENT_READINGS_PATH, payload={})
            assert data == {"watts": 123}

    async def test_call_raises_api_error(self, respx_mock: respx.MockRouter) -> None:
        respx_mock.post(MOCK_BASE + AUTH_LOGIN_PATH).mock(
            return_value=httpx.Response(200, json=_token_envelope("xyz"))
        )
        respx_mock.post(MOCK_BASE + STATIONS_CURRENT_READINGS_PATH).mock(
            return_value=httpx.Response(200, json=_envelope(9999, msg="fail"))
        )
        client = ApiV2("user", "pass")
        async with client:
            await client.do_login()
            with pytest.raises(ApiError) as excinfo:
                await client.call(STATIONS_CURRENT_READINGS_PATH)
            assert excinfo.value.code == 9999
            assert "fail" in excinfo.value.message


class Test401Recover:
    async def test_401_triggers_relogin(self, respx_mock: respx.MockRouter) -> None:
        respx_mock.post(MOCK_BASE + AUTH_LOGIN_PATH).mock(
            return_value=httpx.Response(200, json=_token_envelope("fresh"))
        )
        respx_mock.post(MOCK_BASE + STATIONS_CURRENT_READINGS_PATH).mock(
            side_effect=[
                httpx.Response(401, json=_envelope(401, "expired")),
                httpx.Response(200, json=_envelope(0, {"recovered": True})),
            ]
        )

        client = ApiV2("user", "pass")
        async with client:
            client.token = "old"
            data = await client.call(STATIONS_CURRENT_READINGS_PATH)
            assert data == {"recovered": True}

    async def test_401_relogin_failure_raises_token_expired(self, respx_mock: respx.MockRouter) -> None:
        respx_mock.post(MOCK_BASE + AUTH_LOGIN_PATH).mock(
            return_value=httpx.Response(200, json=_envelope(1001, msg="bad creds"))
        )
        respx_mock.post(MOCK_BASE + STATIONS_CURRENT_READINGS_PATH).mock(
            return_value=httpx.Response(401, json=_envelope(401, "expired"))
        )

        client = ApiV2("user", "pass")
        async with client:
            client.token = "old"
            with pytest.raises(TokenExpiredError):
                await client.call(STATIONS_CURRENT_READINGS_PATH, max_tries=1)


class TestStubSigner:
    def test_stub_sha256(self) -> None:
        result = _stub_sign_token('{"token":"x"}')
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex digest length


class TestInverters:
    async def test_get_station_list(self, respx_mock: respx.MockRouter) -> None:
        respx_mock.post(MOCK_BASE + AUTH_LOGIN_PATH).mock(
            return_value=httpx.Response(200, json=_token_envelope("xyz"))
        )
        respx_mock.post(MOCK_BASE + STATIONS_LIST_PATH).mock(
            return_value=httpx.Response(200, json=_envelope(0, [{"id": "s1"}]))
        )
        client = GoodweInverters("user", "pass")
        async with client:
            await client.do_login()
            data = await client.get_station_list()
            assert data == [{"id": "s1"}]


class TestInverter:
    async def test_get_current_readings_returns_single(self, respx_mock: respx.MockRouter) -> None:
        respx_mock.post(MOCK_BASE + AUTH_LOGIN_PATH).mock(
            return_value=httpx.Response(200, json=_token_envelope("xyz"))
        )
        # Use pattern to match station_id path parameter
        respx_mock.post(url__regex=r'https://au-semsplus\.goodwe\.com/web/sems/sems-plant/api/v1/stations/.*/realtime').mock(
            return_value=httpx.Response(200, json=_envelope(0, [{"sn": "inv1"}]))
        )
        client = GoodweInverter("user", "pass", station_id="abc")
        async with client:
            await client.do_login()
            data = await client.get_current_readings()
            assert isinstance(data, dict)
            assert data["sn"] == "inv1"


class TestEv:
    async def test_charge_log(self, respx_mock: respx.MockRouter) -> None:
        respx_mock.post(MOCK_BASE + AUTH_LOGIN_PATH).mock(
            return_value=httpx.Response(200, json=_token_envelope("xyz"))
        )
        respx_mock.post(MOCK_BASE + EV_CHARGE_LOG_PATH).mock(
            return_value=httpx.Response(200, json=_envelope(0, [{"kwh": 5}]))
        )
        client = GoodweEv("user", "pass")
        async with client:
            await client.do_login()
            data = await client.get_charge_log()
            assert data == [{"kwh": 5}]


class TestPlant:
    async def test_revenue_overview(self, respx_mock: respx.MockRouter) -> None:
        respx_mock.post(MOCK_BASE + AUTH_LOGIN_PATH).mock(
            return_value=httpx.Response(200, json=_token_envelope("xyz"))
        )
        respx_mock.post(MOCK_BASE + PLANT_REVENUE_OVERVIEW_PATH).mock(
            return_value=httpx.Response(200, json=_envelope(0, {"total": 100.0}))
        )
        client = GoodwePlant("user", "pass")
        async with client:
            await client.do_login()
            data = await client.get_revenue_overview("station-1")
            assert data == {"total": 100.0}


class TestNetworkErrors:
    async def test_timeout_raises_network_error(self, respx_mock: respx.MockRouter) -> None:
        respx_mock.post(MOCK_BASE + AUTH_LOGIN_PATH).mock(
            return_value=httpx.Response(200, json=_token_envelope("xyz"))
        )
        respx_mock.post(MOCK_BASE + STATIONS_CURRENT_READINGS_PATH).mock(
            side_effect=httpx.ReadTimeout("timeout")
        )
        client = ApiV2("user", "pass")
        async with client:
            await client.do_login()
            with pytest.raises(NetworkError):
                await client.call(STATIONS_CURRENT_READINGS_PATH)


class TestContextManager:
    async def test_internal_client_closed_on_exit(self) -> None:
        client = ApiV2("user", "pass")
        async with client:
            assert client._http is not None
            assert not client._external_client
        assert client._http is None