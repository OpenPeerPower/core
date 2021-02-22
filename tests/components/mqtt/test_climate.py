"""The tests for the mqtt climate component."""
import copy
import json
from unittest.mock import call, patch

import pytest
import voluptuous as vol

from openpeerpower.components.climate import DEFAULT_MAX_TEMP, DEFAULT_MIN_TEMP
from openpeerpower.components.climate.const import (
    DOMAIN as CLIMATE_DOMAIN,
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    PRESET_ECO,
    PRESET_NONE,
    SUPPORT_AUX_HEAT,
    SUPPORT_FAN_MODE,
    SUPPORT_PRESET_MODE,
    SUPPORT_SWING_MODE,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_TARGET_TEMPERATURE_RANGE,
)
from openpeerpower.const import STATE_OFF
from openpeerpower.setup import async_setup_component

from .test_common import (
    help_test_availability_when_connection_lost,
    help_test_availability_without_topic,
    help_test_custom_availability_payload,
    help_test_default_availability_payload,
    help_test_discovery_broken,
    help_test_discovery_removal,
    help_test_discovery_update,
    help_test_discovery_update_attr,
    help_test_discovery_update_unchanged,
    help_test_entity_debug_info_message,
    help_test_entity_device_info_remove,
    help_test_entity_device_info_update,
    help_test_entity_device_info_with_connection,
    help_test_entity_device_info_with_identifier,
    help_test_entity_id_update_discovery_update,
    help_test_entity_id_update_subscriptions,
    help_test_setting_attribute_via_mqtt_json_message,
    help_test_setting_attribute_with_template,
    help_test_unique_id,
    help_test_update_with_json_attrs_bad_JSON,
    help_test_update_with_json_attrs_not_dict,
)

from tests.common import async_fire_mqtt_message
from tests.components.climate import common

ENTITY_CLIMATE = "climate.test"

DEFAULT_CONFIG = {
    CLIMATE_DOMAIN: {
        "platform": "mqtt",
        "name": "test",
        "mode_command_topic": "mode-topic",
        "temperature_command_topic": "temperature-topic",
        "temperature_low_command_topic": "temperature-low-topic",
        "temperature_high_command_topic": "temperature-high-topic",
        "fan_mode_command_topic": "fan-mode-topic",
        "swing_mode_command_topic": "swing-mode-topic",
        "away_mode_command_topic": "away-mode-topic",
        "hold_command_topic": "hold-topic",
        "aux_command_topic": "aux-topic",
    }
}


async def test_setup_params.opp, mqtt_mock):
    """Test the initial parameters."""
    assert await async_setup_component.opp, CLIMATE_DOMAIN, DEFAULT_CONFIG)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("temperature") == 21
    assert state.attributes.get("fan_mode") == "low"
    assert state.attributes.get("swing_mode") == "off"
    assert state.state == "off"
    assert state.attributes.get("min_temp") == DEFAULT_MIN_TEMP
    assert state.attributes.get("max_temp") == DEFAULT_MAX_TEMP


async def test_supported_features.opp, mqtt_mock):
    """Test the supported_features."""
    assert await async_setup_component.opp, CLIMATE_DOMAIN, DEFAULT_CONFIG)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)
    support = (
        SUPPORT_TARGET_TEMPERATURE
        | SUPPORT_SWING_MODE
        | SUPPORT_FAN_MODE
        | SUPPORT_PRESET_MODE
        | SUPPORT_AUX_HEAT
        | SUPPORT_TARGET_TEMPERATURE_RANGE
    )

    assert state.attributes.get("supported_features") == support


async def test_get_hvac_modes.opp, mqtt_mock):
    """Test that the operation list returns the correct modes."""
    assert await async_setup_component.opp, CLIMATE_DOMAIN, DEFAULT_CONFIG)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)
    modes = state.attributes.get("hvac_modes")
    assert [
        HVAC_MODE_AUTO,
        STATE_OFF,
        HVAC_MODE_COOL,
        HVAC_MODE_HEAT,
        HVAC_MODE_DRY,
        HVAC_MODE_FAN_ONLY,
    ] == modes


async def test_set_operation_bad_attr_and_state.opp, mqtt_mock, caplog):
    """Test setting operation mode without required attribute.

    Also check the state.
    """
    assert await async_setup_component.opp, CLIMATE_DOMAIN, DEFAULT_CONFIG)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)
    assert state.state == "off"
    with pytest.raises(vol.Invalid) as excinfo:
        await common.async_set_hvac_mode.opp, None, ENTITY_CLIMATE)
    assert (
        "value must be one of ['auto', 'cool', 'dry', 'fan_only', 'heat', 'heat_cool', 'off'] for dictionary value @ data['hvac_mode']"
    ) in str(excinfo.value)
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.state == "off"


