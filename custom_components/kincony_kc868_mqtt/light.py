"""Lights for KinCony KC868 MQTT Controller."""
from __future__ import annotations

from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
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
    for channel, cfg in mapping.get("outputs", {}).items():
        if cfg.get("enabled") and cfg.get("type") == "light":
            entities.append(KinConyLight(coordinator, channel, cfg))
    async_add_entities(entities)


class KinConyLight(KinConyEntity, LightEntity):
    """KinCony output as light."""

    _attr_supported_color_modes = {ColorMode.ONOFF}
    _attr_color_mode = ColorMode.ONOFF

    @property
    def is_on(self) -> bool | None:
        value = value_from_state(self.coordinator.data, self.channel)
        if value is None:
            return None
        state = bool(value)
        if self.cfg.get("invert"):
            state = not state
        return state

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_publish_output(self.channel, not bool(self.cfg.get("invert")))

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_publish_output(self.channel, bool(self.cfg.get("invert")))
