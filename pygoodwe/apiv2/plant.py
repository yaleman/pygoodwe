"""GoodWe Plant-level KPI client."""

from __future__ import annotations

import logging
from typing import Any, Optional

from httpx import AsyncClient

from .client import ApiV2, TokenSigner
from .constants import (
    DEFAULT_REGION,
    PLANT_BASIC_PATH,
    PLANT_POWER_STATISTICS_PATH,
    PLANT_REVENUE_CALENDAR_PATH,
    PLANT_REVENUE_CURVE_PATH,
    PLANT_REVENUE_OVERVIEW_PATH,
    PLANT_REVENUE_TOTAL_PATH,
)
from .payloads import PowerstationIdRequest

__all__ = ["GoodwePlant"]

logger = logging.getLogger(__name__)


class GoodwePlant(ApiV2):
    """Plant-level KPIs via the SEMS Plus HEMS endpoints."""

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

    async def get_revenue_overview(self, station_id: str) -> dict[str, Any]:
        data: Any = await self.call(
            PLANT_REVENUE_OVERVIEW_PATH,
            payload=PowerstationIdRequest(powerstation_id=station_id),
        )
        return data if isinstance(data, dict) else {}

    async def get_revenue_curve(self, station_id: str) -> dict[str, Any]:
        data: Any = await self.call(
            PLANT_REVENUE_CURVE_PATH,
            payload=PowerstationIdRequest(powerstation_id=station_id),
        )
        return data if isinstance(data, dict) else {}

    async def get_revenue_calendar(self, station_id: str) -> dict[str, Any]:
        data: Any = await self.call(
            PLANT_REVENUE_CALENDAR_PATH,
            payload=PowerstationIdRequest(powerstation_id=station_id),
        )
        return data if isinstance(data, dict) else {}

    async def get_revenue_total(self, station_id: str) -> dict[str, Any]:
        data: Any = await self.call(
            PLANT_REVENUE_TOTAL_PATH,
            payload=PowerstationIdRequest(powerstation_id=station_id),
        )
        return data if isinstance(data, dict) else {}

    async def get_power_statistics(self, station_id: str) -> dict[str, Any]:
        data: Any = await self.call(
            PLANT_POWER_STATISTICS_PATH,
            payload=PowerstationIdRequest(powerstation_id=station_id),
        )
        return data if isinstance(data, dict) else {}

    async def get_plant_basic(self) -> dict[str, Any]:
        data: Any = await self.call(PLANT_BASIC_PATH)
        return data if isinstance(data, dict) else {}
