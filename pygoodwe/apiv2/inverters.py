"""GoodWe Inverter subclasses of ApiV2."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import Any, Optional

from httpx import AsyncClient

from .client import ApiV2, TokenSigner
from .constants import (
    DEFAULT_REGION,
    REPORT_EXPORT_DAY_PATH,
    REPORT_FILE_PATH_PATH,
    REPORT_POWER_REPORT_BY_MONTH_PATH,
    STATIONS_CURRENT_READINGS_PATH,
    STATIONS_LIST_PATH,
)
from .payloads import (
    DatepwIdRequest,
    IdRequest,
    MonthReportRequest,
    StationListRequest,
)

__all__ = ["GoodweInverter", "GoodweInverters"]

logger = logging.getLogger(__name__)


class GoodweInverters(ApiV2):
    """Multi-station SEMS Plus async client."""

    def __init__(
        self,
        account: str,
        password: str,
        region: str = DEFAULT_REGION,
        token: Optional[str] = None,
        user_agent: Optional[str] = None,
        sign_token: Optional[TokenSigner] = None,
        http: Optional[AsyncClient] = None,
        timeout: float = 10.0,
    ) -> None:
        super().__init__(
            account,
            password,
            region=region,
            token=token,
            user_agent=user_agent,
            sign_token=sign_token,
            http=http,
            timeout=timeout,
        )

    async def get_station_list(
        self,
        body: Optional[StationListRequest] = None,
    ) -> list[dict[str, Any]]:
        """Return a paginated list of power stations."""
        request_body = body or StationListRequest()
        data: Any = await self.call(STATIONS_LIST_PATH, payload=request_body)
        if isinstance(data, list):
            return data
        return [data]

    async def get_current_readings(self, station_id: str) -> list[dict[str, Any]]:
        """Return the latest reading batch for a station (async version)."""
        data: Any = await self.call(STATIONS_CURRENT_READINGS_PATH.format(station_id=station_id), payload={})
        if isinstance(data, list):
            return data
        return [data]

    async def get_power_report(
        self,
        report_date: date,
        page_index: int = 1,
        page_size: int = 8,
    ) -> dict[str, Any]:
        """Return the monthly power report for the given date."""
        month_str = report_date.strftime("%Y-%m")
        body = MonthReportRequest(
            date=month_str,
            pw_id="",
            page_index=page_index,
            page_size=page_size,
            is_report=1,
        )
        data: Any = await self.call(REPORT_POWER_REPORT_BY_MONTH_PATH, payload=body)
        if isinstance(data, dict):
            return data
        return {}

    async def get_day_detailed_readings(
        self,
        export_date: date,
        path: str,
        *,
        timeout: float = 30.0,
    ) -> bool:
        """Download the detailed daily XLS for a given date."""
        datestr = export_date.strftime("%Y-%m-%d")
        export_body = DatepwIdRequest(date=datestr, pw_id="")
        export_id: Any = await self.call(REPORT_EXPORT_DAY_PATH, payload=export_body)
        if not export_id:
            logger.error("No export ID returned from export request")
            return False
        file_info: Any = await self.call(REPORT_FILE_PATH_PATH, payload=IdRequest(id=str(export_id)))

        file_url = file_info.get("file_path") if isinstance(file_info, dict) else None
        if not file_url:
            logger.error("No file path returned from export")
            return False

        httpx_client = self._ensure_client()
        from .exceptions import NetworkError

        try:
            response = await httpx_client.get(file_url, timeout=timeout)
            response.raise_for_status()
            Path(path).write_bytes(response.content)
            return True
        except NetworkError:
            raise
        except Exception as exc:
            logger.error("Failed to download XLS file: %s", exc)
            return False


class GoodweInverter(GoodweInverters):
    """Single-station SEMS Plus async client.

    Overrides get_current_readings to return a single inverter dict.
    """

    def __init__(
        self,
        account: str,
        password: str,
        station_id: str,
        region: str = DEFAULT_REGION,
        token: Optional[str] = None,
        user_agent: Optional[str] = None,
        sign_token: Optional[TokenSigner] = None,
        http: Optional[AsyncClient] = None,
        timeout: float = 10.0,
    ) -> None:
        super().__init__(
            account,
            password,
            region=region,
            token=token,
            user_agent=user_agent,
            sign_token=sign_token,
            http=http,
            timeout=timeout,
        )
        self.station_id = station_id

    async def get_current_readings(self, station_id: Optional[str] = None) -> dict[str, Any]:  # type: ignore[override]
        sid = station_id or self.station_id
        result: Any = await super().get_current_readings(sid)
        if not result:
            raise ValueError("No inverter data returned")
        if isinstance(result, list):
            if not result[0]:
                raise ValueError("No inverter data returned")
            return dict(result[0])
        return dict(result)

    async def get_pv_flow(self) -> float:
        data = await self.get_current_readings()
        powerflow = data.get("powerflow") or {}
        pv = powerflow.get("pv", 0)
        if isinstance(pv, str):
            pv = pv.rstrip("(W)").strip() or "0"
        return float(pv)

    async def get_voltage(self) -> float:
        data = await self.get_current_readings()
        inverters = data.get("inverter") or {}
        if isinstance(inverters, list):
            inverters = inverters[0]
        return float(inverters.get("invert_full", {}).get("vac1", 0.0))

    async def get_load_flow(self) -> tuple[float, str]:
        data = await self.get_current_readings()
        powerflow = data.get("powerflow") or {}
        load_value = powerflow.get("load", 0.0)
        if isinstance(load_value, str):
            load_value = load_value.rstrip("(W)").strip() or "0"
        status = powerflow.get("loadStatus", 0)
        direction = "Using Battery" if status == 1 else "Importing"
        return float(load_value), direction

    async def get_battery_soc(self) -> float:
        data = await self.get_current_readings()
        inverters = data.get("inverter") or {}
        if isinstance(inverters, list):
            inverters = inverters[0]
        return float(inverters.get("soc", 0.0))

    async def get_inverter_temperature(self) -> float:
        data = await self.get_current_readings()
        inverters = data.get("inverter") or {}
        if isinstance(inverters, list):
            inverters = inverters[0]
        return float(inverters.get("tempperature", 0.0))

    async def get_day_income(self) -> float:
        data = await self.get_current_readings()
        return float(data.get("kpi", {}).get("day_income", 0.0))

    async def get_total_income(self) -> float:
        data = await self.get_current_readings()
        return float(data.get("kpi", {}).get("total_income", 0.0))

    async def get_day_power(self) -> float:
        data = await self.get_current_readings()
        return float(data.get("kpi", {}).get("power", 0.0))

    async def get_total_power(self) -> float:
        data = await self.get_current_readings()
        return float(data.get("kpi", {}).get("total_power", 0.0))

    async def get_station_location(self) -> dict[str, float]:
        data = await self.get_current_readings()
        return {
            "latitude": float(data.get("info", {}).get("latitude", 0.0)),
            "longitude": float(data.get("info", {}).get("longitude", 0.0)),
        }

    async def is_battery_full(self, fullstate: float = 100.0) -> bool:
        return await self.get_battery_soc() >= fullstate