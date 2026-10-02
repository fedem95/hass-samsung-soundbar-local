"""Subwoofer buttons for Samsung Soundbar Local."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import SoundbarError
from .coordinator import SoundbarConfigEntry, SoundbarCoordinator
from .entity import SoundbarEntity

# translation key / unique id suffix -> remote key
_BUTTONS = {
    "woofer_plus": "WOOFER_PLUS",
    "woofer_minus": "WOOFER_MINUS",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SoundbarConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the subwoofer buttons."""
    async_add_entities(
        SoundbarKeyButton(entry.runtime_data, key, remote_key)
        for key, remote_key in _BUTTONS.items()
    )


class SoundbarKeyButton(SoundbarEntity, ButtonEntity):
    """A button that sends one key of the soundbar remote."""

    def __init__(
        self, coordinator: SoundbarCoordinator, key: str, remote_key: str
    ) -> None:
        super().__init__(coordinator, key)
        self._attr_translation_key = key
        self._remote_key = remote_key

    async def async_press(self) -> None:
        try:
            await self.coordinator.soundbar.press_key(self._remote_key)
        except SoundbarError as err:
            raise HomeAssistantError(f"Soundbar command failed: {err}") from err
