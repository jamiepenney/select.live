"""Data update coordinator for select.live."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID, CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SelectLiveApi, SelectLiveData, SelectLiveError
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

type SelectLiveConfigEntry = ConfigEntry[SelectLiveCoordinator]


class SelectLiveCoordinator(DataUpdateCoordinator[SelectLiveData]):
    """Polls the device once per interval and shares the result with all sensors."""

    config_entry: SelectLiveConfigEntry

    def __init__(self, hass: HomeAssistant, entry: SelectLiveConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.api = SelectLiveApi(
            async_get_clientsession(hass),
            entry.data[CONF_IP_ADDRESS],
            entry.data[CONF_DEVICE_ID],
        )

    async def _async_update_data(self) -> SelectLiveData:
        try:
            return await self.api.async_get_data()
        except SelectLiveError as err:
            raise UpdateFailed(str(err)) from err
