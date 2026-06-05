"""Helper functions for KinCony KC868 MQTT Controller."""
from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Any

from .const import DEFAULT_PULSE_SECONDS

_RE_INPUT = re.compile(r"^input(\d+)$")
_RE_OUTPUT = re.compile(r"^output(\d+)$")
_RE_ADC = re.compile(r"^adc(\d+)$")
_RE_SENSOR = re.compile(r"^sensor(\d+)$")


def sorted_channels(data: dict[str, Any], prefix: str) -> list[str]:
    def key_num(key: str) -> int:
        match = re.search(r"(\d+)", key)
        return int(match.group(1)) if match else 9999
    return sorted([k for k in data if k.startswith(prefix)], key=key_num)


def detect_counts(data: dict[str, Any]) -> dict[str, int]:
    return {
        "inputs": len([k for k in data if _RE_INPUT.match(k)]),
        "outputs": len([k for k in data if _RE_OUTPUT.match(k)]),
        "adcs": len([k for k in data if _RE_ADC.match(k)]),
        "sensors": len([k for k in data if _RE_SENSOR.match(k)]),
    }


def default_mapping(data: dict[str, Any]) -> dict[str, Any]:
    """Build editable default mapping from the first STATE JSON."""
    mapping: dict[str, Any] = {"inputs": {}, "outputs": {}, "sensors": {}}

    for channel in sorted_channels(data, "input"):
        number = channel.replace("input", "")
        mapping["inputs"][channel] = {
            "enabled": False,
            "name": f"Input {number}",
            "type": "binary_sensor",
            "device_class": "none",
            "invert": False,
            "icon": "",
        }

    for channel in sorted_channels(data, "output"):
        number = channel.replace("output", "")
        mapping["outputs"][channel] = {
            "enabled": False,
            "name": f"Output {number}",
            "type": "switch",
            "device_class": "none",
            "invert": False,
            "icon": "",
            "pulse_seconds": DEFAULT_PULSE_SECONDS,
        }

    for channel in sorted_channels(data, "adc"):
        number = channel.replace("adc", "")
        mapping["sensors"][channel] = {
            "enabled": False,
            "name": f"ADC {number}",
            "type": "sensor",
            "unit": "",
            "device_class": "none",
            "state_class": "measurement",
            "icon": "",
        }

    for channel in sorted_channels(data, "sensor"):
        number = channel.replace("sensor", "")
        value = data.get(channel, {})
        if isinstance(value, dict) and "temperature" in value:
            mapping["sensors"][f"{channel}_temperature"] = {
                "enabled": False,
                "source": channel,
                "field": "temperature",
                "name": f"Sensor {number} Temperature",
                "type": "sensor",
                "unit": "°C",
                "device_class": "temperature",
                "state_class": "measurement",
                "icon": "",
                "ignore_values": [-100],
            }
        if isinstance(value, dict) and "humidity" in value:
            mapping["sensors"][f"{channel}_humidity"] = {
                "enabled": False,
                "source": channel,
                "field": "humidity",
                "name": f"Sensor {number} Humidity",
                "type": "sensor",
                "unit": "%",
                "device_class": "humidity",
                "state_class": "measurement",
                "icon": "",
                "ignore_values": [-100],
            }

    return mapping


def normalize_mapping(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize mapping shape and fill optional keys."""
    mapping = deepcopy(raw)
    mapping.setdefault("inputs", {})
    mapping.setdefault("outputs", {})
    mapping.setdefault("sensors", {})

    for channel, cfg in mapping["inputs"].items():
        cfg.setdefault("enabled", False)
        cfg.setdefault("name", channel)
        cfg.setdefault("type", "binary_sensor")
        cfg.setdefault("device_class", "none")
        cfg.setdefault("invert", False)
        cfg.setdefault("icon", "")

    for channel, cfg in mapping["outputs"].items():
        cfg.setdefault("enabled", False)
        cfg.setdefault("name", channel)
        cfg.setdefault("type", "switch")
        cfg.setdefault("device_class", "none")
        cfg.setdefault("invert", False)
        cfg.setdefault("icon", "")
        cfg.setdefault("pulse_seconds", DEFAULT_PULSE_SECONDS)

    for channel, cfg in mapping["sensors"].items():
        cfg.setdefault("enabled", False)
        cfg.setdefault("name", channel)
        cfg.setdefault("type", "sensor")
        cfg.setdefault("unit", "")
        cfg.setdefault("device_class", "none")
        cfg.setdefault("state_class", "measurement")
        cfg.setdefault("icon", "")

    return mapping


def mapping_to_text(mapping: dict[str, Any]) -> str:
    return json.dumps(mapping, ensure_ascii=False, indent=2)


def mapping_from_text(text: str) -> dict[str, Any]:
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("Mapping must be a JSON object")
    return normalize_mapping(parsed)


def value_from_state(data: dict[str, Any] | None, channel: str, field: str = "value") -> Any:
    if not data:
        return None
    source = data.get(channel)
    if isinstance(source, dict):
        return source.get(field)
    return None


def sensor_value_from_state(data: dict[str, Any] | None, cfg_key: str, cfg: dict[str, Any]) -> Any:
    if not data:
        return None
    source = cfg.get("source") or cfg_key
    field = cfg.get("field", "value")
    source_value = data.get(source)
    if isinstance(source_value, dict):
        value = source_value.get(field)
    else:
        value = None
    if value in cfg.get("ignore_values", []):
        return None
    return value
