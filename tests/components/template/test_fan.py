"""The tests for the Template fan platform."""
import pytest
import voluptuous as vol

from openpeerpower import setup
from openpeerpower.components.fan import (
    ATTR_DIRECTION,
    ATTR_OSCILLATING,
    ATTR_PERCENTAGE,
    ATTR_PRESET_MODE,
    ATTR_SPEED,
    DIRECTION_FORWARD,
    DIRECTION_REVERSE,
    SPEED_HIGH,
    SPEED_LOW,
    SPEED_MEDIUM,
    SPEED_OFF,
)
from openpeerpower.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE

from tests.common import assert_setup_component, async_mock_service
from tests.components.fan import common

_TEST_FAN = "fan.test_fan"
# Represent for fan's state
_STATE_INPUT_BOOLEAN = "input_boolean.state"
# Represent for fan's state
_STATE_AVAILABILITY_BOOLEAN = "availability_boolean.state"
# Represent for fan's speed
_SPEED_INPUT_SELECT = "input_select.speed"
# Represent for fan's preset mode
_PRESET_MODE_INPUT_SELECT = "input_select.preset_mode"
# Represent for fan's speed percentage
_PERCENTAGE_INPUT_NUMBER = "input_number.percentage"
# Represent for fan's oscillating
_OSC_INPUT = "input_select.osc"
# Represent for fan's direction
_DIRECTION_INPUT_SELECT = "input_select.direction"


@pytest.fixture
def calls.opp):
    """Track calls to a mock service."""
    return async_mock_service.opp, "test", "automation")


# Configuration tests #
async def test_missing_optional_config.opp, calls):
    """Test: missing optional template is ok."""
    with assert_setup_component(1, "fan"):
        assert await setup.async_setup_component(
           .opp,
            "fan",
            {
                "fan": {
                    "platform": "template",
                    "fans": {
                        "test_fan": {
                            "value_template": "{{ 'on' }}",
                            "turn_on": {"service": "script.fan_on"},
                            "turn_off": {"service": "script.fan_off"},
                        }
                    },
                }
            },
        )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    _verify.opp, STATE_ON, None, None, None, None, None)


async def test_missing_value_template_config.opp, calls):
    """Test: missing 'value_template' will fail."""
    with assert_setup_component(0, "fan"):
        assert await setup.async_setup_component(
           .opp,
            "fan",
            {
                "fan": {
                    "platform": "template",
                    "fans": {
                        "test_fan": {
                            "turn_on": {"service": "script.fan_on"},
                            "turn_off": {"service": "script.fan_off"},
                        }
                    },
                }
            },
        )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    assert.opp.states.async_all() == []


async def test_missing_turn_on_config.opp, calls):
    """Test: missing 'turn_on' will fail."""
    with assert_setup_component(0, "fan"):
        assert await setup.async_setup_component(
           .opp,
            "fan",
            {
                "fan": {
                    "platform": "template",
                    "fans": {
                        "test_fan": {
                            "value_template": "{{ 'on' }}",
                            "turn_off": {"service": "script.fan_off"},
                        }
                    },
                }
            },
        )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    assert.opp.states.async_all() == []


async def test_missing_turn_off_config.opp, calls):
    """Test: missing 'turn_off' will fail."""
    with assert_setup_component(0, "fan"):
        assert await setup.async_setup_component(
           .opp,
            "fan",
            {
                "fan": {
                    "platform": "template",
                    "fans": {
                        "test_fan": {
                            "value_template": "{{ 'on' }}",
                            "turn_on": {"service": "script.fan_on"},
                        }
                    },
                }
            },
        )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    assert.opp.states.async_all() == []


async def test_invalid_config.opp, calls):
    """Test: missing 'turn_off' will fail."""
    with assert_setup_component(0, "fan"):
        assert await setup.async_setup_component(
           .opp,
            "fan",
            {
                "platform": "template",
                "fans": {
                    "test_fan": {
                        "value_template": "{{ 'on' }}",
                        "turn_on": {"service": "script.fan_on"},
                    }
                },
            },
        )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    assert.opp.states.async_all() == []


# End of configuration tests #


