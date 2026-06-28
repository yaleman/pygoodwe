"""Typed exceptions for the GoodWe SEMS Plus async client."""

from __future__ import annotations

from typing import Any, Optional


class GoodweError(Exception):
    """Base class for all apiv2 errors."""


class AuthError(GoodweError):
    """Raised when login fails (bad credentials)."""


class TokenExpiredError(GoodweError):
    """Raised when the session token is expired and re-login failed."""


class ApiError(GoodweError):
    """Raised when the API returns a non-zero error code."""

    def __init__(self, code: int, message: str, *, raw: Optional[Any] = None) -> None:
        super().__init__(f"GoodWe API error {code}: {message}")
        self.code = code
        self.message = message
        self.raw = raw


class NetworkError(GoodweError):
    """Raised on transport-layer failure (timeout, DNS, connection)."""


class RegionError(GoodweError):
    """Raised when the region cannot be resolved."""
