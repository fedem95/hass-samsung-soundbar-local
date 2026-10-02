"""Polling coordinator for Samsung Soundbar Local."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import Soundbar, SoundbarError, SoundbarState
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

type SoundbarConfigEntry = ConfigEntry[SoundbarCoordinator]


class SoundbarCoordinator(DataUpdateCoordinator[SoundbarState]):
    """Read the whole soundbar state every SCAN_INTERVAL."""

    config_entry: SoundbarConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: SoundbarConfigEntry,
        soundbar: Soundbar,
        model: str | None,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {soundbar.host}",
            update_interval=SCAN_INTERVAL,
        )
        self.soundbar = soundbar
        self.model = model

    async def _async_update_data(self) -> SoundbarState:
        try:
            return await self.soundbar.state()
        except SoundbarError as err:
            raise UpdateFailed(str(err)) from err