# Template tests #
async def test_templates_with_entities.opp, calls):
    """Test tempalates with values from other entities."""
    value_template = """
        {% if is_state('input_boolean.state', 'True') %}
            {{ 'on' }}
        {% else %}
            {{ 'off' }}
        {% endif %}
    """

    with assert_setup_component(1, "fan"):
        assert await setup.async_setup_component(
           .opp,
            "fan",
            {
                "fan": {
                    "platform": "template",
                    "fans": {
                        "test_fan": {
                            "value_template": value_template,
                            "percentage_template": "{{ states('input_number.percentage') }}",
                            "speed_template": "{{ states('input_select.speed') }}",
                            "preset_mode_template": "{{ states('input_select.preset_mode') }}",
                            "oscillating_template": "{{ states('input_select.osc') }}",
                            "direction_template": "{{ states('input_select.direction') }}",
                            "speed_count": "3",
                            "set_percentage": {
                                "service": "script.fans_set_speed",
                                "data_template": {"percentage": "{{ percentage }}"},
                            },
                            "turn_on": {"service": "script.fan_on"},
                            "turn_off": {"service": "script.fan_off"},
                        }
                    },
                }
            },
        )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    _verify.opp, STATE_OFF, None, 0, None, None, None)

   .opp.states.async_set(_STATE_INPUT_BOOLEAN, True)
   .opp.states.async_set(_SPEED_INPUT_SELECT, SPEED_MEDIUM)
   .opp.states.async_set(_OSC_INPUT, "True")
   .opp.states.async_set(_DIRECTION_INPUT_SELECT, DIRECTION_FORWARD)
    await.opp.async_block_till_done()

    _verify.opp, STATE_ON, SPEED_MEDIUM, 66, True, DIRECTION_FORWARD, None)

   .opp.states.async_set(_PERCENTAGE_INPUT_NUMBER, 33)
    await.opp.async_block_till_done()
    _verify.opp, STATE_ON, SPEED_LOW, 33, True, DIRECTION_FORWARD, None)

   .opp.states.async_set(_PERCENTAGE_INPUT_NUMBER, 66)
    await.opp.async_block_till_done()
    _verify.opp, STATE_ON, SPEED_MEDIUM, 66, True, DIRECTION_FORWARD, None)

   .opp.states.async_set(_PERCENTAGE_INPUT_NUMBER, 100)
    await.opp.async_block_till_done()
    _verify.opp, STATE_ON, SPEED_HIGH, 100, True, DIRECTION_FORWARD, None)

   .opp.states.async_set(_PERCENTAGE_INPUT_NUMBER, "dog")
    await.opp.async_block_till_done()
    _verify.opp, STATE_ON, None, 0, True, DIRECTION_FORWARD, None)


async def test_templates_with_entities_and_invalid_percentage.opp, calls):
    """Test templates with values from other entities."""
   .opp.states.async_set("sensor.percentage", "0")

    with assert_setup_component(1, "fan"):
        assert await setup.async_setup_component(
           .opp,
            "fan",
            {
                "fan": {
                    "platform": "template",
                    "fans": {
                        "test_fan": {
                            "value_template": "{{ 'on' }}",
                            "percentage_template": "{{ states('sensor.percentage') }}",
                            "turn_on": {"service": "script.fan_on"},
                            "turn_off": {"service": "script.fan_off"},
                        },
                    },
                }
            },
        )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    _verify.opp, STATE_OFF, SPEED_OFF, 0, None, None, None)

   .opp.states.async_set("sensor.percentage", "33")
    await.opp.async_block_till_done()

    _verify.opp, STATE_ON, SPEED_LOW, 33, None, None, None)

   .opp.states.async_set("sensor.percentage", "invalid")
    await.opp.async_block_till_done()

    _verify.opp, STATE_ON, None, 0, None, None, None)

   .opp.states.async_set("sensor.percentage", "5000")
    await.opp.async_block_till_done()

    _verify.opp, STATE_ON, None, 0, None, None, None)

   .opp.states.async_set("sensor.percentage", "100")
    await.opp.async_block_till_done()

    _verify.opp, STATE_ON, SPEED_HIGH, 100, None, None, None)

   .opp.states.async_set("sensor.percentage", "0")
    await.opp.async_block_till_done()

    _verify.opp, STATE_OFF, SPEED_OFF, 0, None, None, None)


