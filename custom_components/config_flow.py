"""Config flow for KinCony KC868 MQTT Controller."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import mqtt
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector

from .const import (
    CONF_COMMAND_TOPIC,
    CONF_MAPPING,
    CONF_MODEL,
    CONF_MQTT_PREFIX,
    CONF_NAME,
    CONF_REFRESH_PAYLOAD,
    CONF_STATE_TOPIC,
    DEFAULT_MODEL,
    DEFAULT_NAME,
    DOMAIN,
)
from .helpers import default_mapping, detect_counts, mapping_from_text, mapping_to_text, normalize_mapping

_LOGGER = logging.getLogger(__name__)


async def _wait_for_state(hass: HomeAssistant, topic: str, timeout: int = 8) -> dict[str, Any] | None:
    """Wait for one MQTT STATE message. Retained STATE should arrive immediately."""
    future: asyncio.Future[dict[str, Any]] = hass.loop.create_future()

    @callback
    def _message_received(msg: mqtt.ReceiveMessage) -> None:
        if future.done():
            return
        try:
            payload = json.loads(msg.payload)
            if isinstance(payload, dict):
                future.set_result(payload)
            else:
                future.set_exception(ValueError("Payload is not JSON object"))
        except Exception as err:  # noqa: BLE001
            future.set_exception(err)

    unsub = await mqtt.async_subscribe(hass, topic, _message_received, qos=0, encoding="utf-8")
    try:
        return await asyncio.wait_for(future, timeout=timeout)
    except asyncio.TimeoutError:
        return None
    finally:
        unsub()


def _user_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)): str,
            vol.Optional(CONF_HOST, default=defaults.get(CONF_HOST, "")): str,
            vol.Optional(CONF_MODEL, default=defaults.get(CONF_MODEL, DEFAULT_MODEL)): str,
            vol.Required(CONF_MQTT_PREFIX, default=defaults.get(CONF_MQTT_PREFIX, "KC868_A16/ECC9FF002428")): str,
            vol.Optional(CONF_STATE_TOPIC, default=defaults.get(CONF_STATE_TOPIC, "")): str,
            vol.Optional(CONF_COMMAND_TOPIC, default=defaults.get(CONF_COMMAND_TOPIC, "")): str,
            vol.Optional(CONF_REFRESH_PAYLOAD, default=defaults.get(CONF_REFRESH_PAYLOAD, "")): str,
        }
    )


def _mapping_schema(default_text: str) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                "mapping_json",
                default=default_text,
            ): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True, type=selector.TextSelectorType.TEXT)
            )
        }
    )


class KinConyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._base_data: dict[str, Any] = {}
        self._detected_state: dict[str, Any] | None = None
        self._default_mapping_text = "{}"
        self._counts: dict[str, int] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            prefix = user_input[CONF_MQTT_PREFIX].strip().strip("/")
            state_topic = (user_input.get(CONF_STATE_TOPIC) or f"{prefix}/STATE").strip()
            command_topic = (user_input.get(CONF_COMMAND_TOPIC) or f"{prefix}/SET").strip()
            base_data = {
                CONF_NAME: user_input[CONF_NAME].strip(),
                CONF_HOST: (user_input.get(CONF_HOST) or "").strip(),
                CONF_MODEL: (user_input.get(CONF_MODEL) or DEFAULT_MODEL).strip(),
                CONF_MQTT_PREFIX: prefix,
                CONF_STATE_TOPIC: state_topic,
                CONF_COMMAND_TOPIC: command_topic,
                CONF_REFRESH_PAYLOAD: (user_input.get(CONF_REFRESH_PAYLOAD) or "").strip(),
            }

            await self.async_set_unique_id(prefix)
            self._abort_if_unique_id_configured()

            detected_state = await _wait_for_state(self.hass, state_topic)
            if detected_state is None:
                errors["base"] = "no_state_message"
            else:
                self._base_data = base_data
                self._detected_state = detected_state
                self._counts = detect_counts(detected_state)
                self._default_mapping_text = mapping_to_text(default_mapping(detected_state))
                return await self.async_step_mapping()

        return self.async_show_form(
            step_id="user",
            data_schema=_user_schema(user_input),
            errors=errors,
        )

    async def async_step_mapping(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                mapping = mapping_from_text(user_input["mapping_json"])
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Invalid KinCony mapping JSON: %s", err)
                errors["mapping_json"] = "invalid_mapping"
            else:
                data = dict(self._base_data)
                data[CONF_MAPPING] = mapping
                return self.async_create_entry(title=data[CONF_NAME], data=data)

        placeholders = {
            "inputs": str(self._counts.get("inputs", 0)),
            "outputs": str(self._counts.get("outputs", 0)),
            "adcs": str(self._counts.get("adcs", 0)),
            "sensors": str(self._counts.get("sensors", 0)),
        }
        return self.async_show_form(
            step_id="mapping",
            data_schema=_mapping_schema(self._default_mapping_text),
            errors=errors,
            description_placeholders=placeholders,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return KinConyOptionsFlow(config_entry)


class KinConyOptionsFlow(config_entries.OptionsFlow):
    """Options flow for editing mapping."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            try:
                mapping = mapping_from_text(user_input["mapping_json"])
            except Exception:  # noqa: BLE001
                return self.async_show_form(
                    step_id="init",
                    data_schema=_mapping_schema(user_input["mapping_json"]),
                    errors={"mapping_json": "invalid_mapping"},
                )
            new_data = dict(self.entry.data)
            new_data[CONF_MAPPING] = mapping
            self.hass.config_entries.async_update_entry(self.entry, data=new_data)
            return self.async_create_entry(title="", data={})

        mapping_text = mapping_to_text(normalize_mapping(self.entry.data.get(CONF_MAPPING, {})))
        return self.async_show_form(
            step_id="init",
            data_schema=_mapping_schema(mapping_text),
        )
