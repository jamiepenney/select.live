"""Config flow for select.live."""
from __future__ import annotations

from typing import Any

import probatio as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_DEVICE_ID, CONF_IP_ADDRESS
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CannotConnect, SelectLiveApi
from .const import DEFAULT_HOST, DEFAULT_NAME, DOMAIN


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_IP_ADDRESS, default=defaults.get(CONF_IP_ADDRESS, DEFAULT_HOST)
            ): str,
            vol.Required(CONF_DEVICE_ID, default=defaults.get(CONF_DEVICE_ID, "")): str,
        }
    )


class SelectLiveConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for select.live."""

    VERSION = 1

    async def _async_validate(self, data: dict[str, Any]) -> str | None:
        """Return an error key if the device can't be reached, else None."""
        api = SelectLiveApi(
            async_get_clientsession(self.hass), data[CONF_IP_ADDRESS], data[CONF_DEVICE_ID]
        )
        try:
            await api.async_get_data()
        except CannotConnect:
            return "cannot_connect"
        return None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle setup from the UI."""
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
            self._abort_if_unique_id_configured()
            if (error := await self._async_validate(user_input)) is None:
                return self.async_create_entry(title=DEFAULT_NAME, data=user_input)
            errors["base"] = error

        return self.async_show_form(
            step_id="user", data_schema=_schema(user_input or {}), errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Allow changing the host without removing the entry."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
            self._abort_if_unique_id_mismatch(reason="wrong_device")
            if (error := await self._async_validate(user_input)) is None:
                return self.async_update_reload_and_abort(entry, data_updates=user_input)
            errors["base"] = error

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_schema(user_input or dict(entry.data)),
            errors=errors,
        )

    async def async_step_import(self, import_data: dict[str, Any]) -> ConfigFlowResult:
        """Import an existing YAML configuration."""
        await self.async_set_unique_id(import_data[CONF_DEVICE_ID])
        self._abort_if_unique_id_configured()
        if (error := await self._async_validate(import_data)) is not None:
            return self.async_abort(reason=error)
        return self.async_create_entry(
            title=DEFAULT_NAME,
            data={
                CONF_IP_ADDRESS: import_data[CONF_IP_ADDRESS],
                CONF_DEVICE_ID: import_data[CONF_DEVICE_ID],
            },
        )