async def test_templates_with_entities_and_preset_modes.opp, calls):
    """Test templates with values from other entities."""
   .opp.states.async_set("sensor.preset_mode", "0")

    with assert_setup_component(1, "fan"):
        assert await setup.async_setup_component(
           .opp,
            "fan",
            {
                "fan": {
                    "platform": "template",
                    "fans": {
                        "test_fan": {
                            "value_template": "{{ 'on' }}",
                            "preset_modes": ["auto", "smart"],
                            "preset_mode_template": "{{ states('sensor.preset_mode') }}",
                            "turn_on": {"service": "script.fan_on"},
                            "turn_off": {"service": "script.fan_off"},
                        },
                    },
                }
            },
        )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    _verify.opp, STATE_ON, None, None, None, None, None)

   .opp.states.async_set("sensor.preset_mode", "invalid")
    await.opp.async_block_till_done()

    _verify.opp, STATE_ON, None, None, None, None, None)

   .opp.states.async_set("sensor.preset_mode", "auto")
    await.opp.async_block_till_done()

    _verify.opp, STATE_ON, "auto", None, None, None, "auto")

   .opp.states.async_set("sensor.preset_mode", "smart")
    await.opp.async_block_till_done()

    _verify.opp, STATE_ON, "smart", None, None, None, "smart")

   .opp.states.async_set("sensor.preset_mode", "invalid")
    await.opp.async_block_till_done()
    _verify.opp, STATE_ON, None, None, None, None, None)


async def test_template_with_unavailable_entities.opp, calls):
    """Test unavailability with value_template."""

    with assert_setup_component(1, "fan"):
        assert await setup.async_setup_component(
           .opp,
            "fan",
            {
                "fan": {
                    "platform": "template",
                    "fans": {
                        "test_fan": {
                            "value_template": "{{ 'unavailable' }}",
                            "turn_on": {"service": "script.fan_on"},
                            "turn_off": {"service": "script.fan_off"},
                        }
                    },
                }
            },
        )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()
    assert.opp.states.get(_TEST_FAN).state == STATE_OFF


async def test_template_with_unavailable_parameters.opp, calls):
    """Test unavailability of speed, direction and oscillating parameters."""

    with assert_setup_component(1, "fan"):
        assert await setup.async_setup_component(
           .opp,
            "fan",
            {
                "fan": {
                    "platform": "template",
                    "fans": {
                        "test_fan": {
                            "value_template": "{{ 'on' }}",
                            "speed_template": "{{ 'unavailable' }}",
                            "oscillating_template": "{{ 'unavailable' }}",
                            "direction_template": "{{ 'unavailable' }}",
                            "turn_on": {"service": "script.fan_on"},
                            "turn_off": {"service": "script.fan_off"},
                        }
                    },
                }
            },
        )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    _verify.opp, STATE_ON, None, 0, None, None, None)


async def test_availability_template_with_entities.opp, calls):
    """Test availability tempalates with values from other entities."""

    with assert_setup_component(1, "fan"):
        assert await setup.async_setup_component(
           .opp,
            "fan",
            {
                "fan": {
                    "platform": "template",
                    "fans": {
                        "test_fan": {
                            "availability_template": "{{ is_state('availability_boolean.state', 'on') }}",
                            "value_template": "{{ 'on' }}",
                            "speed_template": "{{ 'medium' }}",
                            "oscillating_template": "{{ 1 == 1 }}",
                            "direction_template": "{{ 'forward' }}",
                            "turn_on": {"service": "script.fan_on"},
                            "turn_off": {"service": "script.fan_off"},
                        }
                    },
                }
            },
        )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    # When template returns true..
   .opp.states.async_set(_STATE_AVAILABILITY_BOOLEAN, STATE_ON)
    await.opp.async_block_till_done()

    # Device State should not be unavailable
    assert.opp.states.get(_TEST_FAN).state != STATE_UNAVAILABLE

    # When Availability template returns false
   .opp.states.async_set(_STATE_AVAILABILITY_BOOLEAN, STATE_OFF)
    await.opp.async_block_till_done()

    # device state should be unavailable
    assert.opp.states.get(_TEST_FAN).state == STATE_UNAVAILABLE


