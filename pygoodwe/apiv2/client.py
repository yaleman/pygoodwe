"""Async GoodWe SEMS Plus client implementation."""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Generic, Optional, TypeVar, Union

import httpx
from typing_extensions import Self

from . import constants as cfg
from .constants import DEFAULT_REGION, DEFAULT_TIMEOUT, SEMSPLUS_REGIONS
from .exceptions import (
    ApiError,
    AuthError,
    GoodweError,
    NetworkError,
    RegionError,
    TokenExpiredError,
)
from .payloads import (
    LoginRequest,
    Serializable,
)

__all__ = ["ApiV2", "TokenSigner"]

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(frozen=True)
class _Envelope(Generic[T]):
    """Response envelope wrapping all SEMS Plus API responses."""

    code: int
    msg: str = ""
    data: Optional[T] = None

    def check(self) -> T:
        """Return the inner data on success, otherwise raise."""
        if self.code != 0 or self.data is None:
            raise ApiError(self.code, self.msg)
        return self.data


TokenSigner = Callable[[str], Union[str, Awaitable[str]]]


def _stub_sign_token(token_json: str) -> str:
    """Placeholder HMAC implementation.

    The real signing key is buried in the minified front-end bundle
    (function ``b2`` in ``index.528074a0.py``); replace with the real
    implementation once extracted. The server may or may not enforce
    signatures for all endpoints.
    """
    return hashlib.sha256(token_json.encode()).hexdigest()


def _to_json_serializable(value: Any) -> Any:
    """Recursively convert payloads and envelopes to plain dicts."""
    if isinstance(value, Serializable):
        return _to_json_serializable(value.to_dict())
    if isinstance(value, dict):
        return {k: _to_json_serializable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_json_serializable(item) for item in value]
    return value


def _parse_envelope(response: httpx.Response) -> _Envelope[Any]:
    """Parse the response and return the checked envelope."""
    try:
        raw = response.json()
    except ValueError as exc:
        raise ApiError(-1, f"Malformed JSON response: {exc}") from exc

    if not isinstance(raw, dict):
        raise ApiError(-1, f"Expected object, got {type(raw).__name__}")

    code_val = raw.get("code", -1)
    if isinstance(code_val, str):
        result_code = -1 if code_val != "0" else 0
    else:
        result_code = int(code_val)

    return _Envelope(code=result_code, msg=str(raw.get("msg", "")), data=raw.get("data"))


