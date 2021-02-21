"""The tests for the Template Binary sensor platform."""
from datetime import timedelta
import logging
from unittest.mock import patch

from openpeerpower import setup
from openpeerpower.components import binary_sensor
from openpeerpower.const import (
    ATTR_DEVICE_CLASS,
    EVENT_OPENPEERPOWER_START,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from openpeerpowerr.core import CoreState
import openpeerpowerr.util.dt as dt_util

from tests.common import assert_setup_component, async_fire_time_changed


async def test_setup.opp):
    """Test the setup."""
    config = {
        "binary_sensor": {
            "platform": "template",
            "sensors": {
                "test": {
                    "friendly_name": "virtual thingy",
                    "value_template": "{{ foo }}",
                    "device_class": "motion",
                }
            },
        }
    }
    with assert_setup_component(1):
        assert await setup.async_setup_component.opp, binary_sensor.DOMAIN, config)


async def test_setup_no_sensors.opp):
    """Test setup with no sensors."""
    with assert_setup_component(0):
        assert await setup.async_setup_component(
           .opp, binary_sensor.DOMAIN, {"binary_sensor": {"platform": "template"}}
        )


async def test_setup_invalid_device.opp):
    """Test the setup with invalid devices."""
    with assert_setup_component(0):
        assert await setup.async_setup_component(
           .opp,
            binary_sensor.DOMAIN,
            {"binary_sensor": {"platform": "template", "sensors": {"foo bar": {}}}},
        )


async def test_setup_invalid_device_class.opp):
    """Test setup with invalid sensor class."""
    with assert_setup_component(0):
        assert await setup.async_setup_component(
           .opp,
            binary_sensor.DOMAIN,
            {
                "binary_sensor": {
                    "platform": "template",
                    "sensors": {
                        "test": {
                            "value_template": "{{ foo }}",
                            "device_class": "foobarnotreal",
                        }
                    },
                }
            },
        )


async def test_setup_invalid_missing_template.opp):
    """Test setup with invalid and missing template."""
    with assert_setup_component(0):
        assert await setup.async_setup_component(
           .opp,
            binary_sensor.DOMAIN,
            {
                "binary_sensor": {
                    "platform": "template",
                    "sensors": {"test": {"device_class": "motion"}},
                }
            },
        )


async def test_icon_template.opp):
    """Test icon template."""
    with assert_setup_component(1):
        assert await setup.async_setup_component(
           .opp,
            binary_sensor.DOMAIN,
            {
                "binary_sensor": {
                    "platform": "template",
                    "sensors": {
                        "test_template_sensor": {
                            "value_template": "{{ states.sensor.xyz.state }}",
                            "icon_template": "{% if "
                            "states.binary_sensor.test_state.state == "
                            "'Works' %}"
                            "mdi:check"
                            "{% endif %}",
                        }
                    },
                }
            },
        )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test_template_sensor")
    assert state.attributes.get("icon") == ""

   .opp.states.async_set("binary_sensor.test_state", "Works")
    await.opp.async_block_till_done()
    state = opp.states.get("binary_sensor.test_template_sensor")
    assert state.attributes["icon"] == "mdi:check"


async def test_entity_picture_template.opp):
    """Test entity_picture template."""
    with assert_setup_component(1):
        assert await setup.async_setup_component(
           .opp,
            binary_sensor.DOMAIN,
            {
                "binary_sensor": {
                    "platform": "template",
                    "sensors": {
                        "test_template_sensor": {
                            "value_template": "{{ states.sensor.xyz.state }}",
                            "entity_picture_template": "{% if "
                            "states.binary_sensor.test_state.state == "
                            "'Works' %}"
                            "/local/sensor.png"
                            "{% endif %}",
                        }
                    },
                }
            },
        )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test_template_sensor")
    assert state.attributes.get("entity_picture") == ""

   .opp.states.async_set("binary_sensor.test_state", "Works")
    await.opp.async_block_till_done()
    state = opp.states.get("binary_sensor.test_template_sensor")
    assert state.attributes["entity_picture"] == "/local/sensor.png"