async def test_templates_with_valid_values.opp, calls):
    """Test templates with valid values."""
    with assert_setup_component(1, "fan"):
        assert await setup.async_setup_component(
           .opp,
            "fan",
            {
                "fan": {
                    "platform": "template",
                    "fans": {
                        "test_fan": {
                            "value_template": "{{ 'on' }}",
                            "speed_template": "{{ 'medium' }}",
                            "oscillating_template": "{{ 1 == 1 }}",
                            "direction_template": "{{ 'forward' }}",
                            "turn_on": {"service": "script.fan_on"},
                            "turn_off": {"service": "script.fan_off"},
                        }
                    },
                }
            },
        )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    _verify.opp, STATE_ON, SPEED_MEDIUM, 66, True, DIRECTION_FORWARD, None)


async def test_templates_invalid_values.opp, calls):
    """Test templates with invalid values."""
    with assert_setup_component(1, "fan"):
        assert await setup.async_setup_component(
           .opp,
            "fan",
            {
                "fan": {
                    "platform": "template",
                    "fans": {
                        "test_fan": {
                            "value_template": "{{ 'abc' }}",
                            "speed_template": "{{ '0' }}",
                            "oscillating_template": "{{ 'xyz' }}",
                            "direction_template": "{{ 'right' }}",
                            "turn_on": {"service": "script.fan_on"},
                            "turn_off": {"service": "script.fan_off"},
                        }
                    },
                }
            },
        )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    _verify.opp, STATE_OFF, None, 0, None, None, None)


async def test_invalid_availability_template_keeps_component_available.opp, caplog):
    """Test that an invalid availability keeps the device available."""

    with assert_setup_component(1, "fan"):
        assert await setup.async_setup_component(
           .opp,
            "fan",
            {
                "fan": {
                    "platform": "template",
                    "fans": {
                        "test_fan": {
                            "value_template": "{{ 'on' }}",
                            "availability_template": "{{ x - 12 }}",
                            "speed_template": "{{ states('input_select.speed') }}",
                            "preset_mode_template": "{{ states('input_select.preset_mode') }}",
                            "oscillating_template": "{{ states('input_select.osc') }}",
                            "direction_template": "{{ states('input_select.direction') }}",
                            "turn_on": {"service": "script.fan_on"},
                            "turn_off": {"service": "script.fan_off"},
                        }
                    },
                }
            },
        )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    assert.opp.states.get("fan.test_fan").state != STATE_UNAVAILABLE

    assert "TemplateError" in caplog.text
    assert "x" in caplog.text


# End of template tests #


# Function tests #
async def test_on_off.opp, calls):
    """Test turn on and turn off."""
    await _register_components.opp)

    # Turn on fan
    await common.async_turn_on.opp, _TEST_FAN)

    # verify
    assert.opp.states.get(_STATE_INPUT_BOOLEAN).state == STATE_ON
    _verify.opp, STATE_ON, None, 0, None, None, None)

    # Turn off fan
    await common.async_turn_off.opp, _TEST_FAN)

    # verify
    assert.opp.states.get(_STATE_INPUT_BOOLEAN).state == STATE_OFF
    _verify.opp, STATE_OFF, None, 0, None, None, None)


async def test_on_with_speed.opp, calls):
    """Test turn on with speed."""
    await _register_components.opp)

    # Turn on fan with high speed
    await common.async_turn_on.opp, _TEST_FAN, SPEED_HIGH)

    # verify
    assert.opp.states.get(_STATE_INPUT_BOOLEAN).state == STATE_ON
    assert int(float.opp.states.get(_PERCENTAGE_INPUT_NUMBER).state)) == 100
    _verify.opp, STATE_ON, SPEED_HIGH, 100, None, None, None)


