"""Fixtures for Samsung Soundbar Local tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.soundbar_local.api import SoundbarState


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Load integrations from custom_components."""
    yield


@pytest.fixture
def soundbar() -> Generator[AsyncMock]:
    """A fake soundbar client, shared by setup and config flow."""
    fake = AsyncMock()
    fake.host = "192.168.2.71"
    fake.identifier.return_value = "22_AV_HW-Q990D"
    fake.state.return_value = SoundbarState(
        power=True,
        volume=8,
        muted=False,
        source="E_ARC",
        sound_mode="ADAPTIVE",
        codec="MAT_PCM",
    )
    with (
        patch("custom_components.soundbar_local.Soundbar", return_value=fake),
        patch(
            "custom_components.soundbar_local.config_flow.Soundbar", return_value=fake
        ),
    ):
        yield fake
