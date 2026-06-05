"""Constants for KinCony KC868 MQTT Controller."""
from __future__ import annotations

DOMAIN = "kincony_kc868_mqtt"

CONF_NAME = "name"
CONF_HOST = "host"
CONF_MODEL = "model"
CONF_MQTT_PREFIX = "mqtt_prefix"
CONF_STATE_TOPIC = "state_topic"
CONF_COMMAND_TOPIC = "command_topic"
CONF_MAPPING = "mapping"
CONF_REFRESH_PAYLOAD = "refresh_payload"

DEFAULT_NAME = "KinCony KC868"
DEFAULT_MODEL = "KC868"
DEFAULT_PULSE_SECONDS = 0.5

PLATFORMS = ["binary_sensor", "button", "light", "sensor", "switch"]

INPUT_TYPES = ["disabled", "binary_sensor"]
OUTPUT_TYPES = ["disabled", "switch", "light", "button"]
SENSOR_TYPES = ["disabled", "sensor"]

DEVICE_CLASSES_BINARY = [
    "none",
    "door",
    "garage_door",
    "window",
    "motion",
    "occupancy",
    "problem",
    "safety",
    "moisture",
    "lock",
    "opening",
]

DEVICE_CLASSES_SWITCH = ["none", "outlet", "switch"]