async def test_set_speed.opp, calls):
    """Test set valid speed."""
    await _register_components.opp, preset_modes=["auto", "smart"])

    # Turn on fan
    await common.async_turn_on.opp, _TEST_FAN)

    # Set fan's speed to high
    await common.async_set_speed.opp, _TEST_FAN, SPEED_HIGH)

    # verify
    assert.opp.states.get(_SPEED_INPUT_SELECT).state == SPEED_HIGH
    _verify.opp, STATE_ON, SPEED_HIGH, 100, None, None, None)

    # Set fan's speed to medium
    await common.async_set_speed.opp, _TEST_FAN, SPEED_MEDIUM)

    # verify
    assert.opp.states.get(_SPEED_INPUT_SELECT).state == SPEED_MEDIUM
    _verify.opp, STATE_ON, SPEED_MEDIUM, 66, None, None, None)

    # Set fan's speed to off
    await common.async_set_speed.opp, _TEST_FAN, SPEED_OFF)

    # verify
    assert.opp.states.get(_SPEED_INPUT_SELECT).state == SPEED_OFF
    _verify.opp, STATE_OFF, SPEED_OFF, 0, None, None, None)


async def test_set_percentage.opp, calls):
    """Test set valid speed percentage."""
    await _register_components.opp)

    # Turn on fan
    await common.async_turn_on.opp, _TEST_FAN)

    # Set fan's percentage speed to 100
    await common.async_set_percentage.opp, _TEST_FAN, 100)

    # verify
    assert int(float.opp.states.get(_PERCENTAGE_INPUT_NUMBER).state)) == 100

    _verify.opp, STATE_ON, SPEED_HIGH, 100, None, None, None)

    # Set fan's percentage speed to 66
    await common.async_set_percentage.opp, _TEST_FAN, 66)
    assert int(float.opp.states.get(_PERCENTAGE_INPUT_NUMBER).state)) == 66

    _verify.opp, STATE_ON, SPEED_MEDIUM, 66, None, None, None)

    # Set fan's percentage speed to 0
    await common.async_set_percentage.opp, _TEST_FAN, 0)
    assert int(float.opp.states.get(_PERCENTAGE_INPUT_NUMBER).state)) == 0

    _verify.opp, STATE_OFF, SPEED_OFF, 0, None, None, None)

    # Set fan's percentage speed to 50
    await common.async_turn_on.opp, _TEST_FAN, percentage=50)
    assert int(float.opp.states.get(_PERCENTAGE_INPUT_NUMBER).state)) == 50

    _verify.opp, STATE_ON, SPEED_MEDIUM, 50, None, None, None)


async def test_increase_decrease_speed.opp, calls):
    """Test set valid increase and derease speed."""
    await _register_components.opp)

    # Turn on fan
    await common.async_turn_on.opp, _TEST_FAN)

    # Set fan's percentage speed to 100
    await common.async_set_percentage.opp, _TEST_FAN, 100)

    # verify
    assert int(float.opp.states.get(_PERCENTAGE_INPUT_NUMBER).state)) == 100

    _verify.opp, STATE_ON, SPEED_HIGH, 100, None, None, None)

    # Set fan's percentage speed to 66
    await common.async_decrease_speed.opp, _TEST_FAN)
    assert int(float.opp.states.get(_PERCENTAGE_INPUT_NUMBER).state)) == 66

    _verify.opp, STATE_ON, SPEED_MEDIUM, 66, None, None, None)

    # Set fan's percentage speed to 33
    await common.async_decrease_speed.opp, _TEST_FAN)
    assert int(float.opp.states.get(_PERCENTAGE_INPUT_NUMBER).state)) == 33

    _verify.opp, STATE_ON, SPEED_LOW, 33, None, None, None)

    # Set fan's percentage speed to 0
    await common.async_decrease_speed.opp, _TEST_FAN)
    assert int(float.opp.states.get(_PERCENTAGE_INPUT_NUMBER).state)) == 0

    _verify.opp, STATE_OFF, SPEED_OFF, 0, None, None, None)

    # Set fan's percentage speed to 33
    await common.async_increase_speed.opp, _TEST_FAN)
    assert int(float.opp.states.get(_PERCENTAGE_INPUT_NUMBER).state)) == 33

    _verify.opp, STATE_ON, SPEED_LOW, 33, None, None, None)


async def test_set_invalid_speed_from_initial_stage.opp, calls):
    """Test set invalid speed when fan is in initial state."""
    await _register_components.opp)

    # Turn on fan
    await common.async_turn_on.opp, _TEST_FAN)

    # Set fan's speed to 'invalid'
    await common.async_set_speed.opp, _TEST_FAN, "invalid")

    # verify speed is unchanged
    assert.opp.states.get(_SPEED_INPUT_SELECT).state == ""
    _verify.opp, STATE_ON, None, 0, None, None, None)


