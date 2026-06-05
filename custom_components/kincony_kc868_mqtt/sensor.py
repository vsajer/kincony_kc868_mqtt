"""Sensors for KinCony KC868 MQTT Controller."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.util import dt as dt_util

from .const import CONF_MAPPING, DOMAIN
from .entity import KinConyEntity
from .helpers import sensor_value_from_state


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    mapping = entry.data.get(CONF_MAPPING, {})
    entities = [KinConyLastSeenSensor(coordinator, "last_seen", {"name": "Last seen"})]
    for channel, cfg in mapping.get("sensors", {}).items():
        if cfg.get("enabled") and cfg.get("type") == "sensor":
            entities.append(KinConySensor(coordinator, channel, cfg))
    async_add_entities(entities)


class KinConySensor(KinConyEntity, SensorEntity):
    """KinCony generic sensor."""

    def __init__(self, coordinator, channel: str, cfg: dict[str, Any]) -> None:
        super().__init__(coordinator, channel, cfg)
        unit = cfg.get("unit") or None
        if unit:
            self._attr_native_unit_of_measurement = unit
        device_class = cfg.get("device_class")
        if device_class and device_class != "none":
            self._attr_device_class = device_class
        state_class = cfg.get("state_class")
        if state_class and state_class != "none":
            self._attr_state_class = state_class

    @property
    def native_value(self) -> Any:
        return sensor_value_from_state(self.coordinator.data, self.channel, self.cfg)


class KinConyLastSeenSensor(KinConyEntity, SensorEntity):
    """Diagnostic last-seen sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self) -> Any:
        return self.coordinator.last_seen