async def test_set_operation.opp, mqtt_mock):
    """Test setting of new operation mode."""
    assert await async_setup_component.opp, CLIMATE_DOMAIN, DEFAULT_CONFIG)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)
    assert state.state == "off"
    await common.async_set_hvac_mode.opp, "cool", ENTITY_CLIMATE)
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.state == "cool"
    assert state.state == "cool"
    mqtt_mock.async_publish.assert_called_once_with("mode-topic", "cool", 0, False)


async def test_set_operation_pessimistic.opp, mqtt_mock):
    """Test setting operation mode in pessimistic mode."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["climate"]["mode_state_topic"] = "mode-state"
    assert await async_setup_component.opp, CLIMATE_DOMAIN, config)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)
    assert state.state == "unknown"

    await common.async_set_hvac_mode.opp, "cool", ENTITY_CLIMATE)
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.state == "unknown"

    async_fire_mqtt_message.opp, "mode-state", "cool")
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.state == "cool"

    async_fire_mqtt_message.opp, "mode-state", "bogus mode")
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.state == "cool"


async def test_set_operation_with_power_command.opp, mqtt_mock):
    """Test setting of new operation mode with power command enabled."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["climate"]["power_command_topic"] = "power-command"
    assert await async_setup_component.opp, CLIMATE_DOMAIN, config)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)
    assert state.state == "off"
    await common.async_set_hvac_mode.opp, "cool", ENTITY_CLIMATE)
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.state == "cool"
    mqtt_mock.async_publish.assert_has_calls(
        [call("power-command", "ON", 0, False), call("mode-topic", "cool", 0, False)]
    )
    mqtt_mock.async_publish.reset_mock()

    await common.async_set_hvac_mode.opp, "off", ENTITY_CLIMATE)
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.state == "off"
    mqtt_mock.async_publish.assert_has_calls(
        [call("power-command", "OFF", 0, False), call("mode-topic", "off", 0, False)]
    )
    mqtt_mock.async_publish.reset_mock()


async def test_set_fan_mode_bad_attr.opp, mqtt_mock, caplog):
    """Test setting fan mode without required attribute."""
    assert await async_setup_component.opp, CLIMATE_DOMAIN, DEFAULT_CONFIG)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("fan_mode") == "low"
    with pytest.raises(vol.Invalid) as excinfo:
        await common.async_set_fan_mode.opp, None, ENTITY_CLIMATE)
    assert "string value is None for dictionary value @ data['fan_mode']" in str(
        excinfo.value
    )
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("fan_mode") == "low"


async def test_set_fan_mode_pessimistic.opp, mqtt_mock):
    """Test setting of new fan mode in pessimistic mode."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["climate"]["fan_mode_state_topic"] = "fan-state"
    assert await async_setup_component.opp, CLIMATE_DOMAIN, config)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("fan_mode") is None

    await common.async_set_fan_mode.opp, "high", ENTITY_CLIMATE)
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("fan_mode") is None

    async_fire_mqtt_message.opp, "fan-state", "high")
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("fan_mode") == "high"

    async_fire_mqtt_message.opp, "fan-state", "bogus mode")
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("fan_mode") == "high"


async def test_set_fan_mode.opp, mqtt_mock):
    """Test setting of new fan mode."""
    assert await async_setup_component.opp, CLIMATE_DOMAIN, DEFAULT_CONFIG)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("fan_mode") == "low"
    await common.async_set_fan_mode.opp, "high", ENTITY_CLIMATE)
    mqtt_mock.async_publish.assert_called_once_with("fan-mode-topic", "high", 0, False)
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("fan_mode") == "high"


async def test_set_swing_mode_bad_attr.opp, mqtt_mock, caplog):
    """Test setting swing mode without required attribute."""
    assert await async_setup_component.opp, CLIMATE_DOMAIN, DEFAULT_CONFIG)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_mode") == "off"
    with pytest.raises(vol.Invalid) as excinfo:
        await common.async_set_swing_mode.opp, None, ENTITY_CLIMATE)
    assert "string value is None for dictionary value @ data['swing_mode']" in str(
        excinfo.value
    )
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_mode") == "off"


async def test_set_swing_pessimistic.opp, mqtt_mock):
    """Test setting swing mode in pessimistic mode."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["climate"]["swing_mode_state_topic"] = "swing-state"
    assert await async_setup_component.opp, CLIMATE_DOMAIN, config)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_mode") is None

    await common.async_set_swing_mode.opp, "on", ENTITY_CLIMATE)
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_mode") is None

    async_fire_mqtt_message.opp, "swing-state", "on")
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_mode") == "on"

    async_fire_mqtt_message.opp, "swing-state", "bogus state")
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_mode") == "on"


