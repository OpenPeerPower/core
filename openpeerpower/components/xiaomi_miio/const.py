"""Constants for the Xiaomi Miio component."""
DOMAIN = "xiaomi_miio"

CONF_FLOW_TYPE = "config_flow_device"
CONF_GATEWAY = "gateway"
CONF_DEVICE = "device"
CONF_MODEL = "model"
CONF_MAC = "mac"

KEY_COORDINATOR = "coordinator"

# Fam Models
MODEL_AIRPURIFIER_V1 = "zhimi.airpurifier.v1"
MODEL_AIRPURIFIER_V2 = "zhimi.airpurifier.v2"
MODEL_AIRPURIFIER_V3 = "zhimi.airpurifier.v3"
MODEL_AIRPURIFIER_V5 = "zhimi.airpurifier.v5"
MODEL_AIRPURIFIER_PRO = "zhimi.airpurifier.v6"
MODEL_AIRPURIFIER_PRO_V7 = "zhimi.airpurifier.v7"
MODEL_AIRPURIFIER_M1 = "zhimi.airpurifier.m1"
MODEL_AIRPURIFIER_M2 = "zhimi.airpurifier.m2"
MODEL_AIRPURIFIER_MA1 = "zhimi.airpurifier.ma1"
MODEL_AIRPURIFIER_MA2 = "zhimi.airpurifier.ma2"
MODEL_AIRPURIFIER_SA1 = "zhimi.airpurifier.sa1"
MODEL_AIRPURIFIER_SA2 = "zhimi.airpurifier.sa2"
MODEL_AIRPURIFIER_2S = "zhimi.airpurifier.mc1"
MODEL_AIRPURIFIER_3 = "zhimi.airpurifier.ma4"
MODEL_AIRPURIFIER_3H = "zhimi.airpurifier.mb3"

MODEL_AIRHUMIDIFIER_V1 = "zhimi.humidifier.v1"
MODEL_AIRHUMIDIFIER_CA1 = "zhimi.humidifier.ca1"
MODEL_AIRHUMIDIFIER_CA4 = "zhimi.humidifier.ca4"
MODEL_AIRHUMIDIFIER_CB1 = "zhimi.humidifier.cb1"

MODEL_AIRFRESH_VA2 = "zhimi.airfresh.va2"

MODELS_PURIFIER_MIOT = [MODEL_AIRPURIFIER_3, MODEL_AIRPURIFIER_3H]
MODELS_HUMIDIFIER_MIOT = [MODEL_AIRHUMIDIFIER_CA4]
MODELS_FAN_MIIO = [
    MODEL_AIRPURIFIER_V1,
    MODEL_AIRPURIFIER_V2,
    MODEL_AIRPURIFIER_V3,
    MODEL_AIRPURIFIER_V5,
    MODEL_AIRPURIFIER_PRO,
    MODEL_AIRPURIFIER_PRO_V7,
    MODEL_AIRPURIFIER_M1,
    MODEL_AIRPURIFIER_M2,
    MODEL_AIRPURIFIER_MA1,
    MODEL_AIRPURIFIER_MA2,
    MODEL_AIRPURIFIER_SA1,
    MODEL_AIRPURIFIER_SA2,
    MODEL_AIRPURIFIER_2S,
    MODEL_AIRHUMIDIFIER_V1,
    MODEL_AIRHUMIDIFIER_CA1,
    MODEL_AIRHUMIDIFIER_CB1,
    MODEL_AIRFRESH_VA2,
]

# Model lists
MODELS_GATEWAY = ["lumi.gateway", "lumi.acpartner"]
MODELS_SWITCH = [
    "chuangmi.plug.v1",
    "chuangmi.plug.v3",
    "chuangmi.plug.hmi208",
    "qmi.powerstrip.v1",
    "zimi.powerstrip.v2",
    "chuangmi.plug.m1",
    "chuangmi.plug.m3",
    "chuangmi.plug.v2",
    "chuangmi.plug.hmi205",
    "chuangmi.plug.hmi206",
    "lumi.acpartner.v3",
]
MODELS_FAN = MODELS_FAN_MIIO + MODELS_HUMIDIFIER_MIOT + MODELS_PURIFIER_MIOT
MODELS_VACUUM = ["roborock.vacuum"]

