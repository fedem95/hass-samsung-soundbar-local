"""Async client for the local IP control API of 2024 Samsung soundbars.

The soundbar serves JSON-RPC 2.0 over HTTPS on port 1516 (self-signed
certificate) once "IP control" is enabled in the SmartThings app.

Observed on a HW-Q990D:
- every call except ``createAccessToken`` needs a valid ``AccessToken``;
- the ``Accept: application/json`` header is mandatory, without it the
  server answers ``400 Bad Request``;
- ``<name>Control`` methods read the value when called without it and set
  it when called with it (``volumeControl`` takes an integer, ``muteControl``
  a boolean, ``powerControl`` ``"powerOn"``/``"powerOff"``);
- a missing or expired token is answered with a bare
  ``{"code": -32700, "message": "Parse error"}`` outside the JSON-RPC
  envelope;
- the bar keeps answering in standby and reports ``"power": "powerOff"``.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any

import aiohttp

DEFAULT_PORT = 1516
DEFAULT_TIMEOUT = 8

POWER_ON = "powerOn"
POWER_OFF = "powerOff"

_PARSE_ERROR = -32700


def model_from(identifier: str | None) -> str | None:
    """``22_AV_HW-Q990D`` -> ``HW-Q990D``."""
    if not identifier:
        return None
    return identifier.rsplit("_", 1)[-1]


class SoundbarError(Exception):
    """Base error for the soundbar client."""


class SoundbarConnectionError(SoundbarError):
    """The soundbar could not be reached or answered with garbage."""


class SoundbarAuthError(SoundbarError):
    """The soundbar refused the access token (IP control disabled?)."""


class SoundbarApiError(SoundbarError):
    """The soundbar answered with a JSON-RPC error."""


@dataclass(slots=True)
class SoundbarState:
    """A snapshot of the soundbar."""

    power: bool
    volume: int
    muted: bool
    source: str | None
    sound_mode: str | None
    codec: str | None


class Soundbar:
    """Client for one soundbar."""

    def __init__(
        self,
        host: str,
        session: aiohttp.ClientSession,
        *,
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.host = host
        self._url = f"https://{host}:{port}/"
        self._session = session
        self._timeout = timeout
        self._token: str | None = None
        self._token_lock = asyncio.Lock()
        self._request_id = 0

    async def _post(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self._request_id += 1
        payload: dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": method,
            "id": self._request_id,
        }
        if params:
            payload["params"] = params
        try:
            async with asyncio.timeout(self._timeout):
                resp = await self._session.post(
                    self._url,
                    data=json.dumps(payload, separators=(",", ":")),
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                    ssl=False,
                )
                resp.raise_for_status()
                body = await resp.text()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise SoundbarConnectionError(f"{method}: {err}") from err
        try:
            data = json.loads(body)
        except ValueError as err:
            raise SoundbarConnectionError(f"{method}: invalid JSON {body!r}") from err
        if not isinstance(data, dict):
            raise SoundbarConnectionError(f"{method}: unexpected answer {data!r}")
        return data

    async def _refresh_token(self, stale: str | None) -> str:
        async with self._token_lock:
            # Another call may have refreshed it while we waited for the lock.
            if self._token is not None and self._token != stale:
                return self._token
            data = await self._post("createAccessToken", {})
            try:
                self._token = data["result"]["AccessToken"]
            except (KeyError, TypeError) as err:
                self._token = None
                raise SoundbarAuthError(
                    "no access token in the answer; is IP control enabled?"
                ) from err
            return self._token

    async def call(self, method: str, **params: Any) -> dict[str, Any]:
        """Call a method, getting a new token once if the current one is refused."""
        for attempt in range(2):
            token = self._token or await self._refresh_token(None)
            data = await self._post(method, {"AccessToken": token, **params})
            if "result" in data:
                return data["result"] or {}
            error = data.get("error", data)
            if error.get("code") != _PARSE_ERROR:
                raise SoundbarApiError(f"{method}: {error}")
            if attempt == 0:
                await self._refresh_token(token)
        raise SoundbarAuthError(f"{method}: access token refused")

    # Reads ------------------------------------------------------------

    async def identifier(self) -> str | None:
        """Model identifier, e.g. ``22_AV_HW-Q990D``."""
        return (await self.call("getIdentifier")).get("identifier")

    async def state(self) -> SoundbarState:
        """Read power, volume, mute, source, sound mode and codec."""
        power = (await self.call("powerControl")).get("power")
        volume = (await self.call("volumeControl")).get("volume", 0)
        muted = (await self.call("muteControl")).get("mute", False)
        source = (await self.call("inputSelectControl")).get("inputSource")
        sound_mode = (await self.call("soundModeControl")).get("soundMode")
        codec = (await self.call("getCodec")).get("codec")
        return SoundbarState(
            power=power == POWER_ON,
            volume=int(volume),
            muted=bool(muted),
            source=source,
            sound_mode=sound_mode,
            codec=codec or None,
        )

    # Commands ---------------------------------------------------------

    async def _command(self, method: str, **params: Any) -> None:
        result = await self.call(method, **params)
        if result.get("success") is False:
            raise SoundbarApiError(f"{method} {params} refused")

    async def set_power(self, on: bool) -> None:
        await self._command("powerControl", power=POWER_ON if on else POWER_OFF)

    async def set_volume(self, volume: int) -> None:
        await self._command("volumeControl", volume=max(0, min(100, volume)))

    async def set_mute(self, mute: bool) -> None:
        await self._command("muteControl", mute=mute)

    async def select_source(self, source: str) -> None:
        await self._command("inputSelectControl", inputSource=source)

    async def set_sound_mode(self, mode: str) -> None:
        await self._command("soundModeControl", soundMode=mode)

    async def press_key(self, key: str) -> None:
        """Send a remote key, e.g. ``VOL_UP``, ``WOOFER_PLUS``, ``MUTE``."""
        await self.call("remoteKeyControl", remoteKey=key)