async def test_set_invalid_speed.opp, calls):
    """Test set invalid speed when fan has valid speed."""
    await _register_components.opp)

    # Turn on fan
    await common.async_turn_on.opp, _TEST_FAN)

    # Set fan's speed to high
    await common.async_set_speed.opp, _TEST_FAN, SPEED_HIGH)

    # verify
    assert.opp.states.get(_SPEED_INPUT_SELECT).state == SPEED_HIGH
    _verify.opp, STATE_ON, SPEED_HIGH, 100, None, None, None)

    # Set fan's speed to 'invalid'
    await common.async_set_speed.opp, _TEST_FAN, "invalid")

    # verify speed is unchanged
    assert.opp.states.get(_SPEED_INPUT_SELECT).state == SPEED_HIGH
    _verify.opp, STATE_ON, SPEED_HIGH, 100, None, None, None)


async def test_custom_speed_list.opp, calls):
    """Test set custom speed list."""
    await _register_components.opp, ["1", "2", "3"])

    # Turn on fan
    await common.async_turn_on.opp, _TEST_FAN)

    # Set fan's speed to '1'
    await common.async_set_speed.opp, _TEST_FAN, "1")

    # verify
    assert.opp.states.get(_SPEED_INPUT_SELECT).state == "1"
    _verify.opp, STATE_ON, "1", 33, None, None, None)

    # Set fan's speed to 'medium' which is invalid
    await common.async_set_speed.opp, _TEST_FAN, SPEED_MEDIUM)

    # verify that speed is unchanged
    assert.opp.states.get(_SPEED_INPUT_SELECT).state == "1"
    _verify.opp, STATE_ON, "1", 33, None, None, None)


async def test_preset_modes.opp, calls):
    """Test preset_modes."""
    await _register_components(
       .opp, ["off", "low", "medium", "high", "auto", "smart"], ["auto", "smart"]
    )

    # Turn on fan
    await common.async_turn_on.opp, _TEST_FAN)

    # Set fan's preset_mode to "auto"
    await common.async_set_preset_mode.opp, _TEST_FAN, "auto")

    # verify
    assert.opp.states.get(_PRESET_MODE_INPUT_SELECT).state == "auto"

    # Set fan's preset_mode to "smart"
    await common.async_set_preset_mode.opp, _TEST_FAN, "smart")

    # Verify fan's preset_mode is "smart"
    assert.opp.states.get(_PRESET_MODE_INPUT_SELECT).state == "smart"

    # Set fan's preset_mode to "invalid"
    await common.async_set_preset_mode.opp, _TEST_FAN, "invalid")

    # Verify fan's preset_mode is still "smart"
    assert.opp.states.get(_PRESET_MODE_INPUT_SELECT).state == "smart"

    # Set fan's preset_mode to "auto"
    await common.async_turn_on.opp, _TEST_FAN, preset_mode="auto")

    # verify
    assert.opp.states.get(_PRESET_MODE_INPUT_SELECT).state == "auto"


async def test_set_osc.opp, calls):
    """Test set oscillating."""
    await _register_components.opp)

    # Turn on fan
    await common.async_turn_on.opp, _TEST_FAN)

    # Set fan's osc to True
    await common.async_oscillate.opp, _TEST_FAN, True)

    # verify
    assert.opp.states.get(_OSC_INPUT).state == "True"
    _verify.opp, STATE_ON, None, 0, True, None, None)

    # Set fan's osc to False
    await common.async_oscillate.opp, _TEST_FAN, False)

    # verify
    assert.opp.states.get(_OSC_INPUT).state == "False"
    _verify.opp, STATE_ON, None, 0, False, None, None)


async def test_set_invalid_osc_from_initial_state.opp, calls):
    """Test set invalid oscillating when fan is in initial state."""
    await _register_components.opp)

    # Turn on fan
    await common.async_turn_on.opp, _TEST_FAN)

    # Set fan's osc to 'invalid'
    with pytest.raises(vol.Invalid):
        await common.async_oscillate.opp, _TEST_FAN, "invalid")

    # verify
    assert.opp.states.get(_OSC_INPUT).state == ""
    _verify.opp, STATE_ON, None, 0, None, None, None)


