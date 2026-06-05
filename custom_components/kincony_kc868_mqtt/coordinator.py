"""MQTT coordinator for KinCony KC868 MQTT Controller."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Callable

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.util import dt as dt_util

from .const import CONF_COMMAND_TOPIC, CONF_STATE_TOPIC, DOMAIN

_LOGGER = logging.getLogger(__name__)

SIGNAL_UPDATE = f"{DOMAIN}_update"


class KinConyMqttCoordinator:
    """Small push coordinator backed by MQTT retained STATE messages."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.state_topic: str = entry.data[CONF_STATE_TOPIC]
        self.command_topic: str = entry.data[CONF_COMMAND_TOPIC]
        self.data: dict[str, Any] = {}
        self.available: bool = False
        self.last_seen: datetime | None = None
        self._unsub: Callable[[], None] | None = None

    async def async_start(self) -> None:
        """Subscribe to the state topic."""
        await self.async_stop()

        @callback
        def _message_received(msg: mqtt.ReceiveMessage) -> None:
            self._handle_message(msg.payload)

        self._unsub = await mqtt.async_subscribe(
            self.hass,
            self.state_topic,
            _message_received,
            qos=0,
            encoding="utf-8",
        )

    async def async_stop(self) -> None:
        """Unsubscribe from MQTT."""
        if self._unsub is not None:
            self._unsub()
            self._unsub = None

    @callback
    def _handle_message(self, payload: str | bytes) -> None:
        """Process STATE JSON."""
        try:
            if isinstance(payload, bytes):
                payload = payload.decode()
            parsed = json.loads(payload)
            if not isinstance(parsed, dict):
                raise ValueError("STATE payload is not an object")
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Invalid KinCony STATE payload on %s: %s", self.state_topic, err)
            return

        # KC868 firmware usually sends the complete state. If a future firmware sends
        # partial updates, merge them instead of dropping old channel values.
        self.data.update(parsed)
        self.available = True
        self.last_seen = dt_util.utcnow()
        async_dispatcher_send(self.hass, self.signal_update)

    @property
    def signal_update(self) -> str:
        return f"{SIGNAL_UPDATE}_{self.entry.entry_id}"

    async def async_publish_output(self, output: str, value: bool) -> None:
        """Publish an output command. Commands are never retained."""
        payload = json.dumps({output: {"value": value}}, separators=(",", ":"))
        await mqtt.async_publish(
            self.hass,
            self.command_topic,
            payload,
            qos=0,
            retain=False,
        )

    async def async_pulse_output(self, output: str, pulse_seconds: float) -> None:
        """Pulse an output."""
        await self.async_publish_output(output, True)
        if pulse_seconds > 0:
            await asyncio.sleep(pulse_seconds)
            await self.async_publish_output(output, False)

    async def async_request_refresh(self) -> None:
        """Optional refresh hook. Currently MQTT retained STATE is the source of truth."""
        refresh_payload = self.entry.options.get("refresh_payload") or self.entry.data.get("refresh_payload")
        if refresh_payload:
            await mqtt.async_publish(
                self.hass,
                self.command_topic,
                refresh_payload,
                qos=0,
                retain=False,
            )