async def test_attribute_templates.opp):
    """Test attribute_templates template."""
    with assert_setup_component(1):
        assert await setup.async_setup_component(
           .opp,
            binary_sensor.DOMAIN,
            {
                "binary_sensor": {
                    "platform": "template",
                    "sensors": {
                        "test_template_sensor": {
                            "value_template": "{{ states.sensor.xyz.state }}",
                            "attribute_templates": {
                                "test_attribute": "It {{ states.sensor.test_state.state }}."
                            },
                        }
                    },
                }
            },
        )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test_template_sensor")
    assert state.attributes.get("test_attribute") == "It ."
   .opp.states.async_set("sensor.test_state", "Works2")
    await.opp.async_block_till_done()
   .opp.states.async_set("sensor.test_state", "Works")
    await.opp.async_block_till_done()
    state = opp.states.get("binary_sensor.test_template_sensor")
    assert state.attributes["test_attribute"] == "It Works."


async def test_match_all.opp):
    """Test template that is rerendered on any state lifecycle."""
    with patch(
        "openpeerpower.components.template.binary_sensor."
        "BinarySensorTemplate._update_state"
    ) as _update_state:
        with assert_setup_component(1):
            assert await setup.async_setup_component(
               .opp,
                binary_sensor.DOMAIN,
                {
                    "binary_sensor": {
                        "platform": "template",
                        "sensors": {
                            "match_all_template_sensor": {
                                "value_template": (
                                    "{% for state in states %}"
                                    "{% if state.entity_id == 'sensor.humidity' %}"
                                    "{{ state.entity_id }}={{ state.state }}"
                                    "{% endif %}"
                                    "{% endfor %}"
                                ),
                            },
                        },
                    }
                },
            )

            await.opp.async_start()
            await.opp.async_block_till_done()
            init_calls = len(_update_state.mock_calls)

           .opp.states.async_set("sensor.any_state", "update")
            await.opp.async_block_till_done()
            assert len(_update_state.mock_calls) == init_calls


async def test_event.opp):
    """Test the event."""
    config = {
        "binary_sensor": {
            "platform": "template",
            "sensors": {
                "test": {
                    "friendly_name": "virtual thingy",
                    "value_template": "{{ states.sensor.test_state.state == 'on' }}",
                    "device_class": "motion",
                }
            },
        }
    }
    with assert_setup_component(1):
        assert await setup.async_setup_component.opp, binary_sensor.DOMAIN, config)

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "off"

   .opp.states.async_set("sensor.test_state", "on")
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "on"


async def test_template_delay_on.opp):
    """Test binary sensor template delay on."""
    config = {
        "binary_sensor": {
            "platform": "template",
            "sensors": {
                "test": {
                    "friendly_name": "virtual thingy",
                    "value_template": "{{ states.sensor.test_state.state == 'on' }}",
                    "device_class": "motion",
                    "delay_on": 5,
                }
            },
        }
    }
    await setup.async_setup_component.opp, binary_sensor.DOMAIN, config)
    await.opp.async_block_till_done()
    await.opp.async_start()

   .opp.states.async_set("sensor.test_state", "on")
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "off"

    future = dt_util.utcnow() + timedelta(seconds=5)
    async_fire_time_changed.opp, future)
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "on"

    # check with time changes
   .opp.states.async_set("sensor.test_state", "off")
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "off"

   .opp.states.async_set("sensor.test_state", "on")
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "off"

   .opp.states.async_set("sensor.test_state", "off")
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "off"

    future = dt_util.utcnow() + timedelta(seconds=5)
    async_fire_time_changed.opp, future)
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "off"


async def test_template_delay_off.opp):
    """Test binary sensor template delay off."""
    config = {
        "binary_sensor": {
            "platform": "template",
            "sensors": {
                "test": {
                    "friendly_name": "virtual thingy",
                    "value_template": "{{ states.sensor.test_state.state == 'on' }}",
                    "device_class": "motion",
                    "delay_off": 5,
                }
            },
        }
    }
   .opp.states.async_set("sensor.test_state", "on")
    await setup.async_setup_component.opp, binary_sensor.DOMAIN, config)
    await.opp.async_block_till_done()
    await.opp.async_start()

   .opp.states.async_set("sensor.test_state", "off")
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "on"

    future = dt_util.utcnow() + timedelta(seconds=5)
    async_fire_time_changed.opp, future)
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "off"

    # check with time changes
   .opp.states.async_set("sensor.test_state", "on")
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "on"

   .opp.states.async_set("sensor.test_state", "off")
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "on"

   .opp.states.async_set("sensor.test_state", "on")
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "on"

    future = dt_util.utcnow() + timedelta(seconds=5)
    async_fire_time_changed.opp, future)
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "on"