async def test_set_swing.opp, mqtt_mock):
    """Test setting of new swing mode."""
    assert await async_setup_component.opp, CLIMATE_DOMAIN, DEFAULT_CONFIG)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_mode") == "off"
    await common.async_set_swing_mode.opp, "on", ENTITY_CLIMATE)
    mqtt_mock.async_publish.assert_called_once_with("swing-mode-topic", "on", 0, False)
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_mode") == "on"


async def test_set_target_temperature.opp, mqtt_mock):
    """Test setting the target temperature."""
    assert await async_setup_component.opp, CLIMATE_DOMAIN, DEFAULT_CONFIG)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("temperature") == 21
    await common.async_set_hvac_mode.opp, "heat", ENTITY_CLIMATE)
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.state == "heat"
    mqtt_mock.async_publish.assert_called_once_with("mode-topic", "heat", 0, False)
    mqtt_mock.async_publish.reset_mock()
    await common.async_set_temperature.opp, temperature=47, entity_id=ENTITY_CLIMATE)
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("temperature") == 47
    mqtt_mock.async_publish.assert_called_once_with(
        "temperature-topic", "47.0", 0, False
    )

    # also test directly supplying the operation mode to set_temperature
    mqtt_mock.async_publish.reset_mock()
    await common.async_set_temperature(
       .opp, temperature=21, hvac_mode="cool", entity_id=ENTITY_CLIMATE
    )
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.state == "cool"
    assert state.attributes.get("temperature") == 21
    mqtt_mock.async_publish.assert_has_calls(
        [
            call("mode-topic", "cool", 0, False),
            call("temperature-topic", "21.0", 0, False),
        ]
    )
    mqtt_mock.async_publish.reset_mock()


async def test_set_target_temperature_pessimistic.opp, mqtt_mock):
    """Test setting the target temperature."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["climate"]["temperature_state_topic"] = "temperature-state"
    assert await async_setup_component.opp, CLIMATE_DOMAIN, config)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("temperature") is None
    await common.async_set_hvac_mode.opp, "heat", ENTITY_CLIMATE)
    await common.async_set_temperature.opp, temperature=47, entity_id=ENTITY_CLIMATE)
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("temperature") is None

    async_fire_mqtt_message.opp, "temperature-state", "1701")
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("temperature") == 1701

    async_fire_mqtt_message.opp, "temperature-state", "not a number")
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("temperature") == 1701


async def test_set_target_temperature_low_high.opp, mqtt_mock):
    """Test setting the low/high target temperature."""
    assert await async_setup_component.opp, CLIMATE_DOMAIN, DEFAULT_CONFIG)
    await.opp.async_block_till_done()

    await common.async_set_temperature(
       .opp, target_temp_low=20, target_temp_high=23, entity_id=ENTITY_CLIMATE
    )
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("target_temp_low") == 20
    assert state.attributes.get("target_temp_high") == 23
    mqtt_mock.async_publish.assert_any_call("temperature-low-topic", "20.0", 0, False)
    mqtt_mock.async_publish.assert_any_call("temperature-high-topic", "23.0", 0, False)


async def test_set_target_temperature_low_highpessimistic.opp, mqtt_mock):
    """Test setting the low/high target temperature."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["climate"]["temperature_low_state_topic"] = "temperature-low-state"
    config["climate"]["temperature_high_state_topic"] = "temperature-high-state"
    assert await async_setup_component.opp, CLIMATE_DOMAIN, config)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("target_temp_low") is None
    assert state.attributes.get("target_temp_high") is None
    await common.async_set_temperature(
       .opp, target_temp_low=20, target_temp_high=23, entity_id=ENTITY_CLIMATE
    )
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("target_temp_low") is None
    assert state.attributes.get("target_temp_high") is None

    async_fire_mqtt_message.opp, "temperature-low-state", "1701")
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("target_temp_low") == 1701
    assert state.attributes.get("target_temp_high") is None

    async_fire_mqtt_message.opp, "temperature-high-state", "1703")
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("target_temp_low") == 1701
    assert state.attributes.get("target_temp_high") == 1703

    async_fire_mqtt_message.opp, "temperature-low-state", "not a number")
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("target_temp_low") == 1701

    async_fire_mqtt_message.opp, "temperature-high-state", "not a number")
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("target_temp_high") == 1703


