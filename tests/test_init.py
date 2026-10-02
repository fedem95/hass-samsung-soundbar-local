"""Tests for setup, config flow and entities."""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import AsyncMock

from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.soundbar_local.api import (
    SoundbarAuthError,
    SoundbarConnectionError,
)
from custom_components.soundbar_local.const import DOMAIN, SCAN_INTERVAL

MP = "media_player.samsung_hw_q990d"


async def _setup(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "192.168.2.71"}, unique_id="192.168.2.71"
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_flow_creates_entry(hass: HomeAssistant, soundbar: AsyncMock) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: " 192.168.2.71 "}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Samsung HW-Q990D"
    assert result["data"] == {CONF_HOST: "192.168.2.71"}


async def test_flow_errors(hass: HomeAssistant, soundbar: AsyncMock) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    soundbar.identifier.side_effect = SoundbarConnectionError("down")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.2.71"}
    )
    assert result["errors"] == {"base": "cannot_connect"}
    soundbar.identifier.side_effect = SoundbarAuthError("no token")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.2.71"}
    )
    assert result["errors"] == {"base": "invalid_auth"}
    soundbar.identifier.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.2.71"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_setup_retries_when_unreachable(
    hass: HomeAssistant, soundbar: AsyncMock
) -> None:
    soundbar.identifier.side_effect = SoundbarConnectionError("down")
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_HOST: "192.168.2.71"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_entities_and_commands(hass: HomeAssistant, soundbar: AsyncMock) -> None:
    entry = await _setup(hass)
    state = hass.states.get(MP)
    assert state.state == "on"
    assert state.attributes["volume_level"] == 0.08
    assert state.attributes["source"] == "TV (eARC)"
    assert state.attributes["sound_mode"] == "Adaptive"
    assert state.attributes["codec"] == "MAT_PCM"
    assert "TV (eARC)" in state.attributes["source_list"]

    ent_reg = er.async_get(hass)
    # Same unique ids as the original integration, so existing entities survive.
    assert ent_reg.async_get(MP).unique_id == "192.168.2.71"
    assert (
        ent_reg.async_get("button.samsung_hw_q990d_subwoofer").unique_id
        == "192.168.2.71_woofer_plus"
    )

    await hass.services.async_call(
        "media_player",
        "volume_set",
        {"entity_id": MP, "volume_level": 0.25},
        blocking=True,
    )
    soundbar.set_volume.assert_awaited_with(25)
    await hass.services.async_call(
        "media_player", "volume_up", {"entity_id": MP}, blocking=True
    )
    soundbar.set_volume.assert_awaited_with(9)
    await hass.services.async_call(
        "media_player",
        "select_source",
        {"entity_id": MP, "source": "HDMI 1"},
        blocking=True,
    )
    soundbar.select_source.assert_awaited_with("HDMI_IN1")
    await hass.services.async_call(
        "media_player",
        "select_sound_mode",
        {"entity_id": MP, "sound_mode": "Clear Voice"},
        blocking=True,
    )
    soundbar.set_sound_mode.assert_awaited_with("CLEARVOICE")
    await hass.services.async_call(
        "media_player",
        "volume_mute",
        {"entity_id": MP, "is_volume_muted": True},
        blocking=True,
    )
    soundbar.set_mute.assert_awaited_with(True)
    await hass.services.async_call(
        "media_player", "turn_off", {"entity_id": MP}, blocking=True
    )
    soundbar.set_power.assert_awaited_with(False)
    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.samsung_hw_q990d_subwoofer"},
        blocking=True,
    )
    soundbar.press_key.assert_awaited_with("WOOFER_PLUS")

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_standby_is_off_and_outage_is_unavailable(
    hass: HomeAssistant, soundbar: AsyncMock
) -> None:
    await _setup(hass)
    soundbar.state.return_value = replace(soundbar.state.return_value, power=False)
    async_fire_time_changed(hass, dt_util.utcnow() + SCAN_INTERVAL)
    await hass.async_block_till_done()
    assert hass.states.get(MP).state == "off"

    soundbar.state.side_effect = SoundbarConnectionError("down")
    async_fire_time_changed(hass, dt_util.utcnow() + SCAN_INTERVAL * 2)
    await hass.async_block_till_done()
    assert hass.states.get(MP).state == "unavailable"
