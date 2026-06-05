"""Binary sensors for KinCony KC868 MQTT Controller."""
from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_MAPPING, DOMAIN
from .entity import KinConyEntity
from .helpers import value_from_state


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    mapping = entry.data.get(CONF_MAPPING, {})
    entities = []
    for channel, cfg in mapping.get("inputs", {}).items():
        if cfg.get("enabled") and cfg.get("type") == "binary_sensor":
            entities.append(KinConyBinarySensor(coordinator, channel, cfg))
    async_add_entities(entities)


class KinConyBinarySensor(KinConyEntity, BinarySensorEntity):
    """KinCony binary sensor entity."""

    def __init__(self, coordinator, channel: str, cfg: dict[str, Any]) -> None:
        super().__init__(coordinator, channel, cfg)
        device_class = cfg.get("device_class")
        if device_class and device_class != "none":
            self._attr_device_class = device_class

    @property
    def is_on(self) -> bool | None:
        value = value_from_state(self.coordinator.data, self.channel)
        if value is None:
            return None
        state = bool(value)
        if self.cfg.get("invert"):
            state = not state
        return state
