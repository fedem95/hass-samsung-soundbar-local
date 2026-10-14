"""Volume number for Samsung Soundbar Local."""

from __future__ import annotations

from dataclasses import replace

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import SoundbarError
from .coordinator import SoundbarConfigEntry, SoundbarCoordinator
from .entity import SoundbarEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SoundbarConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the volume number."""
    async_add_entities([SoundbarVolume(entry.runtime_data)])


class SoundbarVolume(SoundbarEntity, NumberEntity):
    """The bar volume, readable and settable in standby too.

    Home Assistant hides a media player's volume while it is off, but the bar
    keeps reporting and accepting it in standby.
    """

    _attr_translation_key = "volume"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: SoundbarCoordinator) -> None:
        super().__init__(coordinator, "volume")

    @property
    def native_value(self) -> int:
        return self.coordinator.data.volume

    async def async_set_native_value(self, value: float) -> None:
        level = round(value)
        try:
            await self.coordinator.soundbar.set_volume(level)
        except SoundbarError as err:
            raise HomeAssistantError(f"Soundbar command failed: {err}") from err
        self.coordinator.async_set_updated_data(
            replace(self.coordinator.data, volume=level)
        )
        await self.coordinator.async_request_refresh()