async def test_receive_mqtt_temperature.opp, mqtt_mock):
    """Test getting the current temperature via MQTT."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["climate"]["current_temperature_topic"] = "current_temperature"
    assert await async_setup_component.opp, CLIMATE_DOMAIN, config)
    await.opp.async_block_till_done()

    async_fire_mqtt_message.opp, "current_temperature", "47")
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("current_temperature") == 47


async def test_set_away_mode_pessimistic.opp, mqtt_mock):
    """Test setting of the away mode."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["climate"]["away_mode_state_topic"] = "away-state"
    assert await async_setup_component.opp, CLIMATE_DOMAIN, config)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "none"

    await common.async_set_preset_mode.opp, "away", ENTITY_CLIMATE)
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "none"

    async_fire_mqtt_message.opp, "away-state", "ON")
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "away"

    async_fire_mqtt_message.opp, "away-state", "OFF")
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "none"

    async_fire_mqtt_message.opp, "away-state", "nonsense")
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "none"


async def test_set_away_mode.opp, mqtt_mock):
    """Test setting of the away mode."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["climate"]["payload_on"] = "AN"
    config["climate"]["payload_off"] = "AUS"

    assert await async_setup_component.opp, CLIMATE_DOMAIN, config)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "none"
    await common.async_set_preset_mode.opp, "away", ENTITY_CLIMATE)
    mqtt_mock.async_publish.assert_called_once_with("away-mode-topic", "AN", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "away"

    await common.async_set_preset_mode.opp, PRESET_NONE, ENTITY_CLIMATE)
    mqtt_mock.async_publish.assert_called_once_with("away-mode-topic", "AUS", 0, False)
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "none"

    await common.async_set_preset_mode.opp, "hold-on", ENTITY_CLIMATE)
    mqtt_mock.async_publish.reset_mock()

    await common.async_set_preset_mode.opp, "away", ENTITY_CLIMATE)
    mqtt_mock.async_publish.assert_has_calls(
        [call("hold-topic", "off", 0, False), call("away-mode-topic", "AN", 0, False)]
    )
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "away"


async def test_set_hvac_action.opp, mqtt_mock):
    """Test setting of the HVAC action."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["climate"]["action_topic"] = "action"
    assert await async_setup_component.opp, CLIMATE_DOMAIN, config)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("hvac_action") is None

    async_fire_mqtt_message.opp, "action", "cool")
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("hvac_action") == "cool"


async def test_set_hold_pessimistic.opp, mqtt_mock):
    """Test setting the hold mode in pessimistic mode."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["climate"]["hold_state_topic"] = "hold-state"
    assert await async_setup_component.opp, CLIMATE_DOMAIN, config)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("hold_mode") is None

    await common.async_set_preset_mode.opp, "hold", ENTITY_CLIMATE)
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("hold_mode") is None

    async_fire_mqtt_message.opp, "hold-state", "on")
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "on"

    async_fire_mqtt_message.opp, "hold-state", "off")
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "none"


async def test_set_hold.opp, mqtt_mock):
    """Test setting the hold mode."""
    assert await async_setup_component.opp, CLIMATE_DOMAIN, DEFAULT_CONFIG)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "none"
    await common.async_set_preset_mode.opp, "hold-on", ENTITY_CLIMATE)
    mqtt_mock.async_publish.assert_called_once_with("hold-topic", "hold-on", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "hold-on"

    await common.async_set_preset_mode.opp, PRESET_ECO, ENTITY_CLIMATE)
    mqtt_mock.async_publish.assert_called_once_with("hold-topic", "eco", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == PRESET_ECO

    await common.async_set_preset_mode.opp, PRESET_NONE, ENTITY_CLIMATE)
    mqtt_mock.async_publish.assert_called_once_with("hold-topic", "off", 0, False)
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "none"


async def test_set_preset_mode_twice.opp, mqtt_mock):
    """Test setting of the same mode twice only publishes once."""
    assert await async_setup_component.opp, CLIMATE_DOMAIN, DEFAULT_CONFIG)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "none"
    await common.async_set_preset_mode.opp, "hold-on", ENTITY_CLIMATE)
    mqtt_mock.async_publish.assert_called_once_with("hold-topic", "hold-on", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "hold-on"

    await common.async_set_preset_mode.opp, "hold-on", ENTITY_CLIMATE)
    mqtt_mock.async_publish.assert_not_called()


async def test_set_aux_pessimistic.opp, mqtt_mock):
    """Test setting of the aux heating in pessimistic mode."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["climate"]["aux_state_topic"] = "aux-state"
    assert await async_setup_component.opp, CLIMATE_DOMAIN, config)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("aux_heat") == "off"

    await common.async_set_aux_heat.opp, True, ENTITY_CLIMATE)
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("aux_heat") == "off"

    async_fire_mqtt_message.opp, "aux-state", "ON")
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("aux_heat") == "on"

    async_fire_mqtt_message.opp, "aux-state", "OFF")
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("aux_heat") == "off"

    async_fire_mqtt_message.opp, "aux-state", "nonsense")
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("aux_heat") == "off"