async def test_template_with_templated_delay_on.opp):
    """Test binary sensor template with template delay on."""
    config = {
        "binary_sensor": {
            "platform": "template",
            "sensors": {
                "test": {
                    "friendly_name": "virtual thingy",
                    "value_template": "{{ states.sensor.test_state.state == 'on' }}",
                    "device_class": "motion",
                    "delay_on": '{{ ({ "seconds": 6 / 2 }) }}',
                }
            },
        }
    }
    await setup.async_setup_component.opp, binary_sensor.DOMAIN, config)
    await.opp.async_block_till_done()
    await.opp.async_start()

   .opp.states.async_set("sensor.test_state", "on")
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "off"

    future = dt_util.utcnow() + timedelta(seconds=3)
    async_fire_time_changed.opp, future)
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "on"

    # check with time changes
   .opp.states.async_set("sensor.test_state", "off")
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "off"

   .opp.states.async_set("sensor.test_state", "on")
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "off"

   .opp.states.async_set("sensor.test_state", "off")
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "off"

    future = dt_util.utcnow() + timedelta(seconds=3)
    async_fire_time_changed.opp, future)
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "off"


async def test_template_with_templated_delay_off.opp):
    """Test binary sensor template with template delay off."""
    config = {
        "binary_sensor": {
            "platform": "template",
            "sensors": {
                "test": {
                    "friendly_name": "virtual thingy",
                    "value_template": "{{ states.sensor.test_state.state == 'on' }}",
                    "device_class": "motion",
                    "delay_off": '{{ ({ "seconds": 6 / 2 }) }}',
                }
            },
        }
    }
   .opp.states.async_set("sensor.test_state", "on")
    await setup.async_setup_component.opp, binary_sensor.DOMAIN, config)
    await.opp.async_block_till_done()
    await.opp.async_start()

   .opp.states.async_set("sensor.test_state", "off")
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "on"

    future = dt_util.utcnow() + timedelta(seconds=3)
    async_fire_time_changed.opp, future)
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "off"

    # check with time changes
   .opp.states.async_set("sensor.test_state", "on")
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "on"

   .opp.states.async_set("sensor.test_state", "off")
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "on"

   .opp.states.async_set("sensor.test_state", "on")
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "on"

    future = dt_util.utcnow() + timedelta(seconds=3)
    async_fire_time_changed.opp, future)
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "on"


async def test_template_with_delay_on_based_on_input.opp):
    """Test binary sensor template with template delay on based on input number."""
    config = {
        "binary_sensor": {
            "platform": "template",
            "sensors": {
                "test": {
                    "friendly_name": "virtual thingy",
                    "value_template": "{{ states.sensor.test_state.state == 'on' }}",
                    "device_class": "motion",
                    "delay_on": '{{ ({ "seconds": states("input_number.delay")|int }) }}',
                }
            },
        }
    }
    await setup.async_setup_component.opp, binary_sensor.DOMAIN, config)
    await.opp.async_block_till_done()
    await.opp.async_start()

   .opp.states.async_set("sensor.test_state", "off")
    await.opp.async_block_till_done()

   .opp.states.async_set("input_number.delay", 3)
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "off"

   .opp.states.async_set("sensor.test_state", "on")
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "off"

    future = dt_util.utcnow() + timedelta(seconds=3)
    async_fire_time_changed.opp, future)
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "on"

    # set input to 4 seconds
   .opp.states.async_set("sensor.test_state", "off")
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "off"

   .opp.states.async_set("input_number.delay", 4)
    await.opp.async_block_till_done()

   .opp.states.async_set("sensor.test_state", "on")
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "off"

    future = dt_util.utcnow() + timedelta(seconds=2)
    async_fire_time_changed.opp, future)
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "off"

    future = dt_util.utcnow() + timedelta(seconds=4)
    async_fire_time_changed.opp, future)
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "on"


