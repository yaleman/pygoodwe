"""pygoodwe.apiv2 — async GoodWe SEMS Plus client.

Quickstart::

    import asyncio
    from pygoodwe.apiv2 import GoodweInverter

    async def main():
        async with GoodweInverter("user", "pass", station_id="...") as inv:
            await inv.do_login()
            data = await inv.get_current_readings()
            print(data)

    asyncio.run(main())
"""

from .client import ApiV2
from .ev import GoodweEv
from .exceptions import (
    ApiError,
    AuthError,
    GoodweError,
    NetworkError,
    RegionError,
    TokenExpiredError,
)
from .inverters import GoodweInverter, GoodweInverters
from .plant import GoodwePlant

__all__ = [
    "ApiV2",
    "ApiError",
    "AuthError",
    "GoodweEv",
    "GoodweError",
    "GoodweInverter",
    "GoodweInverters",
    "GoodwePlant",
    "NetworkError",
    "RegionError",
    "TokenExpiredError",
]
