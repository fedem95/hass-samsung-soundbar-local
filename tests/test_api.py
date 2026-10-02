"""Tests for the soundbar client, against a fake HTTP session."""

from __future__ import annotations

import json
from typing import Any

import aiohttp
import pytest

from custom_components.soundbar_local.api import (
    Soundbar,
    SoundbarApiError,
    SoundbarAuthError,
    SoundbarConnectionError,
    model_from,
)


class FakeResponse:
    def __init__(self, body: Any) -> None:
        self._body = body if isinstance(body, str) else json.dumps(body)

    def raise_for_status(self) -> None:
        return None

    async def text(self) -> str:
        return self._body


class FakeBar:
    """Mimics the HW-Q990D answers seen on the real device."""

    def __init__(self) -> None:
        self.valid_tokens = {"t1"}
        self.next_token = iter(["t1", "t2", "t3"])
        self.volume = 8
        self.calls: list[dict[str, Any]] = []
        self.down = False

    async def post(
        self, url: str, *, data: str, headers: dict, ssl: bool
    ) -> FakeResponse:
        if self.down:
            raise aiohttp.ClientConnectionError("unreachable")
        assert headers["Accept"] == "application/json"
        req = json.loads(data)
        self.calls.append(req)
        method, params = req["method"], req.get("params", {})
        if method == "createAccessToken":
            token = next(self.next_token)
            self.valid_tokens.add(token)
            return FakeResponse(
                {"jsonrpc": "2.0", "id": "1", "result": {"AccessToken": token}}
            )
        if params.get("AccessToken") not in self.valid_tokens:
            return FakeResponse({"code": -32700, "message": "Parse error"})
        if method == "volumeControl":
            if "volume" in params:
                self.volume = params["volume"]
                return FakeResponse(
                    {"jsonrpc": "2.0", "id": "1", "result": {"success": True}}
                )
            return FakeResponse(
                {"jsonrpc": "2.0", "id": "1", "result": {"volume": str(self.volume)}}
            )
        results = {
            "powerControl": {"power": "powerOff"},
            "muteControl": {"mute": False},
            "inputSelectControl": {"inputSource": "E_ARC"},
            "soundModeControl": {"soundMode": "ADAPTIVE"},
            "getCodec": {"codec": "MAT_PCM"},
            "getIdentifier": {"identifier": "22_AV_HW-Q990D"},
        }
        if method in results:
            return FakeResponse(
                {"jsonrpc": "2.0", "id": "1", "result": results[method]}
            )
        return FakeResponse(
            {
                "jsonrpc": "2.0",
                "id": "1",
                "error": {"code": -32601, "message": "Method not found"},
            }
        )


async def test_state_reads_standby() -> None:
    bar = FakeBar()
    state = await Soundbar("bar", bar).state()  # type: ignore[arg-type]
    assert state.power is False
    assert state.volume == 8
    assert state.source == "E_ARC"


async def test_expired_token_is_renewed_once() -> None:
    bar = FakeBar()
    client = Soundbar("bar", bar)  # type: ignore[arg-type]
    await client.identifier()
    bar.valid_tokens = set()  # the bar forgets every token, e.g. after a reboot
    assert await client.identifier() == "22_AV_HW-Q990D"
    assert [c["method"] for c in bar.calls].count("createAccessToken") == 2


async def test_token_always_refused() -> None:
    bar = FakeBar()
    client = Soundbar("bar", bar)  # type: ignore[arg-type]
    await client.identifier()
    bar.valid_tokens = set()
    bar.next_token = iter(["x1", "x2"])
    original = bar.post

    async def forget(*args: Any, **kwargs: Any) -> FakeResponse:
        resp = await original(*args, **kwargs)
        bar.valid_tokens = set()
        return resp

    bar.post = forget  # type: ignore[method-assign]
    with pytest.raises(SoundbarAuthError):
        await client.identifier()


async def test_set_volume_is_direct_and_clamped() -> None:
    bar = FakeBar()
    client = Soundbar("bar", bar)  # type: ignore[arg-type]
    await client.set_volume(130)
    assert bar.volume == 100
    sets = [c for c in bar.calls if c["method"] == "volumeControl"]
    assert len(sets) == 1


async def test_unknown_method() -> None:
    with pytest.raises(SoundbarApiError):
        await Soundbar("bar", FakeBar()).call("nope")  # type: ignore[arg-type]


async def test_unreachable() -> None:
    bar = FakeBar()
    bar.down = True
    with pytest.raises(SoundbarConnectionError):
        await Soundbar("bar", bar).state()  # type: ignore[arg-type]


def test_model_from() -> None:
    assert model_from("22_AV_HW-Q990D") == "HW-Q990D"
    assert model_from(None) is None
