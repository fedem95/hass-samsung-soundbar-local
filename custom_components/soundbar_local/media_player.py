"""Media player entity for Samsung Soundbar Local."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import replace
from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import SoundbarError
from .const import SOUND_MODES, SOURCES
from .coordinator import SoundbarConfigEntry, SoundbarCoordinator
from .entity import SoundbarEntity

_SOURCE_CODES = {name: code for code, name in SOURCES.items()}
_SOUND_MODE_CODES = {name: code for code, name in SOUND_MODES.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SoundbarConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the soundbar media player."""
    async_add_entities([SoundbarMediaPlayer(entry.runtime_data)])


class SoundbarMediaPlayer(SoundbarEntity, MediaPlayerEntity):
    """The soundbar as a media player: power, volume, input, sound mode."""

    _attr_name = None
    _attr_device_class = MediaPlayerDeviceClass.SPEAKER
    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.SELECT_SOURCE
        | MediaPlayerEntityFeature.SELECT_SOUND_MODE
    )
    _attr_source_list = list(SOURCES.values())
    _attr_sound_mode_list = list(SOUND_MODES.values())
    # One step of the physical remote.
    _attr_volume_step = 0.01

    def __init__(self, coordinator: SoundbarCoordinator) -> None:
        super().__init__(coordinator, None)

    @property
    def state(self) -> MediaPlayerState:
        return (
            MediaPlayerState.ON if self.coordinator.data.power else MediaPlayerState.OFF
        )

    @property
    def volume_level(self) -> float:
        return self.coordinator.data.volume / 100

    @property
    def is_volume_muted(self) -> bool:
        return self.coordinator.data.muted

    @property
    def source(self) -> str | None:
        code = self.coordinator.data.source
        return SOURCES.get(code, code) if code else None

    @property
    def sound_mode(self) -> str | None:
        code = self.coordinator.data.sound_mode
        return SOUND_MODES.get(code, code) if code else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"codec": self.coordinator.data.codec}

    async def _run(
        self, command: Callable[[], Awaitable[None]], **changes: Any
    ) -> None:
        """Send a command, show the expected state at once, then re-read the bar."""
        try:
            await command()
        except SoundbarError as err:
            raise HomeAssistantError(f"Soundbar command failed: {err}") from err
        if changes:
            self.coordinator.async_set_updated_data(
                replace(self.coordinator.data, **changes)
            )
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self) -> None:
        await self._run(lambda: self.coordinator.soundbar.set_power(True), power=True)

    async def async_turn_off(self) -> None:
        await self._run(lambda: self.coordinator.soundbar.set_power(False), power=False)

    async def async_set_volume_level(self, volume: float) -> None:
        level = round(volume * 100)
        await self._run(
            lambda: self.coordinator.soundbar.set_volume(level), volume=level
        )

    async def async_mute_volume(self, mute: bool) -> None:
        await self._run(lambda: self.coordinator.soundbar.set_mute(mute), muted=mute)

    async def async_select_source(self, source: str) -> None:
        code = _SOURCE_CODES.get(source, source)
        await self._run(
            lambda: self.coordinator.soundbar.select_source(code), source=code
        )

    async def async_select_sound_mode(self, sound_mode: str) -> None:
        code = _SOUND_MODE_CODES.get(sound_mode, sound_mode)
        await self._run(
            lambda: self.coordinator.soundbar.set_sound_mode(code), sound_mode=code
        )
