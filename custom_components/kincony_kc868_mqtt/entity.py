"""Base entities for KinCony KC868 MQTT Controller."""
from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import CONF_HOST, CONF_MODEL, CONF_NAME, CONF_MQTT_PREFIX, DOMAIN
from .coordinator import KinConyMqttCoordinator


class KinConyEntity(Entity):
    """Base KinCony entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: KinConyMqttCoordinator, channel: str, cfg: dict[str, Any]) -> None:
        self.coordinator = coordinator
        self.channel = channel
        self.cfg = cfg
        self._attr_name = cfg.get("name", channel)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{channel}"
        icon = cfg.get("icon")
        if icon:
            self._attr_icon = icon

    @property
    def device_info(self) -> DeviceInfo:
        data = self.coordinator.entry.data
        prefix = data.get(CONF_MQTT_PREFIX, self.coordinator.state_topic)
        return DeviceInfo(
            identifiers={(DOMAIN, prefix)},
            name=data.get(CONF_NAME, "KinCony KC868"),
            manufacturer="KinCony",
            model=data.get(CONF_MODEL, "KC868"),
            configuration_url=f"http://{data[CONF_HOST]}" if data.get(CONF_HOST) else None,
        )

    @property
    def available(self) -> bool:
        return self.coordinator.available

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                self.coordinator.signal_update,
                self.async_write_ha_state,
            )
        )
