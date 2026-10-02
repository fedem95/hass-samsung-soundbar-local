"""Config flow for Samsung Soundbar Local."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import Soundbar, SoundbarAuthError, SoundbarError, model_from
from .const import DOMAIN


class SoundbarLocalConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ask for the soundbar address and check that it answers."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()
            soundbar = Soundbar(
                host, async_get_clientsession(self.hass, verify_ssl=False)
            )
            try:
                identifier = await soundbar.identifier()
            except SoundbarAuthError:
                errors["base"] = "invalid_auth"
            except SoundbarError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"Samsung {model_from(identifier) or 'Soundbar'}",
                    data={CONF_HOST: host},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
            errors=errors,
        )
