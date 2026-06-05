"""Buttons for KinCony KC868 MQTT Controller."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_MAPPING, DEFAULT_PULSE_SECONDS, DOMAIN
from .entity import KinConyEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    mapping = entry.data.get(CONF_MAPPING, {})
    entities = []
    for channel, cfg in mapping.get("outputs", {}).items():
        if cfg.get("enabled") and cfg.get("type") == "button":
            entities.append(KinConyButton(coordinator, channel, cfg))
    async_add_entities(entities)


class KinConyButton(KinConyEntity, ButtonEntity):
    """KinCony output as momentary button."""

    async def async_press(self) -> None:
        pulse = float(self.cfg.get("pulse_seconds", DEFAULT_PULSE_SECONDS) or 0)
        await self.coordinator.async_pulse_output(self.channel, pulse)
