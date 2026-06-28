"""GoodWe EV charger async client."""

from __future__ import annotations

import logging
from typing import Any, Optional

from httpx import AsyncClient

from .client import ApiV2, TokenSigner
from .constants import (
    DEFAULT_REGION,
    EV_CHARGE_LOG_PATH,
    EV_CONFIG_PATH,
    EV_SCHEDULED_CHARGE_PATH,
    EV_START_CHARGE_PATH,
    EV_STOP_CHARGE_PATH,
)
from .payloads import EvConfigPayload, EvSchedulePayload

__all__ = ["GoodweEv"]

logger = logging.getLogger(__name__)


class GoodweEv(ApiV2):
    """EV charger control via SEMS Plus remote endpoints."""

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

    async def get_charge_log(self) -> list[dict[str, Any]]:
        """Return the EV charge log entries."""
        data: Any = await self.call(EV_CHARGE_LOG_PATH)
        return data if isinstance(data, list) else [data]

    async def get_config(self) -> dict[str, Any]:
        """Return charger configuration."""
        data: Any = await self.call(EV_CONFIG_PATH)
        return data if isinstance(data, dict) else {}

    async def set_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Set charger configuration."""
        data: Any = await self.call(
            EV_CONFIG_PATH,
            payload=EvConfigPayload(config=config),
        )
        return data if isinstance(data, dict) else {}

    async def start_charge(self) -> dict[str, Any]:
        """Start a charging session."""
        data: Any = await self.call(EV_START_CHARGE_PATH)
        return data if isinstance(data, dict) else {}

    async def stop_charge(self) -> dict[str, Any]:
        """Stop a charging session."""
        data: Any = await self.call(EV_STOP_CHARGE_PATH)
        return data if isinstance(data, dict) else {}

    async def set_scheduled(self, schedule: dict[str, Any]) -> dict[str, Any]:
        """Set a scheduled charging window."""
        data: Any = await self.call(
            EV_SCHEDULED_CHARGE_PATH,
            payload=EvSchedulePayload(schedule=schedule),
        )
        return data if isinstance(data, dict) else {}
