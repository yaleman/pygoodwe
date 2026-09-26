"""Internal client for the SEMS+ Web monitoring endpoints."""

import base64
import hashlib
import json
import logging
import time
from datetime import datetime
from enum import Enum
from typing import Any

import requests

LOGIN_URL = "https://semsplus.goodwe.com/web/sems/sems-user/api/v1/auth/cross-login"
GATEWAY_URL = "https://eu-gateway.semsportal.com/web/sems"
SUCCESS_CODES = (0, "0", "00000")
WEB_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"


class FailureKind(Enum):
    AUTH = "authentication"
    PERMISSION = "permission"
    RATE_LIMIT = "rate_limit"
    TRANSPORT = "transport"
    API = "api"
    UNAVAILABLE = "unavailable"
    NO_INVERTERS = "no_inverters"


class SemsPlusError(RuntimeError):
    """A SEMS+ failure with a machine-readable kind."""

    def __init__(self, kind: FailureKind, message: str) -> None:
        super().__init__(message)
        self.kind = kind


class SemsPlusClient:
    """Authenticated requests and minimal live-reading normalization."""

    def __init__(self, session: requests.Session, account: str, password: str, logger: logging.Logger) -> None:
        self.session = session
        self.account = account
        self.password = password
        self.logger = logger
        self.token: dict[str, Any] | None = None
        self.api_base = GATEWAY_URL

    @staticmethod
    def _signature(token: dict[str, Any]) -> str:
        timestamp = round(time.time() * 1000)
        digest = hashlib.sha256(f"{timestamp}@{token.get('uid', '')}@{token.get('token', '')}".encode()).hexdigest()
        return base64.b64encode(f"{digest}@{timestamp}".encode()).decode()

    def login(self, timeout: int = 10) -> None:
        password_hash = hashlib.md5(self.password.encode(), usedforsecurity=False).hexdigest()
        password_encoded = base64.b64encode(password_hash.encode()).decode()
        try:
            response = self.session.post(
                LOGIN_URL,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/plain, */*",
                    "Origin": "https://semsplus.goodwe.com",
                    "Referer": "https://semsplus.goodwe.com/",
                    "Token": json.dumps({"uid": "", "timestamp": 0, "token": "", "client": "semsPlusWeb", "version": "", "language": "en"}),
                    "X-Signature": self._signature({}),
                    "User-Agent": WEB_USER_AGENT,
                },
                json={"account": self.account, "pwd": password_encoded, "agreement": 1, "isChinese": False, "isLocal": False},
                timeout=timeout,
            )
            if response.status_code == 429:
                raise SemsPlusError(FailureKind.RATE_LIMIT, "SEMS+ rate limit reached")
            if response.status_code in (401, 403):
                raise SemsPlusError(FailureKind.AUTH, "SEMS+ login was rejected")
            response.raise_for_status()
            body = response.json()
        except SemsPlusError:
            raise
        except (requests.RequestException, ValueError) as exc:
            raise SemsPlusError(FailureKind.TRANSPORT, "SEMS+ login request failed") from exc
        if isinstance(body, dict) and body.get("code") == "GY0429":
            raise SemsPlusError(FailureKind.RATE_LIMIT, "SEMS+ rate limit reached")
        if not isinstance(body, dict) or body.get("code") not in SUCCESS_CODES:
            raise SemsPlusError(FailureKind.AUTH, "SEMS+ login was rejected")
        token = body.get("data")
        if not isinstance(token, dict) or not isinstance(token.get("token"), str) or not token["token"]:
            raise SemsPlusError(FailureKind.AUTH, "SEMS+ login returned no token")
        self.token = token
        api = body.get("api") or token.get("api")
        self.api_base = api.rstrip("/") if isinstance(api, str) and api.startswith("https://") else GATEWAY_URL

    def request(self, path: str, *, method: str = "GET", payload: dict[str, Any] | None = None, timeout: int = 10) -> Any:
        if self.token is None:
            self.login(timeout)
        for attempt in range(2):
            token = self.token
            if token is None:
                raise SemsPlusError(FailureKind.AUTH, "SEMS+ session is unavailable")
            try:
                response = self.session.request(
                    method,
                    self.api_base + path,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                        "User-Agent": WEB_USER_AGENT,
                        "Token": json.dumps(token),
                        "X-Signature": self._signature(token),
                    },
                    json=payload,
                    timeout=timeout,
                )
                if response.status_code == 429:
                    raise SemsPlusError(FailureKind.RATE_LIMIT, "SEMS+ rate limit reached")
                if response.status_code == 403:
                    raise SemsPlusError(FailureKind.PERMISSION, "SEMS+ access denied")
                if response.status_code == 401:
                    if attempt == 0:
                        self.login(timeout)
                        continue
                    raise SemsPlusError(FailureKind.AUTH, "SEMS+ session was rejected")
                response.raise_for_status()
                body = response.json()
            except SemsPlusError:
                raise
            except (requests.RequestException, ValueError) as exc:
                raise SemsPlusError(FailureKind.TRANSPORT, "SEMS+ request failed") from exc
            if not isinstance(body, dict):
                raise SemsPlusError(FailureKind.API, "SEMS+ returned an invalid response")
            code = body.get("code")
            if code == "GY0429":
                raise SemsPlusError(FailureKind.RATE_LIMIT, "SEMS+ rate limit reached")
            if code not in SUCCESS_CODES:
                if code == "C0602" and attempt == 0:
                    self.login(timeout)
                    continue
                kind = FailureKind.AUTH if code == "C0602" else FailureKind.API
                raise SemsPlusError(kind, "SEMS+ rejected the request")
            return body.get("data")
        raise SemsPlusError(FailureKind.AUTH, "SEMS+ session renewal failed")

    @staticmethod
    def _number(value: Any) -> float | None:
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _factors(groups: Any) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if isinstance(groups, list):
            for group in groups:
                if isinstance(group, dict) and isinstance(group.get("factors"), list):
                    for factor in group["factors"]:
                        if isinstance(factor, dict) and isinstance(factor.get("code"), str) and factor.get("data") is not None:
                            result[factor["code"]] = factor["data"]
        return result

    def _devices(self, station_id: str) -> list[dict[str, Any]]:
        data = self.request(f"/sems-plant/api/stations/device/all-status?stationId={station_id}")
        devices: list[dict[str, Any]] = []
        if not isinstance(data, dict):
            raise SemsPlusError(FailureKind.UNAVAILABLE, "SEMS+ device status is unavailable")
        for group in data.get("deviceDetailList", []):
            if not isinstance(group, dict) or group.get("deviceType") not in ("INVERTER", "ENERGY_STORAGE_INTEGRATED_CABINET"):
                continue
            for status in group.get("statusDetailList", []):
                if not isinstance(status, dict):
                    continue
                details = status.get("detailMap", {})
                if not isinstance(details, dict):
                    continue
                for serial in status.get("snList", []):
                    detail = details.get(serial)
                    if isinstance(serial, str) and isinstance(detail, dict):
                        devices.append({**detail, "sn": serial, "status": status.get("status"), "deviceType": group["deviceType"]})
        return devices

    def readings(self, station_id: str) -> dict[str, Any]:
        """Return available SEMS+ readings in the public Classic data layout."""
        devices = self._devices(station_id)
        if not devices:
            raise SemsPlusError(FailureKind.NO_INVERTERS, "SEMS+ returned no inverters")
        flow = self.request(f"/sems-plant/api/stations/flow?stationId={station_id}")
        if not isinstance(flow, dict):
            raise SemsPlusError(FailureKind.UNAVAILABLE, "SEMS+ station flow is unavailable")
        result: dict[str, Any] = {
            "info": {"powerstation_id": station_id, "time": datetime.now().astimezone().strftime("%m/%d/%Y %H:%M:%S")},
            "kpi": {},
            "powerflow": {},
            "inverter": [],
        }
        for device in devices:
            serial = device["sn"]
            suffix = f"?deviceType={device['deviceType']}&pwId={station_id}"
            telemetry: dict[str, Any] = {}
            counters: dict[str, Any] = {}
            try:
                telemetry = self._factors(self.request(f"/sems-plant/api/equipments/{serial}/telemetry{suffix}"))
            except SemsPlusError as exc:
                if exc.kind is FailureKind.RATE_LIMIT:
                    raise
                self.logger.debug("SEMS+ telemetry unavailable for %s: %s", serial, exc.kind.value)
            try:
                counters = self._factors(self.request(f"/sems-plant/api/equipments/{serial}/telecounting{suffix}"))
            except SemsPlusError as exc:
                if exc.kind is FailureKind.RATE_LIMIT:
                    raise
                self.logger.debug("SEMS+ counters unavailable for %s: %s", serial, exc.kind.value)
            full: dict[str, Any] = {"sn": serial, "powerstation_id": station_id, "deviceType": device["deviceType"]}
            for source, target in (("Vac", "vac1"), ("PHASE-A:Vac", "vac1"), ("Temperature", "tempperature"), ("soc", "soc")):
                value = self._number(telemetry.get(source))
                if value is not None:
                    full[target] = value
            for source, target, scale in (("pAc", "pac", 1000), ("proPvStatsToday", "eday", 1), ("proPvStatsTotal", "etotal", 1)):
                value = self._number(telemetry.get(source) if source == "pAc" else counters.get(source))
                if value is not None:
                    full[target] = value * scale
            inverter = {"sn": serial, "invert_full": full}
            if "tempperature" in full:
                inverter["tempperature"] = full["tempperature"]
            result["inverter"].append(inverter)
        powerflow = result["powerflow"]
        for source, target in (("pSystem", "pv"), ("pGrid", "grid"), ("pConsum", "load"), ("pBat", "bettery")):
            value = self._number(flow.get(source))
            if value is not None:
                powerflow[target] = str(value * 1000)
        if "pv" not in powerflow and (pac := self._number(flow.get("pAc"))) is not None:
            powerflow["pv"] = str(pac * 1000)
        if (soc := self._number(flow.get("soc"))) is not None:
            result["soc"] = {"power": soc}
            powerflow["soc"] = soc
        if (grid := self._number(flow.get("pGrid"))) is not None:
            powerflow["gridStatus"] = -1 if grid > 0 else 1
            powerflow["loadStatus"] = powerflow["gridStatus"]
        if (pac := self._number(flow.get("pAc"))) is not None:
            result["kpi"]["pac"] = pac * 1000
            if len(result["inverter"]) == 1:
                result["inverter"][0]["invert_full"].setdefault("pac", pac * 1000)
        if len(result["inverter"]) == 1 and (grid := self._number(flow.get("pGrid"))) is not None:
            result["inverter"][0]["invert_full"].setdefault("pmeter", grid * 1000)
        for key, source in (("power", "eday"), ("total_power", "etotal")):
            values = [item["invert_full"][source] for item in result["inverter"] if source in item["invert_full"]]
            if len(values) == len(result["inverter"]):
                result["kpi"][key] = sum(values)
        return result