async def test_set_aux.opp, mqtt_mock):
    """Test setting of the aux heating."""
    assert await async_setup_component.opp, CLIMATE_DOMAIN, DEFAULT_CONFIG)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("aux_heat") == "off"
    await common.async_set_aux_heat.opp, True, ENTITY_CLIMATE)
    mqtt_mock.async_publish.assert_called_once_with("aux-topic", "ON", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("aux_heat") == "on"

    await common.async_set_aux_heat.opp, False, ENTITY_CLIMATE)
    mqtt_mock.async_publish.assert_called_once_with("aux-topic", "OFF", 0, False)
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("aux_heat") == "off"


async def test_availability_when_connection_lost.opp, mqtt_mock):
    """Test availability after MQTT disconnection."""
    await help_test_availability_when_connection_lost(
       .opp, mqtt_mock, CLIMATE_DOMAIN, DEFAULT_CONFIG
    )


async def test_availability_without_topic.opp, mqtt_mock):
    """Test availability without defined availability topic."""
    await help_test_availability_without_topic(
       .opp, mqtt_mock, CLIMATE_DOMAIN, DEFAULT_CONFIG
    )


async def test_default_availability_payload.opp, mqtt_mock):
    """Test availability by default payload with defined topic."""
    await help_test_default_availability_payload(
       .opp, mqtt_mock, CLIMATE_DOMAIN, DEFAULT_CONFIG
    )


async def test_custom_availability_payload.opp, mqtt_mock):
    """Test availability by custom payload with defined topic."""
    await help_test_custom_availability_payload(
       .opp, mqtt_mock, CLIMATE_DOMAIN, DEFAULT_CONFIG
    )


async def test_get_target_temperature_low_high_with_templates.opp, mqtt_mock, caplog):
    """Test getting temperature high/low with templates."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["climate"]["temperature_low_state_topic"] = "temperature-state"
    config["climate"]["temperature_high_state_topic"] = "temperature-state"
    config["climate"]["temperature_low_state_template"] = "{{ value_json.temp_low }}"
    config["climate"]["temperature_high_state_template"] = "{{ value_json.temp_high }}"

    assert await async_setup_component.opp, CLIMATE_DOMAIN, config)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)

    # Temperature - with valid value
    assert state.attributes.get("target_temp_low") is None
    assert state.attributes.get("target_temp_high") is None

    async_fire_mqtt_message(
       .opp, "temperature-state", '{"temp_low": "1031", "temp_high": "1032"}'
    )
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("target_temp_low") == 1031
    assert state.attributes.get("target_temp_high") == 1032

    # Temperature - with invalid value
    async_fire_mqtt_message.opp, "temperature-state", '"-INVALID-"')
    state = opp.states.get(ENTITY_CLIMATE)
    # make sure, the invalid value gets logged...
    assert "Could not parse temperature from" in caplog.text
    # ... but the actual value stays unchanged.
    assert state.attributes.get("target_temp_low") == 1031
    assert state.attributes.get("target_temp_high") == 1032


async def test_get_with_templates.opp, mqtt_mock, caplog):
    """Test getting various attributes with templates."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    # By default, just unquote the JSON-strings
    config["climate"]["value_template"] = "{{ value_json }}"
    config["climate"]["action_template"] = "{{ value_json }}"
    # Something more complicated for hold mode
    config["climate"]["hold_state_template"] = "{{ value_json.attribute }}"
    # Rendering to a bool for aux heat
    config["climate"]["aux_state_template"] = "{{ value == 'switchmeon' }}"

    config["climate"]["action_topic"] = "action"
    config["climate"]["mode_state_topic"] = "mode-state"
    config["climate"]["fan_mode_state_topic"] = "fan-state"
    config["climate"]["swing_mode_state_topic"] = "swing-state"
    config["climate"]["temperature_state_topic"] = "temperature-state"
    config["climate"]["away_mode_state_topic"] = "away-state"
    config["climate"]["hold_state_topic"] = "hold-state"
    config["climate"]["aux_state_topic"] = "aux-state"
    config["climate"]["current_temperature_topic"] = "current-temperature"

    assert await async_setup_component.opp, CLIMATE_DOMAIN, config)
    await.opp.async_block_till_done()

    # Operation Mode
    state = opp.states.get(ENTITY_CLIMATE)
    async_fire_mqtt_message.opp, "mode-state", '"cool"')
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.state == "cool"

    # Fan Mode
    assert state.attributes.get("fan_mode") is None
    async_fire_mqtt_message.opp, "fan-state", '"high"')
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("fan_mode") == "high"

    # Swing Mode
    assert state.attributes.get("swing_mode") is None
    async_fire_mqtt_message.opp, "swing-state", '"on"')
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_mode") == "on"

    # Temperature - with valid value
    assert state.attributes.get("temperature") is None
    async_fire_mqtt_message.opp, "temperature-state", '"1031"')
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("temperature") == 1031

    # Temperature - with invalid value
    async_fire_mqtt_message.opp, "temperature-state", '"-INVALID-"')
    state = opp.states.get(ENTITY_CLIMATE)
    # make sure, the invalid value gets logged...
    assert "Could not parse temperature from -INVALID-" in caplog.text
    # ... but the actual value stays unchanged.
    assert state.attributes.get("temperature") == 1031

    # Away Mode
    assert state.attributes.get("preset_mode") == "none"
    async_fire_mqtt_message.opp, "away-state", '"ON"')
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "away"

    # Away Mode with JSON values
    async_fire_mqtt_message.opp, "away-state", "false")
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "none"

    async_fire_mqtt_message.opp, "away-state", "true")
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "away"

    # Hold Mode
    async_fire_mqtt_message(
       .opp,
        "hold-state",
        """
        { "attribute": "somemode" }
    """,
    )
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == "somemode"

    # Aux mode
    assert state.attributes.get("aux_heat") == "off"
    async_fire_mqtt_message.opp, "aux-state", "switchmeon")
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("aux_heat") == "on"

    # anything other than 'switchmeon' should turn Aux mode off
    async_fire_mqtt_message.opp, "aux-state", "somerandomstring")
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("aux_heat") == "off"

    # Current temperature
    async_fire_mqtt_message.opp, "current-temperature", '"74656"')
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("current_temperature") == 74656

    # Action
    async_fire_mqtt_message.opp, "action", '"cool"')
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("hvac_action") == "cool"