async def test_template_with_delay_off_based_on_input.opp):
    """Test binary sensor template with template delay off based on input number."""
    config = {
        "binary_sensor": {
            "platform": "template",
            "sensors": {
                "test": {
                    "friendly_name": "virtual thingy",
                    "value_template": "{{ states.sensor.test_state.state == 'on' }}",
                    "device_class": "motion",
                    "delay_off": '{{ ({ "seconds": states("input_number.delay")|int }) }}',
                }
            },
        }
    }
    await setup.async_setup_component.opp, binary_sensor.DOMAIN, config)
    await.opp.async_block_till_done()
    await.opp.async_start()

   .opp.states.async_set("sensor.test_state", "on")
    await.opp.async_block_till_done()

   .opp.states.async_set("input_number.delay", 3)
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "on"

   .opp.states.async_set("sensor.test_state", "off")
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "on"

    future = dt_util.utcnow() + timedelta(seconds=3)
    async_fire_time_changed.opp, future)
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "off"

    # set input to 4 seconds
   .opp.states.async_set("sensor.test_state", "on")
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "on"

   .opp.states.async_set("input_number.delay", 4)
    await.opp.async_block_till_done()

   .opp.states.async_set("sensor.test_state", "off")
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "on"

    future = dt_util.utcnow() + timedelta(seconds=2)
    async_fire_time_changed.opp, future)
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "on"

    future = dt_util.utcnow() + timedelta(seconds=4)
    async_fire_time_changed.opp, future)
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.state == "off"


async def test_available_without_availability_template.opp):
    """Ensure availability is true without an availability_template."""
    config = {
        "binary_sensor": {
            "platform": "template",
            "sensors": {
                "test": {
                    "friendly_name": "virtual thingy",
                    "value_template": "true",
                    "device_class": "motion",
                    "delay_off": 5,
                }
            },
        }
    }
    await setup.async_setup_component.opp, binary_sensor.DOMAIN, config)
    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")

    assert state.state != STATE_UNAVAILABLE
    assert state.attributes[ATTR_DEVICE_CLASS] == "motion"


async def test_availability_template.opp):
    """Test availability template."""
    config = {
        "binary_sensor": {
            "platform": "template",
            "sensors": {
                "test": {
                    "friendly_name": "virtual thingy",
                    "value_template": "true",
                    "device_class": "motion",
                    "delay_off": 5,
                    "availability_template": "{{ is_state('sensor.test_state','on') }}",
                }
            },
        }
    }
    await setup.async_setup_component.opp, binary_sensor.DOMAIN, config)
    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

   .opp.states.async_set("sensor.test_state", STATE_OFF)
    await.opp.async_block_till_done()

    assert.opp.states.get("binary_sensor.test").state == STATE_UNAVAILABLE

   .opp.states.async_set("sensor.test_state", STATE_ON)
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")

    assert state.state != STATE_UNAVAILABLE
    assert state.attributes[ATTR_DEVICE_CLASS] == "motion"


async def test_invalid_attribute_template.opp, caplog):
    """Test that errors are logged if rendering template fails."""
   .opp.states.async_set("binary_sensor.test_sensor", "true")

    await setup.async_setup_component(
       .opp,
        binary_sensor.DOMAIN,
        {
            "binary_sensor": {
                "platform": "template",
                "sensors": {
                    "invalid_template": {
                        "value_template": "{{ states.binary_sensor.test_sensor }}",
                        "attribute_templates": {
                            "test_attribute": "{{ states.binary_sensor.unknown.attributes.picture }}"
                        },
                    }
                },
            }
        },
    )
    await.opp.async_block_till_done()
    assert len.opp.states.async_all()) == 2
    await.opp.async_start()
    await.opp.async_block_till_done()

    assert "test_attribute" in caplog.text
    assert "TemplateError" in caplog.text


async def test_invalid_availability_template_keeps_component_available.opp, caplog):
    """Test that an invalid availability keeps the device available."""

    await setup.async_setup_component(
       .opp,
        binary_sensor.DOMAIN,
        {
            "binary_sensor": {
                "platform": "template",
                "sensors": {
                    "my_sensor": {
                        "value_template": "{{ states.binary_sensor.test_sensor }}",
                        "availability_template": "{{ x - 12 }}",
                    }
                },
            }
        },
    )
    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    assert.opp.states.get("binary_sensor.my_sensor").state != STATE_UNAVAILABLE
    assert ("UndefinedError: 'x' is undefined") in caplog.text


