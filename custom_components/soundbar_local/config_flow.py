"""Config flow for Samsung Soundbar Local."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import Soundbar, SoundbarAuthError, SoundbarError, model_from
from .const import CONF_HDMI1_NAME, CONF_HDMI2_NAME, CONF_SOURCES, DOMAIN, SOURCES


class SoundbarLocalConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ask for the soundbar address and check that it answers."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> SoundbarOptionsFlow:
        return SoundbarOptionsFlow()

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


class SoundbarOptionsFlow(OptionsFlow):
    """Choose the inputs offered and name the HDMI inputs."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SOURCES, default=options.get(CONF_SOURCES, list(SOURCES))
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value=code, label=name)
                            for code, name in SOURCES.items()
                        ],
                        multiple=True,
                        mode=SelectSelectorMode.LIST,
                    )
                ),
                vol.Optional(
                    CONF_HDMI1_NAME,
                    description={"suggested_value": options.get(CONF_HDMI1_NAME)},
                ): str,
                vol.Optional(
                    CONF_HDMI2_NAME,
                    description={"suggested_value": options.get(CONF_HDMI2_NAME)},
                ): str,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