async def test_set_with_templates.opp, mqtt_mock, caplog):
    """Test setting various attributes with templates."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    # Create simple templates
    config["climate"]["fan_mode_command_template"] = "fan_mode: {{ value }}"
    config["climate"]["hold_command_template"] = "hold: {{ value }}"
    config["climate"]["mode_command_template"] = "mode: {{ value }}"
    config["climate"]["swing_mode_command_template"] = "swing_mode: {{ value }}"
    config["climate"]["temperature_command_template"] = "temp: {{ value }}"
    config["climate"]["temperature_high_command_template"] = "temp_hi: {{ value }}"
    config["climate"]["temperature_low_command_template"] = "temp_lo: {{ value }}"

    assert await async_setup_component.opp, CLIMATE_DOMAIN, config)
    await.opp.async_block_till_done()

    # Fan Mode
    await common.async_set_fan_mode.opp, "high", ENTITY_CLIMATE)
    mqtt_mock.async_publish.assert_called_once_with(
        "fan-mode-topic", "fan_mode: high", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("fan_mode") == "high"

    # Hold Mode
    await common.async_set_preset_mode.opp, PRESET_ECO, ENTITY_CLIMATE)
    mqtt_mock.async_publish.assert_called_once_with("hold-topic", "hold: eco", 0, False)
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("preset_mode") == PRESET_ECO

    # Mode
    await common.async_set_hvac_mode.opp, "cool", ENTITY_CLIMATE)
    mqtt_mock.async_publish.assert_called_once_with(
        "mode-topic", "mode: cool", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.state == "cool"

    # Swing Mode
    await common.async_set_swing_mode.opp, "on", ENTITY_CLIMATE)
    mqtt_mock.async_publish.assert_called_once_with(
        "swing-mode-topic", "swing_mode: on", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("swing_mode") == "on"

    # Temperature
    await common.async_set_temperature.opp, temperature=47, entity_id=ENTITY_CLIMATE)
    mqtt_mock.async_publish.assert_called_once_with(
        "temperature-topic", "temp: 47.0", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("temperature") == 47

    # Temperature Low/High
    await common.async_set_temperature(
       .opp, target_temp_low=20, target_temp_high=23, entity_id=ENTITY_CLIMATE
    )
    mqtt_mock.async_publish.assert_any_call(
        "temperature-low-topic", "temp_lo: 20.0", 0, False
    )
    mqtt_mock.async_publish.assert_any_call(
        "temperature-high-topic", "temp_hi: 23.0", 0, False
    )
    mqtt_mock.async_publish.reset_mock()
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("target_temp_low") == 20
    assert state.attributes.get("target_temp_high") == 23


async def test_min_temp_custom.opp, mqtt_mock):
    """Test a custom min temp."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["climate"]["min_temp"] = 26

    assert await async_setup_component.opp, CLIMATE_DOMAIN, config)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)
    min_temp = state.attributes.get("min_temp")

    assert isinstance(min_temp, float)
    assert state.attributes.get("min_temp") == 26