async def test_no_update_template_match_all.opp, caplog):
    """Test that we do not update sensors that match on all."""
   .opp.states.async_set("binary_sensor.test_sensor", "true")

   .opp.state = CoreState.not_running

    await setup.async_setup_component(
       .opp,
        binary_sensor.DOMAIN,
        {
            "binary_sensor": {
                "platform": "template",
                "sensors": {
                    "all_state": {"value_template": '{{ "true" }}'},
                    "all_icon": {
                        "value_template": "{{ states.binary_sensor.test_sensor.state }}",
                        "icon_template": "{{ 1 + 1 }}",
                    },
                    "all_entity_picture": {
                        "value_template": "{{ states.binary_sensor.test_sensor.state }}",
                        "entity_picture_template": "{{ 1 + 1 }}",
                    },
                    "all_attribute": {
                        "value_template": "{{ states.binary_sensor.test_sensor.state }}",
                        "attribute_templates": {"test_attribute": "{{ 1 + 1 }}"},
                    },
                },
            }
        },
    )
    await.opp.async_block_till_done()
    assert len.opp.states.async_all()) == 5

    assert.opp.states.get("binary_sensor.all_state").state == "off"
    assert.opp.states.get("binary_sensor.all_icon").state == "off"
    assert.opp.states.get("binary_sensor.all_entity_picture").state == "off"
    assert.opp.states.get("binary_sensor.all_attribute").state == "off"

   .opp.bus.async_fire(EVENT_OPENPEERPOWER_START)
    await.opp.async_block_till_done()

    assert.opp.states.get("binary_sensor.all_state").state == "on"
    assert.opp.states.get("binary_sensor.all_icon").state == "on"
    assert.opp.states.get("binary_sensor.all_entity_picture").state == "on"
    assert.opp.states.get("binary_sensor.all_attribute").state == "on"

   .opp.states.async_set("binary_sensor.test_sensor", "false")
    await.opp.async_block_till_done()

    assert.opp.states.get("binary_sensor.all_state").state == "on"
    # Will now process because we have one valid template
    assert.opp.states.get("binary_sensor.all_icon").state == "off"
    assert.opp.states.get("binary_sensor.all_entity_picture").state == "off"
    assert.opp.states.get("binary_sensor.all_attribute").state == "off"

    await.opp.helpers.entity_component.async_update_entity("binary_sensor.all_state")
    await.opp.helpers.entity_component.async_update_entity("binary_sensor.all_icon")
    await.opp.helpers.entity_component.async_update_entity(
        "binary_sensor.all_entity_picture"
    )
    await.opp.helpers.entity_component.async_update_entity(
        "binary_sensor.all_attribute"
    )

    assert.opp.states.get("binary_sensor.all_state").state == "on"
    assert.opp.states.get("binary_sensor.all_icon").state == "off"
    assert.opp.states.get("binary_sensor.all_entity_picture").state == "off"
    assert.opp.states.get("binary_sensor.all_attribute").state == "off"


async def test_unique_id.opp):
    """Test unique_id option only creates one binary sensor per id."""
    await setup.async_setup_component(
       .opp,
        binary_sensor.DOMAIN,
        {
            "binary_sensor": {
                "platform": "template",
                "sensors": {
                    "test_template_cover_01": {
                        "unique_id": "not-so-unique-anymore",
                        "value_template": "{{ true }}",
                    },
                    "test_template_cover_02": {
                        "unique_id": "not-so-unique-anymore",
                        "value_template": "{{ false }}",
                    },
                },
            },
        },
    )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    assert len.opp.states.async_all()) == 1


async def test_template_validation_error.opp, caplog):
    """Test binary sensor template delay on."""
    caplog.set_level(logging.ERROR)
    config = {
        "binary_sensor": {
            "platform": "template",
            "sensors": {
                "test": {
                    "friendly_name": "virtual thingy",
                    "value_template": "True",
                    "icon_template": "{{ states.sensor.test_state.state }}",
                    "device_class": "motion",
                    "delay_on": 5,
                },
            },
        },
    }
    await setup.async_setup_component.opp, binary_sensor.DOMAIN, config)
    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.attributes.get("icon") == ""

   .opp.states.async_set("sensor.test_state", "mdi:check")
    await.opp.async_block_till_done()

    state = opp.states.get("binary_sensor.test")
    assert state.attributes.get("icon") == "mdi:check"

   .opp.states.async_set("sensor.test_state", "invalid_icon")
    await.opp.async_block_till_done()
    assert len(caplog.records) == 1
    assert caplog.records[0].message.startswith(
        "Error validating template result 'invalid_icon' from template"
    )

    state = opp.states.get("binary_sensor.test")
    assert state.attributes.get("icon") is None
