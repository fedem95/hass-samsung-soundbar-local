"""Base entity for Samsung Soundbar Local."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SoundbarCoordinator


class SoundbarEntity(CoordinatorEntity[SoundbarCoordinator]):
    """Common device info for every entity of one soundbar."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SoundbarCoordinator, key: str | None) -> None:
        super().__init__(coordinator)
        host = coordinator.soundbar.host
        # The first release used the bare host as the media player unique id:
        # keep it so existing entities survive the update.
        self._attr_unique_id = host if key is None else f"{host}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, host)},
            manufacturer="Samsung",
            model=coordinator.model,
            name=f"Samsung {coordinator.model or 'Soundbar'}",
        )
