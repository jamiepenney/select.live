"""The select.live integration."""
from __future__ import annotations

from homeassistant.const import CONF_DEVICE_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, LEGACY_UNIQUE_IDS
from .coordinator import SelectLiveConfigEntry, SelectLiveCoordinator

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: SelectLiveConfigEntry) -> bool:
    """Set up select.live from a config entry."""
    _migrate_legacy_unique_ids(hass, entry)

    coordinator = SelectLiveCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SelectLiveConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


def _migrate_legacy_unique_ids(hass: HomeAssistant, entry: SelectLiveConfigEntry) -> None:
    """Rename unique IDs from the YAML version so entities keep their history.

    If a new-style entity was already created alongside the legacy one (e.g. by
    an earlier release whose migration didn't match), the new entity is removed
    so the legacy entity, which owns the long-term history, takes its place.
    """
    ent_reg = er.async_get(hass)
    device_id = entry.data[CONF_DEVICE_ID]
    for key, legacy_id in LEGACY_UNIQUE_IDS.items():
        legacy_entity_id = ent_reg.async_get_entity_id(Platform.SENSOR, DOMAIN, legacy_id)
        if legacy_entity_id is None:
            continue
        new_id = f"{device_id}_{key}"
        if duplicate := ent_reg.async_get_entity_id(Platform.SENSOR, DOMAIN, new_id):
            ent_reg.async_remove(duplicate)
        ent_reg.async_update_entity(legacy_entity_id, new_unique_id=new_id)
