"""Payload dataclasses for the GoodWe SEMS Plus API."""

from __future__ import annotations

import dataclasses
from dataclasses import asdict, dataclass
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Serializable(Protocol):
    """Anything that can be reduced to a JSON-friendly dict."""

    def to_dict(self) -> dict[str, Any]: ...


def _to_dict(value: object) -> dict[str, Any]:
    """Serialize a dataclass (or dict-like) to a plain dict."""
    if isinstance(value, Serializable):
        return value.to_dict()
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    raise TypeError(f"Cannot serialize payload of type {type(value)!r}")


@dataclass
class LoginRequest:
    """Payload for /auth/cross-login."""

    account: str
    pwd: str

    def to_dict(self) -> dict[str, Any]:
        return {"account": self.account, "pwd": self.pwd}


@dataclass
class IdRequest:
    """Payload wrapping a single ID (e.g. export job ID)."""

    id: str

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id}


@dataclass
class DatepwIdRequest:
    """Payload with a date string and a powerstation ID."""

    date: str
    pw_id: str

    def to_dict(self) -> dict[str, Any]:
        return {"date": self.date, "pw_id": self.pw_id}


@dataclass
class MonthReportRequest:
    """Payload for the monthly power report endpoint."""

    date: str
    pw_id: str
    page_index: int = 1
    page_size: int = 8
    is_report: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "pw_id": self.pw_id,
            "page_index": self.page_index,
            "page_size": self.page_size,
            "is_report": self.is_report,
        }


@dataclass
class PagedRequest:
    """Generic paginated list request."""

    page_index: int = 1
    page_size: int = 20

    def to_dict(self) -> dict[str, Any]:
        return {"page_index": self.page_index, "page_size": self.page_size}


@dataclass
class StationListRequest(PagedRequest):
    """Payload for listing stations."""

    pass


@dataclass
class AreaCodeRequest:
    """Payload for setting a station's area code."""

    area_code: str

    def to_dict(self) -> dict[str, Any]:
        return {"area_code": self.area_code}


@dataclass
class TimezoneRequest:
    """Payload for setting a station's timezone."""

    timezone: str

    def to_dict(self) -> dict[str, Any]:
        return {"timezone": self.timezone}


@dataclass
class StationCollectRequest:
    """Payload for collecting/un-collecting a station."""

    collect: bool

    def to_dict(self) -> dict[str, Any]:
        return {"collect": self.collect}


@dataclass
class ElecSourceSettingRequest:
    """Payload for setting a station's electricity source setting."""

    setting: int

    def to_dict(self) -> dict[str, Any]:
        return {"setting": self.setting}


@dataclass
class SnRequest:
    """Payload with a serial number."""

    sn: str

    def to_dict(self) -> dict[str, Any]:
        return {"sn": self.sn}


@dataclass
class PowerstationIdRequest:
    """Payload with a powerstation ID."""

    powerstation_id: str

    def to_dict(self) -> dict[str, Any]:
        return {"powerstation_id": self.powerstation_id}


@dataclass
class EvConfigPayload:
    """EV charger configuration payload (free-form, structure TBD)."""

    config: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"config": self.config}


@dataclass
class EvSchedulePayload:
    """EV charger schedule payload (free-form, structure TBD)."""

    schedule: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"schedule": self.schedule}
