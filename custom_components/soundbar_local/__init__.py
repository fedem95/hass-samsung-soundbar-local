"""Samsung Soundbar Local: control 2024 Samsung soundbars over the LAN."""

from __future__ import annotations

from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import Soundbar, SoundbarError, model_from
from .coordinator import SoundbarConfigEntry, SoundbarCoordinator

PLATFORMS = [Platform.BUTTON, Platform.MEDIA_PLAYER]


async def async_setup_entry(hass: HomeAssistant, entry: SoundbarConfigEntry) -> bool:
    """Set up a soundbar from a config entry."""
    soundbar = Soundbar(
        entry.data[CONF_HOST], async_get_clientsession(hass, verify_ssl=False)
    )
    try:
        identifier = await soundbar.identifier()
    except SoundbarError as err:
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = SoundbarCoordinator(hass, entry, soundbar, model_from(identifier))
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SoundbarConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