MODELS_ALL_DEVICES = MODELS_SWITCH + MODELS_FAN + MODELS_VACUUM
MODELS_ALL = MODELS_ALL_DEVICES + MODELS_GATEWAY

# Fan Services
SERVICE_SET_BUZZER_ON = "fan_set_buzzer_on"
SERVICE_SET_BUZZER_OFF = "fan_set_buzzer_off"
SERVICE_SET_FAN_LED_ON = "fan_set_led_on"
SERVICE_SET_FAN_LED_OFF = "fan_set_led_off"
SERVICE_SET_CHILD_LOCK_ON = "fan_set_child_lock_on"
SERVICE_SET_CHILD_LOCK_OFF = "fan_set_child_lock_off"
SERVICE_SET_LED_BRIGHTNESS = "fan_set_led_brightness"
SERVICE_SET_FAVORITE_LEVEL = "fan_set_favorite_level"
SERVICE_SET_FAN_LEVEL = "fan_set_fan_level"
SERVICE_SET_AUTO_DETECT_ON = "fan_set_auto_detect_on"
SERVICE_SET_AUTO_DETECT_OFF = "fan_set_auto_detect_off"
SERVICE_SET_LEARN_MODE_ON = "fan_set_learn_mode_on"
SERVICE_SET_LEARN_MODE_OFF = "fan_set_learn_mode_off"
SERVICE_SET_VOLUME = "fan_set_volume"
SERVICE_RESET_FILTER = "fan_reset_filter"
SERVICE_SET_EXTRA_FEATURES = "fan_set_extra_features"
SERVICE_SET_TARGET_HUMIDITY = "fan_set_target_humidity"
SERVICE_SET_DRY_ON = "fan_set_dry_on"
SERVICE_SET_DRY_OFF = "fan_set_dry_off"
SERVICE_SET_MOTOR_SPEED = "fan_set_motor_speed"

# Light Services
SERVICE_SET_SCENE = "light_set_scene"
SERVICE_SET_DELAYED_TURN_OFF = "light_set_delayed_turn_off"
SERVICE_REMINDER_ON = "light_reminder_on"
SERVICE_REMINDER_OFF = "light_reminder_off"
SERVICE_NIGHT_LIGHT_MODE_ON = "light_night_light_mode_on"
SERVICE_NIGHT_LIGHT_MODE_OFF = "light_night_light_mode_off"
SERVICE_EYECARE_MODE_ON = "light_eyecare_mode_on"
SERVICE_EYECARE_MODE_OFF = "light_eyecare_mode_off"

# Remote Services
SERVICE_LEARN = "remote_learn_command"
SERVICE_SET_REMOTE_LED_ON = "remote_set_led_on"
SERVICE_SET_REMOTE_LED_OFF = "remote_set_led_off"

# Switch Services
SERVICE_SET_WIFI_LED_ON = "switch_set_wifi_led_on"
SERVICE_SET_WIFI_LED_OFF = "switch_set_wifi_led_off"
SERVICE_SET_POWER_MODE = "switch_set_power_mode"
SERVICE_SET_POWER_PRICE = "switch_set_power_price"

# Vacuum Services
SERVICE_MOVE_REMOTE_CONTROL = "vacuum_remote_control_move"
SERVICE_MOVE_REMOTE_CONTROL_STEP = "vacuum_remote_control_move_step"
SERVICE_START_REMOTE_CONTROL = "vacuum_remote_control_start"
SERVICE_STOP_REMOTE_CONTROL = "vacuum_remote_control_stop"
SERVICE_CLEAN_SEGMENT = "vacuum_clean_segment"
SERVICE_CLEAN_ZONE = "vacuum_clean_zone"
SERVICE_GOTO = "vacuum_goto"

# AirQuality Model
MODEL_AIRQUALITYMONITOR_V1 = "zhimi.airmonitor.v1"
MODEL_AIRQUALITYMONITOR_B1 = "cgllc.airmonitor.b1"
MODEL_AIRQUALITYMONITOR_S1 = "cgllc.airmonitor.s1"
