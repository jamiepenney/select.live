"""Sensors for Selectronic SP PRO inverters via select.live."""
from __future__ import annotations

import homeassistant.helpers.config_validation as cv
import probatio as vol
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA as SENSOR_PLATFORM_SCHEMA,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_IP_ADDRESS,
    CONF_NAME,
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.core import DOMAIN as HOMEASSISTANT_DOMAIN
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    BATTERY_IN_WH_TODAY,
    BATTERY_OUT_WH_TODAY,
    BATTERY_SOC,
    BATTERY_W,
    DEFAULT_HOST,
    DEFAULT_NAME,
    DOMAIN,
    GRID_IN_WH_TODAY,
    GRID_OUT_WH_TODAY,
    GRID_W,
    LOAD_W,
    LOAD_WH_TODAY,
    SOLARINVERTER_W,
)
from .coordinator import SelectLiveConfigEntry, SelectLiveCoordinator

# Kept only so existing YAML configs can be imported into a config entry.
PLATFORM_SCHEMA = SENSOR_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Optional(CONF_NAME, default=""): cv.string,
        vol.Optional(CONF_IP_ADDRESS, default=DEFAULT_HOST): cv.string,
    }
)


def _power(key: str) -> SensorEntityDescription:
    return SensorEntityDescription(
        key=key,
        translation_key=key,
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    )


def _energy(key: str) -> SensorEntityDescription:
    return SensorEntityDescription(
        key=key,
        translation_key=key,
        # The API names these *_wh_* but actually reports kWh.
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
    )


SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=BATTERY_SOC,
        translation_key=BATTERY_SOC,
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    _power(LOAD_W),
    _power(GRID_W),
    _power(BATTERY_W),
    _power(SOLARINVERTER_W),
    _energy(GRID_OUT_WH_TODAY),
    _energy(LOAD_WH_TODAY),
    _energy(GRID_IN_WH_TODAY),
    _energy(BATTERY_IN_WH_TODAY),
    _energy(BATTERY_OUT_WH_TODAY),
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Import YAML config into a config entry and flag the YAML for removal."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data=config
    )
    reason = result.get("reason")
    if result.get("type") == FlowResultType.ABORT and reason != "already_configured":
        ir.async_create_issue(
            hass,
            DOMAIN,
            f"deprecated_yaml_import_issue_{reason}",
            is_fixable=False,
            issue_domain=DOMAIN,
            severity=ir.IssueSeverity.WARNING,
            translation_key=f"deprecated_yaml_import_issue_{reason}",
        )
        return

    ir.async_create_issue(
        hass,
        HOMEASSISTANT_DOMAIN,
        f"deprecated_yaml_{DOMAIN}",
        is_fixable=False,
        issue_domain=DOMAIN,
        severity=ir.IssueSeverity.WARNING,
        translation_key="deprecated_yaml",
        translation_placeholders={"domain": DOMAIN, "integration_title": "select.live"},
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SelectLiveConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(SelectLiveSensor(coordinator, desc) for desc in SENSORS)


# CoordinatorEntity and Entity declare `available` differently; harmless, and
# common to every HA coordinator entity.
class SelectLiveSensor(  # pyright: ignore[reportIncompatibleVariableOverride]
    CoordinatorEntity[SelectLiveCoordinator], SensorEntity
):
    """A single value reported by the select.live device."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: SelectLiveCoordinator, description: SensorEntityDescription
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        device_id = coordinator.config_entry.data[CONF_DEVICE_ID]
        self._attr_unique_id = f"{device_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=DEFAULT_NAME,
            manufacturer="Selectronic",
            model=coordinator.data.device_name,
            configuration_url=f"http://{coordinator.config_entry.data[CONF_IP_ADDRESS]}",
        )
        self._update_value()

    def _update_value(self) -> None:
        self._attr_native_value = self.coordinator.data.items.get(
            self.entity_description.key
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_value()
        super()._handle_coordinator_update()