class ApiV2:
    """Base async client for the GoodWe SEMS Plus API.

    Shared transport, authentication, region resolution, and envelope
    handling for all subclasses.
    """

    def __init__(
        self,
        account: str,
        password: str,
        region: str = DEFAULT_REGION,
        token: Optional[str] = None,
        user_agent: Optional[str] = None,
        sign_token: Optional[TokenSigner] = None,
        http: Optional[httpx.AsyncClient] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.account = account
        self.password = password
        self._explicit_base_url: Optional[str] = None
        if region not in SEMSPLUS_REGIONS and region != "auto":
            raise RegionError(f"Unknown region {region!r}")
        self.region = region
        self._resolved_region: Optional[str] = None
        if region != "auto":
            self._resolved_region = region

        self.token = token
        self.user_agent = user_agent or ""
        self._sign_token: TokenSigner = sign_token or _stub_sign_token
        self._external_client = http is not None
        self._http = http
        self.timeout = timeout

        if region != "auto":
            self._base_url = SEMSPLUS_REGIONS[region]

    @property
    def base_url(self) -> str:
        if self._resolved_region is not None:
            return SEMSPLUS_REGIONS[self._resolved_region]
        if self._explicit_base_url:
            return self._explicit_base_url
        return SEMSPLUS_REGIONS[DEFAULT_REGION]

    @property
    def mqtt_url(self) -> Optional[str]:
        """Return the MQTT URL for the configured region, if known."""
        return cfg.MQTT_URLS.get(self._resolved_region or self.region)

    def _build_headers(self) -> dict[str, str]:
        auth = {
            "uid": "",
            "timestamp": 0,
            "token": self.token or "",
            "client": "semsPlusWeb",
            "version": "",
            "language": "en",
        }
        token_json = json.dumps(auth)

        # Allow both sync and async signers.
        sig = self._sign_token(token_json)
        if hasattr(sig, "__await__"):
            raise RuntimeError(
                "Async sign_token must not be called synchronously — "
                "use async_build_headers instead."
            )

        return {
            "User-Agent": self.user_agent,
            "Token": token_json,
            "X-Signature": str(sig),
        }

    async def _async_build_headers(self) -> dict[str, str]:
        """Same as _build_headers but awaits async signers."""
        auth = {
            "uid": "",
            "timestamp": 0,
            "token": self.token or "",
            "client": "semsPlusWeb",
            "version": "",
            "language": "en",
        }
        token_json = json.dumps(auth)
        sig = self._sign_token(token_json)
        if isinstance(sig, Awaitable):
            sig = await sig
        return {
            "User-Agent": self.user_agent,
            "Token": token_json,
            "X-Signature": str(sig),
        }

    def _envelope(self, raw: dict[str, Any]) -> Any:
        """Unwrap and validate an API response envelope."""
        payload = _Envelope(
            code=int(raw.get("code", -1)),
            msg=str(raw.get("msg", "")),
            data=raw.get("data"),
        )
        return payload.check()

    async def _resolve_region_if_needed(self) -> None:
        """Auto-resolve the region from /auth/default-service once."""
        if self._resolved_region is not None:
            return
        if self.region != "auto":
            self._resolved_region = self.region
            return

        client = self._ensure_client()
        try:
            response = await client.get(
                cfg.AUTH_DEFAULT_SERVICE_PATH,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise NetworkError(f"Failed to resolve region: {exc}") from exc

        if int(data.get("code", -1)) != 0:
            raise RegionError(f"default-service returned error: {data.get('msg', '')}")

        resolved = data.get("data", {}).get("region") or data.get("region")
        if not resolved or resolved not in SEMSPLUS_REGIONS:
            raise RegionError(f"default-service returned unknown region {resolved!r}")

        self._resolved_region = resolved
        logger.debug("Resolved SEMS Plus region to %s", resolved)

    def _ensure_client(self) -> httpx.AsyncClient:
        """Return the internal HTTP client, raising if we're closed."""
        if self._http is None:
            raise GoodweError("ApiV2 has no active HTTP client (was close() called?)")
        return self._http

    async def _request(
        self,
        method: str,
        path: str,
        *,
        payload: Optional[Any] = None,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> httpx.Response:
        """Make an HTTP request to the SEMS Plus backend."""
        await self._resolve_region_if_needed()
        client = self._ensure_client()

        url = f"{self.base_url}{path}"
        request_headers = await self._async_build_headers()
        if headers:
            request_headers.update(headers)

        json_body = None
        if payload is not None:
            json_body = _to_json_serializable(payload)

        try:
            response = await client.request(
                method,
                url,
                headers=request_headers,
                json=json_body,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response
        except httpx.TimeoutException as exc:
            raise NetworkError(f"Request to {method} {path} timed out") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                return exc.response
            raise NetworkError(
                f"HTTP {exc.response.status_code} on {method} {path}: {exc.response.text[:200]}"
            ) from exc
        except httpx.HTTPError as exc:
            raise NetworkError(f"Request to {method} {path} failed: {exc}") from exc

    async def handle_401(self, response: httpx.Response) -> bool:
        """Attempt to recover from a 401 response by re-logging in. Returns True on success."""
        if self.token is not None:
            logger.warning("Token present but got 401 — forcing re-login")
        self.token = None
        try:
            if await self.do_login():
                return True
        except GoodweError:
            pass
        raise TokenExpiredError("Authentication failed and re-login was unsuccessful")

    async def call(
        self,
        path: str,
        *,
        payload: Optional[Any] = None,
        params: Optional[dict[str, Any]] = None,
        max_tries: int = 3,
    ) -> Any:
        """Make an API call, handling envelope, auth refresh, and retries."""
        for attempt in range(1, max_tries + 1):
            response = await self._request("POST", path, payload=payload, params=params)

            if response.status_code == 401:
                try:
                    if await self.handle_401(response):
                        continue
                except TokenExpiredError:
                    raise
                continue

            try:
                raw = response.json()
            except ValueError as exc:
                raise ApiError(-1, f"Malformed response: {exc}") from exc

            if not isinstance(raw, dict):
                raise ApiError(-1, f"Expected response dict, got {type(raw).__name__}")

            code_val = raw.get("code", -1)
            if isinstance(code_val, str):
                # String codes like 'C0602' from the new API
                result_code = -1 if code_val != "0" else 0
            else:
                result_code = int(code_val)

            result = _Envelope(
                code=result_code,
                msg=str(raw.get("msg", "")),
                data=raw.get("data"),
            )

            if result.code == 0:
                return result.data

            if result.code in (401, 100002) and attempt < max_tries:
                try:
                    if await self.handle_401(response):
                        continue
                except TokenExpiredError:
                    raise

            raise ApiError(result.code, result.msg)

        raise ApiError(-1, f"Exceeded retries ({max_tries})")

    async def do_login(self) -> bool:
        """POST /auth/cross-login and store the resulting token."""
        response = await self._request(
            "POST",
            cfg.AUTH_LOGIN_PATH,
            payload=LoginRequest(account=self.account, pwd=self.password),
        )

        if response.status_code >= 400:
            raise AuthError(f"Login failed with HTTP {response.status_code}")

        try:
            raw = response.json()
        except ValueError as exc:
            raise AuthError(f"Malformed login response: {exc}") from exc

        code_val = raw.get("code")
        if code_val is None:
            raise AuthError("Login response missing code")
        if isinstance(code_val, str):
            if code_val != "0":
                raise AuthError(f"Login failed: {raw.get('msg', '')}")
        elif int(code_val) != 0:
            raise AuthError(f"Login failed: {raw.get('msg', '')}")

        data = raw.get("data") or {}
        new_token = data.get("token")
        if not new_token:
            raise AuthError("Login response missing token")

        self.token = new_token
        logger.debug("Login successful for account %s", self.account)
        return True

    async def close(self) -> None:
        """Close the internal HTTP client (only if we own it)."""
        if self._http is not None and not self._external_client:
            await self._http.aclose()
            self._http = None

    async def __aenter__(self) -> Self:
        if self._http is None:
            self._http = httpx.AsyncClient()
            self._external_client = False
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()