async def test_set_invalid_osc.opp, calls):
    """Test set invalid oscillating when fan has valid osc."""
    await _register_components.opp)

    # Turn on fan
    await common.async_turn_on.opp, _TEST_FAN)

    # Set fan's osc to True
    await common.async_oscillate.opp, _TEST_FAN, True)

    # verify
    assert.opp.states.get(_OSC_INPUT).state == "True"
    _verify.opp, STATE_ON, None, 0, True, None, None)

    # Set fan's osc to None
    with pytest.raises(vol.Invalid):
        await common.async_oscillate.opp, _TEST_FAN, None)

    # verify osc is unchanged
    assert.opp.states.get(_OSC_INPUT).state == "True"
    _verify.opp, STATE_ON, None, 0, True, None, None)


async def test_set_direction.opp, calls):
    """Test set valid direction."""
    await _register_components.opp)

    # Turn on fan
    await common.async_turn_on.opp, _TEST_FAN)

    # Set fan's direction to forward
    await common.async_set_direction.opp, _TEST_FAN, DIRECTION_FORWARD)

    # verify
    assert.opp.states.get(_DIRECTION_INPUT_SELECT).state == DIRECTION_FORWARD
    _verify.opp, STATE_ON, None, 0, None, DIRECTION_FORWARD, None)

    # Set fan's direction to reverse
    await common.async_set_direction.opp, _TEST_FAN, DIRECTION_REVERSE)

    # verify
    assert.opp.states.get(_DIRECTION_INPUT_SELECT).state == DIRECTION_REVERSE
    _verify.opp, STATE_ON, None, 0, None, DIRECTION_REVERSE, None)


async def test_set_invalid_direction_from_initial_stage.opp, calls):
    """Test set invalid direction when fan is in initial state."""
    await _register_components.opp)

    # Turn on fan
    await common.async_turn_on.opp, _TEST_FAN)

    # Set fan's direction to 'invalid'
    await common.async_set_direction.opp, _TEST_FAN, "invalid")

    # verify direction is unchanged
    assert.opp.states.get(_DIRECTION_INPUT_SELECT).state == ""
    _verify.opp, STATE_ON, None, 0, None, None, None)


async def test_set_invalid_direction.opp, calls):
    """Test set invalid direction when fan has valid direction."""
    await _register_components.opp)

    # Turn on fan
    await common.async_turn_on.opp, _TEST_FAN)

    # Set fan's direction to forward
    await common.async_set_direction.opp, _TEST_FAN, DIRECTION_FORWARD)

    # verify
    assert.opp.states.get(_DIRECTION_INPUT_SELECT).state == DIRECTION_FORWARD
    _verify.opp, STATE_ON, None, 0, None, DIRECTION_FORWARD, None)

    # Set fan's direction to 'invalid'
    await common.async_set_direction.opp, _TEST_FAN, "invalid")

    # verify direction is unchanged
    assert.opp.states.get(_DIRECTION_INPUT_SELECT).state == DIRECTION_FORWARD
    _verify.opp, STATE_ON, None, 0, None, DIRECTION_FORWARD, None)


def _verify(
   .opp,
    expected_state,
    expected_speed,
    expected_percentage,
    expected_oscillating,
    expected_direction,
    expected_preset_mode,
):
    """Verify fan's state, speed and osc."""
    state =.opp.states.get(_TEST_FAN)
    attributes = state.attributes
    assert state.state == str(expected_state)
    assert attributes.get(ATTR_SPEED) == expected_speed
    assert attributes.get(ATTR_PERCENTAGE) == expected_percentage
    assert attributes.get(ATTR_OSCILLATING) == expected_oscillating
    assert attributes.get(ATTR_DIRECTION) == expected_direction
    assert attributes.get(ATTR_PRESET_MODE) == expected_preset_mode


