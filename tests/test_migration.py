"""Tests for migrating entities from the YAML-only version."""
from unittest.mock import AsyncMock

from homeassistant.const import CONF_DEVICE_ID, CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.select_live.const import DOMAIN

from .conftest import DEVICE_ID

# Copied from a real registry, not from const.py, so a "tidied" constant fails here.
LEGACY_SOC_ID = "selectronic _battery _state of _charge"
NEW_SOC_ID = f"{DEVICE_ID}_battery_soc"


def _add_entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DEVICE_ID,
        data={CONF_IP_ADDRESS: "selectronic", CONF_DEVICE_ID: DEVICE_ID},
    )
    entry.add_to_hass(hass)
    return entry


def _add_legacy(entity_registry: er.EntityRegistry) -> er.RegistryEntry:
    return entity_registry.async_get_or_create(
        "sensor", DOMAIN, LEGACY_SOC_ID,
        suggested_object_id="selectronic_battery_state_of_charge",
    )


async def test_legacy_entity_is_adopted(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, mock_api: AsyncMock
) -> None:
    """An orphaned YAML entity keeps its entity_id after setup."""
    old = _add_legacy(entity_registry)
    entry = _add_entry(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entity_registry.async_get_entity_id("sensor", DOMAIN, NEW_SOC_ID) == old.entity_id
    assert entity_registry.async_get_entity_id("sensor", DOMAIN, LEGACY_SOC_ID) is None
    assert entity_registry.async_get(old.entity_id).config_entry_id == entry.entry_id
    assert hass.states.get(old.entity_id).state == "99.9"


async def test_duplicate_new_entity_is_replaced_by_legacy(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, mock_api: AsyncMock
) -> None:
    """If a failed migration left both entities, the legacy one wins."""
    old = _add_legacy(entity_registry)
    entry = _add_entry(hass)
    dup = entity_registry.async_get_or_create(
        "sensor", DOMAIN, NEW_SOC_ID, config_entry=entry,
        suggested_object_id="selectronic_battery_state_of_charge_2",
    )

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entity_registry.async_get(dup.entity_id) is None
    assert entity_registry.async_get_entity_id("sensor", DOMAIN, NEW_SOC_ID) == old.entity_id
    assert hass.states.get(old.entity_id).state == "99.9"


async def test_fresh_install_creates_entities(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, mock_api: AsyncMock
) -> None:
    """With nothing to migrate, all ten sensors are created."""
    entry = _add_entry(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    assert len(entities) == 10