async def test_max_temp_custom.opp, mqtt_mock):
    """Test a custom max temp."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["climate"]["max_temp"] = 60

    assert await async_setup_component.opp, CLIMATE_DOMAIN, config)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)
    max_temp = state.attributes.get("max_temp")

    assert isinstance(max_temp, float)
    assert max_temp == 60


async def test_temp_step_custom.opp, mqtt_mock):
    """Test a custom temp step."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["climate"]["temp_step"] = 0.01

    assert await async_setup_component.opp, CLIMATE_DOMAIN, config)
    await.opp.async_block_till_done()

    state = opp.states.get(ENTITY_CLIMATE)
    temp_step = state.attributes.get("target_temp_step")

    assert isinstance(temp_step, float)
    assert temp_step == 0.01


async def test_temperature_unit.opp, mqtt_mock):
    """Test that setting temperature unit converts temperature values."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["climate"]["temperature_unit"] = "F"
    config["climate"]["current_temperature_topic"] = "current_temperature"

    assert await async_setup_component.opp, CLIMATE_DOMAIN, config)
    await.opp.async_block_till_done()

    async_fire_mqtt_message.opp, "current_temperature", "77")

    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("current_temperature") == 25


async def test_setting_attribute_via_mqtt_json_message.opp, mqtt_mock):
    """Test the setting of attribute via MQTT with JSON payload."""
    await help_test_setting_attribute_via_mqtt_json_message(
       .opp, mqtt_mock, CLIMATE_DOMAIN, DEFAULT_CONFIG
    )


async def test_setting_attribute_with_template.opp, mqtt_mock):
    """Test the setting of attribute via MQTT with JSON payload."""
    await help_test_setting_attribute_with_template(
       .opp, mqtt_mock, CLIMATE_DOMAIN, DEFAULT_CONFIG
    )


async def test_update_with_json_attrs_not_dict.opp, mqtt_mock, caplog):
    """Test attributes get extracted from a JSON result."""
    await help_test_update_with_json_attrs_not_dict(
       .opp, mqtt_mock, caplog, CLIMATE_DOMAIN, DEFAULT_CONFIG
    )


async def test_update_with_json_attrs_bad_JSON.opp, mqtt_mock, caplog):
    """Test attributes get extracted from a JSON result."""
    await help_test_update_with_json_attrs_bad_JSON(
       .opp, mqtt_mock, caplog, CLIMATE_DOMAIN, DEFAULT_CONFIG
    )


async def test_discovery_update_attr.opp, mqtt_mock, caplog):
    """Test update of discovered MQTTAttributes."""
    await help_test_discovery_update_attr(
       .opp, mqtt_mock, caplog, CLIMATE_DOMAIN, DEFAULT_CONFIG
    )


async def test_unique_id.opp, mqtt_mock):
    """Test unique id option only creates one climate per unique_id."""
    config = {
        CLIMATE_DOMAIN: [
            {
                "platform": "mqtt",
                "name": "Test 1",
                "power_state_topic": "test-topic",
                "power_command_topic": "test_topic",
                "unique_id": "TOTALLY_UNIQUE",
            },
            {
                "platform": "mqtt",
                "name": "Test 2",
                "power_state_topic": "test-topic",
                "power_command_topic": "test_topic",
                "unique_id": "TOTALLY_UNIQUE",
            },
        ]
    }
    await help_test_unique_id.opp, mqtt_mock, CLIMATE_DOMAIN, config)


async def test_discovery_removal_climate.opp, mqtt_mock, caplog):
    """Test removal of discovered climate."""
    data = json.dumps(DEFAULT_CONFIG[CLIMATE_DOMAIN])
    await help_test_discovery_removal.opp, mqtt_mock, caplog, CLIMATE_DOMAIN, data)


async def test_discovery_update_climate.opp, mqtt_mock, caplog):
    """Test update of discovered climate."""
    data1 = '{ "name": "Beer" }'
    data2 = '{ "name": "Milk" }'
    await help_test_discovery_update(
       .opp, mqtt_mock, caplog, CLIMATE_DOMAIN, data1, data2
    )


async def test_discovery_update_unchanged_climate.opp, mqtt_mock, caplog):
    """Test update of discovered climate."""
    data1 = '{ "name": "Beer" }'
    with patch(
        "openpeerpower.components.mqtt.climate.MqttClimate.discovery_update"
    ) as discovery_update:
        await help_test_discovery_update_unchanged(
           .opp, mqtt_mock, caplog, CLIMATE_DOMAIN, data1, discovery_update
        )


@pytest.mark.no_fail_on_log_exception
async def test_discovery_broken.opp, mqtt_mock, caplog):
    """Test handling of bad discovery message."""
    data1 = '{ "name": "Beer", "power_command_topic": "test_topic#" }'
    data2 = '{ "name": "Milk", "power_command_topic": "test_topic" }'
    await help_test_discovery_broken(
       .opp, mqtt_mock, caplog, CLIMATE_DOMAIN, data1, data2
    )


async def test_entity_device_info_with_connection.opp, mqtt_mock):
    """Test MQTT climate device registry integration."""
    await help_test_entity_device_info_with_connection(
       .opp, mqtt_mock, CLIMATE_DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_device_info_with_identifier.opp, mqtt_mock):
    """Test MQTT climate device registry integration."""
    await help_test_entity_device_info_with_identifier(
       .opp, mqtt_mock, CLIMATE_DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_device_info_update.opp, mqtt_mock):
    """Test device registry update."""
    await help_test_entity_device_info_update(
       .opp, mqtt_mock, CLIMATE_DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_device_info_remove.opp, mqtt_mock):
    """Test device registry remove."""
    await help_test_entity_device_info_remove(
       .opp, mqtt_mock, CLIMATE_DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_id_update_subscriptions.opp, mqtt_mock):
    """Test MQTT subscriptions are managed when entity_id is updated."""
    config = {
        CLIMATE_DOMAIN: {
            "platform": "mqtt",
            "name": "test",
            "mode_state_topic": "test-topic",
            "availability_topic": "avty-topic",
        }
    }
    await help_test_entity_id_update_subscriptions(
       .opp, mqtt_mock, CLIMATE_DOMAIN, config, ["test-topic", "avty-topic"]
    )


async def test_entity_id_update_discovery_update.opp, mqtt_mock):
    """Test MQTT discovery update when entity_id is updated."""
    await help_test_entity_id_update_discovery_update(
       .opp, mqtt_mock, CLIMATE_DOMAIN, DEFAULT_CONFIG
    )


async def test_entity_debug_info_message.opp, mqtt_mock):
    """Test MQTT debug info."""
    config = {
        CLIMATE_DOMAIN: {
            "platform": "mqtt",
            "name": "test",
            "mode_state_topic": "test-topic",
        }
    }
    await help_test_entity_debug_info_message(
       .opp, mqtt_mock, CLIMATE_DOMAIN, config, "test-topic"
    )


async def test_precision_default.opp, mqtt_mock):
    """Test that setting precision to tenths works as intended."""
    assert await async_setup_component.opp, CLIMATE_DOMAIN, DEFAULT_CONFIG)
    await.opp.async_block_till_done()

    await common.async_set_temperature(
       .opp, temperature=23.67, entity_id=ENTITY_CLIMATE
    )
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("temperature") == 23.7
    mqtt_mock.async_publish.reset_mock()


async def test_precision_halves.opp, mqtt_mock):
    """Test that setting precision to halves works as intended."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["climate"]["precision"] = 0.5
    assert await async_setup_component.opp, CLIMATE_DOMAIN, config)
    await.opp.async_block_till_done()

    await common.async_set_temperature(
       .opp, temperature=23.67, entity_id=ENTITY_CLIMATE
    )
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("temperature") == 23.5
    mqtt_mock.async_publish.reset_mock()


async def test_precision_whole.opp, mqtt_mock):
    """Test that setting precision to whole works as intended."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["climate"]["precision"] = 1.0
    assert await async_setup_component.opp, CLIMATE_DOMAIN, config)
    await.opp.async_block_till_done()

    await common.async_set_temperature(
       .opp, temperature=23.67, entity_id=ENTITY_CLIMATE
    )
    state = opp.states.get(ENTITY_CLIMATE)
    assert state.attributes.get("temperature") == 24.0
    mqtt_mock.async_publish.reset_mock()