async def _register_components.opp, speed_list=None, preset_modes=None):
    """Register basic components for testing."""
    with assert_setup_component(1, "input_boolean"):
        assert await setup.async_setup_component(
           .opp, "input_boolean", {"input_boolean": {"state": None}}
        )

    with assert_setup_component(1, "input_number"):
        assert await setup.async_setup_component(
           .opp,
            "input_number",
            {
                "input_number": {
                    "percentage": {
                        "min": 0.0,
                        "max": 100.0,
                        "name": "Percentage",
                        "step": 1.0,
                        "mode": "slider",
                    }
                }
            },
        )

    with assert_setup_component(4, "input_select"):
        assert await setup.async_setup_component(
           .opp,
            "input_select",
            {
                "input_select": {
                    "speed": {
                        "name": "Speed",
                        "options": [
                            "",
                            SPEED_OFF,
                            SPEED_LOW,
                            SPEED_MEDIUM,
                            SPEED_HIGH,
                            "1",
                            "2",
                            "3",
                            "auto",
                            "smart",
                        ],
                    },
                    "preset_mode": {
                        "name": "Preset Mode",
                        "options": ["auto", "smart"],
                    },
                    "osc": {"name": "oscillating", "options": ["", "True", "False"]},
                    "direction": {
                        "name": "Direction",
                        "options": ["", DIRECTION_FORWARD, DIRECTION_REVERSE],
                    },
                }
            },
        )

    with assert_setup_component(1, "fan"):
        value_template = """
        {% if is_state('input_boolean.state', 'on') %}
            {{ 'on' }}
        {% else %}
            {{ 'off' }}
        {% endif %}
        """

        test_fan_config = {
            "value_template": value_template,
            "speed_template": "{{ states('input_select.speed') }}",
            "preset_mode_template": "{{ states('input_select.preset_mode') }}",
            "percentage_template": "{{ states('input_number.percentage') }}",
            "oscillating_template": "{{ states('input_select.osc') }}",
            "direction_template": "{{ states('input_select.direction') }}",
            "turn_on": {
                "service": "input_boolean.turn_on",
                "entity_id": _STATE_INPUT_BOOLEAN,
            },
            "turn_off": {
                "service": "input_boolean.turn_off",
                "entity_id": _STATE_INPUT_BOOLEAN,
            },
            "set_speed": {
                "service": "input_select.select_option",
                "data_template": {
                    "entity_id": _SPEED_INPUT_SELECT,
                    "option": "{{ speed }}",
                },
            },
            "set_preset_mode": {
                "service": "input_select.select_option",
                "data_template": {
                    "entity_id": _PRESET_MODE_INPUT_SELECT,
                    "option": "{{ preset_mode }}",
                },
            },
            "set_percentage": {
                "service": "input_number.set_value",
                "data_template": {
                    "entity_id": _PERCENTAGE_INPUT_NUMBER,
                    "value": "{{ percentage }}",
                },
            },
            "set_oscillating": {
                "service": "input_select.select_option",
                "data_template": {
                    "entity_id": _OSC_INPUT,
                    "option": "{{ oscillating }}",
                },
            },
            "set_direction": {
                "service": "input_select.select_option",
                "data_template": {
                    "entity_id": _DIRECTION_INPUT_SELECT,
                    "option": "{{ direction }}",
                },
            },
        }

        if speed_list:
            test_fan_config["speeds"] = speed_list

        if preset_modes:
            test_fan_config["preset_modes"] = preset_modes

        assert await setup.async_setup_component(
           .opp,
            "fan",
            {"fan": {"platform": "template", "fans": {"test_fan": test_fan_config}}},
        )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()


async def test_unique_id.opp):
    """Test unique_id option only creates one fan per id."""
    await setup.async_setup_component(
       .opp,
        "fan",
        {
            "fan": {
                "platform": "template",
                "fans": {
                    "test_template_fan_01": {
                        "unique_id": "not-so-unique-anymore",
                        "value_template": "{{ true }}",
                        "turn_on": {
                            "service": "fan.turn_on",
                            "entity_id": "fan.test_state",
                        },
                        "turn_off": {
                            "service": "fan.turn_off",
                            "entity_id": "fan.test_state",
                        },
                    },
                    "test_template_fan_02": {
                        "unique_id": "not-so-unique-anymore",
                        "value_template": "{{ false }}",
                        "turn_on": {
                            "service": "fan.turn_on",
                            "entity_id": "fan.test_state",
                        },
                        "turn_off": {
                            "service": "fan.turn_off",
                            "entity_id": "fan.test_state",
                        },
                    },
                },
            },
        },
    )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    assert len.opp.states.async_all()) == 1
