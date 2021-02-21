"""The test for the Template sensor platform."""
from asyncio import Event
from datetime import timedelta
from unittest.mock import patch

import pytest

from openpeerpowerr.bootstrap import async_from_config_dict
from openpeerpower.components import sensor
from openpeerpower.const import (
    ATTR_ENTITY_PICTURE,
    ATTR_ICON,
    EVENT_COMPONENT_LOADED,
    EVENT_OPENPEERPOWER_START,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from openpeerpowerr.core import CoreState, callback
from openpeerpowerr.helpers.template import Template
from openpeerpowerr.setup import ATTR_COMPONENT, async_setup_component
import openpeerpowerr.util.dt as dt_util

from tests.common import assert_setup_component, async_fire_time_changed


async def test_template.opp):
    """Test template."""
    with assert_setup_component(1, sensor.DOMAIN):
        assert await async_setup_component(
           .opp,
            sensor.DOMAIN,
            {
                "sensor": {
                    "platform": "template",
                    "sensors": {
                        "test_template_sensor": {
                            "value_template": "It {{ states.sensor.test_state.state }}."
                        }
                    },
                }
            },
        )

    await opp.async_block_till_done()
    await.opp.async_start()
    await opp.async_block_till_done()

    state = opp.states.get("sensor.test_template_sensor")
    assert state.state == "It ."

   .opp.states.async_set("sensor.test_state", "Works")
    await opp.async_block_till_done()
    state = opp.states.get("sensor.test_template_sensor")
    assert state.state == "It Works."


async def test_icon_template.opp):
    """Test icon template."""
    with assert_setup_component(1, sensor.DOMAIN):
        assert await async_setup_component(
           .opp,
            sensor.DOMAIN,
            {
                "sensor": {
                    "platform": "template",
                    "sensors": {
                        "test_template_sensor": {
                            "value_template": "{{ states.sensor.test_state.state }}",
                            "icon_template": "{% if states.sensor.test_state.state == "
                            "'Works' %}"
                            "mdi:check"
                            "{% endif %}",
                        }
                    },
                }
            },
        )

    await opp.async_block_till_done()
    await.opp.async_start()
    await opp.async_block_till_done()

    state = opp.states.get("sensor.test_template_sensor")
    assert state.attributes.get("icon") == ""

   .opp.states.async_set("sensor.test_state", "Works")
    await opp.async_block_till_done()
    state = opp.states.get("sensor.test_template_sensor")
    assert state.attributes["icon"] == "mdi:check"


async def test_entity_picture_template.opp):
    """Test entity_picture template."""
    with assert_setup_component(1, sensor.DOMAIN):
        assert await async_setup_component(
           .opp,
            sensor.DOMAIN,
            {
                "sensor": {
                    "platform": "template",
                    "sensors": {
                        "test_template_sensor": {
                            "value_template": "{{ states.sensor.test_state.state }}",
                            "entity_picture_template": "{% if states.sensor.test_state.state == "
                            "'Works' %}"
                            "/local/sensor.png"
                            "{% endif %}",
                        }
                    },
                }
            },
        )

    await opp.async_block_till_done()
    await.opp.async_start()
    await opp.async_block_till_done()

    state = opp.states.get("sensor.test_template_sensor")
    assert state.attributes.get("entity_picture") == ""

   .opp.states.async_set("sensor.test_state", "Works")
    await opp.async_block_till_done()
    state = opp.states.get("sensor.test_template_sensor")
    assert state.attributes["entity_picture"] == "/local/sensor.png"


async def test_friendly_name_template.opp):
    """Test friendly_name template."""
    with assert_setup_component(1, sensor.DOMAIN):
        assert await async_setup_component(
           .opp,
            sensor.DOMAIN,
            {
                "sensor": {
                    "platform": "template",
                    "sensors": {
                        "test_template_sensor": {
                            "value_template": "{{ states.sensor.test_state.state }}",
                            "friendly_name_template": "It {{ states.sensor.test_state.state }}.",
                        }
                    },
                }
            },
        )

    await opp.async_block_till_done()
    await.opp.async_start()
    await opp.async_block_till_done()

    state = opp.states.get("sensor.test_template_sensor")
    assert state.attributes.get("friendly_name") == "It ."

   .opp.states.async_set("sensor.test_state", "Works")
    await opp.async_block_till_done()
    state = opp.states.get("sensor.test_template_sensor")
    assert state.attributes["friendly_name"] == "It Works."


async def test_friendly_name_template_with_unknown_state.opp):
    """Test friendly_name template with an unknown value_template."""
    with assert_setup_component(1, sensor.DOMAIN):
        assert await async_setup_component(
           .opp,
            sensor.DOMAIN,
            {
                "sensor": {
                    "platform": "template",
                    "sensors": {
                        "test_template_sensor": {
                            "value_template": "{{ states.fourohfour.state }}",
                            "friendly_name_template": "It {{ states.sensor.test_state.state }}.",
                        }
                    },
                }
            },
        )

    await opp.async_block_till_done()
    await.opp.async_start()
    await opp.async_block_till_done()

    state = opp.states.get("sensor.test_template_sensor")
    assert state.attributes["friendly_name"] == "It ."

   .opp.states.async_set("sensor.test_state", "Works")
    await opp.async_block_till_done()
    state = opp.states.get("sensor.test_template_sensor")
    assert state.attributes["friendly_name"] == "It Works."


async def test_attribute_templates.opp):
    """Test attribute_templates template."""
    with assert_setup_component(1, sensor.DOMAIN):
        assert await async_setup_component(
           .opp,
            sensor.DOMAIN,
            {
                "sensor": {
                    "platform": "template",
                    "sensors": {
                        "test_template_sensor": {
                            "value_template": "{{ states.sensor.test_state.state }}",
                            "attribute_templates": {
                                "test_attribute": "It {{ states.sensor.test_state.state }}."
                            },
                        }
                    },
                }
            },
        )

    await opp.async_block_till_done()
    await.opp.async_start()
    await opp.async_block_till_done()

    state = opp.states.get("sensor.test_template_sensor")
    assert state.attributes.get("test_attribute") == "It ."

   .opp.states.async_set("sensor.test_state", "Works")
    await opp.async_block_till_done()
    state = opp.states.get("sensor.test_template_sensor")
    assert state.attributes["test_attribute"] == "It Works."


async def test_template_syntax_error.opp):
    """Test templating syntax error."""
    with assert_setup_component(0, sensor.DOMAIN):
        assert await async_setup_component(
           .opp,
            sensor.DOMAIN,
            {
                "sensor": {
                    "platform": "template",
                    "sensors": {
                        "test_template_sensor": {"value_template": "{% if rubbish %}"}
                    },
                }
            },
        )

    await opp.async_block_till_done()
    await.opp.async_start()
    await opp.async_block_till_done()
    assert.opp.states.async_all() == []


async def test_template_attribute_missing.opp):
    """Test missing attribute template."""
    with assert_setup_component(1, sensor.DOMAIN):
        assert await async_setup_component(
           .opp,
            sensor.DOMAIN,
            {
                "sensor": {
                    "platform": "template",
                    "sensors": {
                        "test_template_sensor": {
                            "value_template": "It {{ states.sensor.test_state"
                            ".attributes.missing }}."
                        }
                    },
                }
            },
        )

    await opp.async_block_till_done()
    await.opp.async_start()
    await opp.async_block_till_done()

    state = opp.states.get("sensor.test_template_sensor")
    assert state.state == STATE_UNAVAILABLE


async def test_invalid_name_does_not_create.opp):
    """Test invalid name."""
    with assert_setup_component(0, sensor.DOMAIN):
        assert await async_setup_component(
           .opp,
            sensor.DOMAIN,
            {
                "sensor": {
                    "platform": "template",
                    "sensors": {
                        "test INVALID sensor": {
                            "value_template": "{{ states.sensor.test_state.state }}"
                        }
                    },
                }
            },
        )

    await opp.async_block_till_done()
    await.opp.async_start()
    await opp.async_block_till_done()

    assert.opp.states.async_all() == []


async def test_invalid_sensor_does_not_create.opp):
    """Test invalid sensor."""
    with assert_setup_component(0, sensor.DOMAIN):
        assert await async_setup_component(
           .opp,
            sensor.DOMAIN,
            {
                "sensor": {
                    "platform": "template",
                    "sensors": {"test_template_sensor": "invalid"},
                }
            },
        )

    await opp.async_block_till_done()
    await.opp.async_start()

    assert.opp.states.async_all() == []


async def test_no_sensors_does_not_create.opp):
    """Test no sensors."""
    with assert_setup_component(0, sensor.DOMAIN):
        assert await async_setup_component(
           .opp, sensor.DOMAIN, {"sensor": {"platform": "template"}}
        )

    await opp.async_block_till_done()
    await.opp.async_start()
    await opp.async_block_till_done()

    assert.opp.states.async_all() == []


async def test_missing_template_does_not_create.opp):
    """Test missing template."""
    with assert_setup_component(0, sensor.DOMAIN):
        assert await async_setup_component(
           .opp,
            sensor.DOMAIN,
            {
                "sensor": {
                    "platform": "template",
                    "sensors": {
                        "test_template_sensor": {
                            "not_value_template": "{{ states.sensor.test_state.state }}"
                        }
                    },
                }
            },
        )

    await opp.async_block_till_done()
    await.opp.async_start()
    await opp.async_block_till_done()

    assert.opp.states.async_all() == []


async def test_setup_invalid_device_class.opp):
    """Test setup with invalid device_class."""
    with assert_setup_component(0, sensor.DOMAIN):
        assert await async_setup_component(
           .opp,
            sensor.DOMAIN,
            {
                "sensor": {
                    "platform": "template",
                    "sensors": {
                        "test": {
                            "value_template": "{{ states.sensor.test_sensor.state }}",
                            "device_class": "foobarnotreal",
                        }
                    },
                }
            },
        )


async def test_setup_valid_device_class.opp):
    """Test setup with valid device_class."""
    with assert_setup_component(1, sensor.DOMAIN):
        assert await async_setup_component(
           .opp,
            sensor.DOMAIN,
            {
                "sensor": {
                    "platform": "template",
                    "sensors": {
                        "test1": {
                            "value_template": "{{ states.sensor.test_sensor.state }}",
                            "device_class": "temperature",
                        },
                        "test2": {
                            "value_template": "{{ states.sensor.test_sensor.state }}"
                        },
                    },
                }
            },
        )
    await opp.async_block_till_done()

    state = opp.states.get("sensor.test1")
    assert state.attributes["device_class"] == "temperature"
    state = opp.states.get("sensor.test2")
    assert "device_class" not in state.attributes


@pytest.mark.parametrize("load_registries", [False])
async def test_creating_sensor_loads_group.opp):
    """Test setting up template sensor loads group component first."""
    order = []
    after_dep_event = Event()

    async def async_setup_group.opp, config):
        # Make sure group takes longer to load, so that it won't
        # be loaded first by chance
        await after_dep_event.wait()

        order.append("group")
        return True

    async def async_setup_template(
       .opp, config, async_add_entities, discovery_info=None
    ):
        order.append("sensor.template")
        return True

    async def set_after_dep_event(event):
        if event.data[ATTR_COMPONENT] == "sensor":
            after_dep_event.set()

   .opp.bus.async_listen(EVENT_COMPONENT_LOADED, set_after_dep_event)

    with patch(
        "openpeerpower.components.group.async_setup",
        new=async_setup_group,
    ), patch(
        "openpeerpower.components.template.sensor.async_setup_platform",
        new=async_setup_template,
    ):
        await async_from_config_dict(
            {"sensor": {"platform": "template", "sensors": {}}, "group": {}},.opp
        )
        await opp.async_block_till_done()

    assert order == ["group", "sensor.template"]


async def test_available_template_with_entities.opp):
    """Test availability tempalates with values from other entities."""
   .opp.states.async_set("sensor.availability_sensor", STATE_OFF)
    with assert_setup_component(1, sensor.DOMAIN):
        assert await async_setup_component(
           .opp,
            sensor.DOMAIN,
            {
                "sensor": {
                    "platform": "template",
                    "sensors": {
                        "test_template_sensor": {
                            "value_template": "{{ states.sensor.test_sensor.state }}",
                            "availability_template": "{{ is_state('sensor.availability_sensor', 'on') }}",
                        }
                    },
                }
            },
        )

    await opp.async_block_till_done()
    await.opp.async_start()
    await opp.async_block_till_done()

    # When template returns true..
   .opp.states.async_set("sensor.availability_sensor", STATE_ON)
    await opp.async_block_till_done()

    # Device State should not be unavailable
    assert.opp.states.get("sensor.test_template_sensor").state != STATE_UNAVAILABLE

    # When Availability template returns false
   .opp.states.async_set("sensor.availability_sensor", STATE_OFF)
    await opp.async_block_till_done()

    # device state should be unavailable
    assert.opp.states.get("sensor.test_template_sensor").state == STATE_UNAVAILABLE


async def test_invalid_attribute_template.opp, caplog):
    """Test that errors are logged if rendering template fails."""
   .opp.states.async_set("sensor.test_sensor", "startup")

    await async_setup_component(
       .opp,
        sensor.DOMAIN,
        {
            "sensor": {
                "platform": "template",
                "sensors": {
                    "invalid_template": {
                        "value_template": "{{ states.sensor.test_sensor.state }}",
                        "attribute_templates": {
                            "test_attribute": "{{ states.sensor.unknown.attributes.picture }}"
                        },
                    }
                },
            }
        },
    )
    await opp.async_block_till_done()
    assert len.opp.states.async_all()) == 2

   .opp.bus.async_fire(EVENT_OPENPEERPOWER_START)
    await opp.async_block_till_done()
    await.opp.helpers.entity_component.async_update_entity("sensor.invalid_template")

    assert "TemplateError" in caplog.text
    assert "test_attribute" in caplog.text


async def test_invalid_availability_template_keeps_component_available.opp, caplog):
    """Test that an invalid availability keeps the device available."""

    await async_setup_component(
       .opp,
        sensor.DOMAIN,
        {
            "sensor": {
                "platform": "template",
                "sensors": {
                    "my_sensor": {
                        "value_template": "{{ states.sensor.test_state.state }}",
                        "availability_template": "{{ x - 12 }}",
                    }
                },
            }
        },
    )

    await opp.async_block_till_done()
    await.opp.async_start()
    await opp.async_block_till_done()

    assert.opp.states.get("sensor.my_sensor").state != STATE_UNAVAILABLE
    assert ("UndefinedError: 'x' is undefined") in caplog.text


async def test_no_template_match_all.opp, caplog):
    """Test that we allow static templates."""
   .opp.states.async_set("sensor.test_sensor", "startup")

   .opp.state = CoreState.not_running

    await async_setup_component(
       .opp,
        sensor.DOMAIN,
        {
            "sensor": {
                "platform": "template",
                "sensors": {
                    "invalid_state": {"value_template": "{{ 1 + 1 }}"},
                    "invalid_icon": {
                        "value_template": "{{ states.sensor.test_sensor.state }}",
                        "icon_template": "{{ 1 + 1 }}",
                    },
                    "invalid_entity_picture": {
                        "value_template": "{{ states.sensor.test_sensor.state }}",
                        "entity_picture_template": "{{ 1 + 1 }}",
                    },
                    "invalid_friendly_name": {
                        "value_template": "{{ states.sensor.test_sensor.state }}",
                        "friendly_name_template": "{{ 1 + 1 }}",
                    },
                    "invalid_attribute": {
                        "value_template": "{{ states.sensor.test_sensor.state }}",
                        "attribute_templates": {"test_attribute": "{{ 1 + 1 }}"},
                    },
                },
            }
        },
    )
    await opp.async_block_till_done()

    assert.opp.states.get("sensor.invalid_state").state == "unknown"
    assert.opp.states.get("sensor.invalid_icon").state == "unknown"
    assert.opp.states.get("sensor.invalid_entity_picture").state == "unknown"
    assert.opp.states.get("sensor.invalid_friendly_name").state == "unknown"

    await opp.async_block_till_done()
    assert len.opp.states.async_all()) == 6

    assert.opp.states.get("sensor.invalid_state").state == "unknown"
    assert.opp.states.get("sensor.invalid_icon").state == "unknown"
    assert.opp.states.get("sensor.invalid_entity_picture").state == "unknown"
    assert.opp.states.get("sensor.invalid_friendly_name").state == "unknown"
    assert.opp.states.get("sensor.invalid_attribute").state == "unknown"

   .opp.bus.async_fire(EVENT_OPENPEERPOWER_START)
    await opp.async_block_till_done()

    assert.opp.states.get("sensor.invalid_state").state == "2"
    assert.opp.states.get("sensor.invalid_icon").state == "startup"
    assert.opp.states.get("sensor.invalid_entity_picture").state == "startup"
    assert.opp.states.get("sensor.invalid_friendly_name").state == "startup"
    assert.opp.states.get("sensor.invalid_attribute").state == "startup"

   .opp.states.async_set("sensor.test_sensor", "hello")
    await opp.async_block_till_done()

    assert.opp.states.get("sensor.invalid_state").state == "2"
    # Will now process because we have at least one valid template
    assert.opp.states.get("sensor.invalid_icon").state == "hello"
    assert.opp.states.get("sensor.invalid_entity_picture").state == "hello"
    assert.opp.states.get("sensor.invalid_friendly_name").state == "hello"
    assert.opp.states.get("sensor.invalid_attribute").state == "hello"

    await.opp.helpers.entity_component.async_update_entity("sensor.invalid_state")
    await.opp.helpers.entity_component.async_update_entity("sensor.invalid_icon")
    await.opp.helpers.entity_component.async_update_entity(
        "sensor.invalid_entity_picture"
    )
    await.opp.helpers.entity_component.async_update_entity(
        "sensor.invalid_friendly_name"
    )
    await.opp.helpers.entity_component.async_update_entity("sensor.invalid_attribute")

    assert.opp.states.get("sensor.invalid_state").state == "2"
    assert.opp.states.get("sensor.invalid_icon").state == "hello"
    assert.opp.states.get("sensor.invalid_entity_picture").state == "hello"
    assert.opp.states.get("sensor.invalid_friendly_name").state == "hello"
    assert.opp.states.get("sensor.invalid_attribute").state == "hello"


async def test_unique_id.opp):
    """Test unique_id option only creates one sensor per id."""
    await async_setup_component(
       .opp,
        sensor.DOMAIN,
        {
            "sensor": {
                "platform": "template",
                "sensors": {
                    "test_template_sensor_01": {
                        "unique_id": "not-so-unique-anymore",
                        "value_template": "{{ true }}",
                    },
                    "test_template_sensor_02": {
                        "unique_id": "not-so-unique-anymore",
                        "value_template": "{{ false }}",
                    },
                },
            }
        },
    )

    await opp.async_block_till_done()
    await.opp.async_start()
    await opp.async_block_till_done()

    assert len.opp.states.async_all()) == 1


async def test_sun_renders_once_per_sensor.opp):
    """Test sun change renders the template only once per sensor."""

    now = dt_util.utcnow()
   .opp.states.async_set(
        "sun.sun", "above_horizon", {"elevation": 45.3, "next_rising": now}
    )

    await async_setup_component(
       .opp,
        sensor.DOMAIN,
        {
            "sensor": {
                "platform": "template",
                "sensors": {
                    "solar_angle": {
                        "friendly_name": "Sun angle",
                        "unit_of_measurement": "degrees",
                        "value_template": "{{ state_attr('sun.sun', 'elevation') }}",
                    },
                    "sunrise": {
                        "value_template": "{{ state_attr('sun.sun', 'next_rising') }}"
                    },
                },
            }
        },
    )

    await opp.async_block_till_done()
    await.opp.async_start()
    await opp.async_block_till_done()

    assert len.opp.states.async_all()) == 3

    assert.opp.states.get("sensor.solar_angle").state == "45.3"
    assert.opp.states.get("sensor.sunrise").state == str(now)

    async_render_calls = []

    @callback
    def _record_async_render(self, *args, **kwargs):
        """Catch async_render."""
        async_render_calls.append(self.template)
        return "mocked"

    later = dt_util.utcnow()

    with patch.object(Template, "async_render", _record_async_render):
       .opp.states.async_set("sun.sun", {"elevation": 50, "next_rising": later})
        await opp.async_block_till_done()

    assert.opp.states.get("sensor.solar_angle").state == "mocked"
    assert.opp.states.get("sensor.sunrise").state == "mocked"

    assert len(async_render_calls) == 2
    assert set(async_render_calls) == {
        "{{ state_attr('sun.sun', 'elevation') }}",
        "{{ state_attr('sun.sun', 'next_rising') }}",
    }


async def test_self_referencing_sensor_loop.opp, caplog):
    """Test a self referencing sensor does not loop forever."""

    await async_setup_component(
       .opp,
        sensor.DOMAIN,
        {
            "sensor": {
                "platform": "template",
                "sensors": {
                    "test": {
                        "value_template": "{{ ((states.sensor.test.state or 0) | int) + 1 }}",
                    },
                },
            }
        },
    )

    await opp.async_block_till_done()
    await.opp.async_start()
    await opp.async_block_till_done()

    assert len.opp.states.async_all()) == 1

    await opp.async_block_till_done()
    await opp.async_block_till_done()

    assert "Template loop detected" in caplog.text

    state = opp.states.get("sensor.test")
    assert int(state.state) == 2
    await opp.async_block_till_done()
    assert int(state.state) == 2


async def test_self_referencing_sensor_with_icon_loop.opp, caplog):
    """Test a self referencing sensor loops forever with a valid self referencing icon."""

    await async_setup_component(
       .opp,
        sensor.DOMAIN,
        {
            "sensor": {
                "platform": "template",
                "sensors": {
                    "test": {
                        "value_template": "{{ ((states.sensor.test.state or 0) | int) + 1 }}",
                        "icon_template": "{% if ((states.sensor.test.state or 0) | int) >= 1 %}mdi:greater{% else %}mdi:less{% endif %}",
                    },
                },
            }
        },
    )

    await opp.async_block_till_done()
    await.opp.async_start()
    await opp.async_block_till_done()

    assert len.opp.states.async_all()) == 1

    await opp.async_block_till_done()
    await opp.async_block_till_done()

    assert "Template loop detected" in caplog.text

    state = opp.states.get("sensor.test")
    assert int(state.state) == 3
    assert state.attributes[ATTR_ICON] == "mdi:greater"

    await opp.async_block_till_done()
    assert int(state.state) == 3


async def test_self_referencing_sensor_with_icon_and_picture_entity_loop.opp, caplog):
    """Test a self referencing sensor loop forevers with a valid self referencing icon."""

    await async_setup_component(
       .opp,
        sensor.DOMAIN,
        {
            "sensor": {
                "platform": "template",
                "sensors": {
                    "test": {
                        "value_template": "{{ ((states.sensor.test.state or 0) | int) + 1 }}",
                        "icon_template": "{% if ((states.sensor.test.state or 0) | int) > 3 %}mdi:greater{% else %}mdi:less{% endif %}",
                        "entity_picture_template": "{% if ((states.sensor.test.state or 0) | int) >= 1 %}bigpic{% else %}smallpic{% endif %}",
                    },
                },
            }
        },
    )

    await opp.async_block_till_done()
    await.opp.async_start()
    await opp.async_block_till_done()

    assert len.opp.states.async_all()) == 1

    await opp.async_block_till_done()
    await opp.async_block_till_done()

    assert "Template loop detected" in caplog.text

    state = opp.states.get("sensor.test")
    assert int(state.state) == 4
    assert state.attributes[ATTR_ICON] == "mdi:less"
    assert state.attributes[ATTR_ENTITY_PICTURE] == "bigpic"

    await opp.async_block_till_done()
    assert int(state.state) == 4


async def test_self_referencing_entity_picture_loop.opp, caplog):
    """Test a self referencing sensor does not loop forever with a looping self referencing entity picture."""

    await async_setup_component(
       .opp,
        sensor.DOMAIN,
        {
            "sensor": {
                "platform": "template",
                "sensors": {
                    "test": {
                        "value_template": "{{ 1 }}",
                        "entity_picture_template": "{{ ((states.sensor.test.attributes['entity_picture'] or 0) | int) + 1 }}",
                    },
                },
            }
        },
    )

    await opp.async_block_till_done()
    await.opp.async_start()
    await opp.async_block_till_done()

    assert len.opp.states.async_all()) == 1

    next_time = dt_util.utcnow() + timedelta(seconds=1.2)
    with patch(
        "openpeerpowerr.helpers.ratelimit.dt_util.utcnow", return_value=next_time
    ):
        async_fire_time_changed.opp, next_time)
        await opp.async_block_till_done()
        await opp.async_block_till_done()

    assert "Template loop detected" in caplog.text

    state = opp.states.get("sensor.test")
    assert int(state.state) == 1
    assert state.attributes[ATTR_ENTITY_PICTURE] == 2

    await opp.async_block_till_done()
    assert int(state.state) == 1


async def test_self_referencing_icon_with_no_loop.opp, caplog):
    """Test a self referencing icon that does not loop."""

   .opp.states.async_set("sensor.heartworm_high_80", 10)
   .opp.states.async_set("sensor.heartworm_low_57", 10)
   .opp.states.async_set("sensor.heartworm_avg_64", 10)
   .opp.states.async_set("sensor.heartworm_avg_57", 10)

    value_template_str = """{% if (states.sensor.heartworm_high_80.state|int >= 10) and (states.sensor.heartworm_low_57.state|int >= 10) %}
            extreme
          {% elif (states.sensor.heartworm_avg_64.state|int >= 30) %}
            high
          {% elif (states.sensor.heartworm_avg_64.state|int >= 14) %}
            moderate
          {% elif (states.sensor.heartworm_avg_64.state|int >= 5) %}
            slight
          {% elif (states.sensor.heartworm_avg_57.state|int >= 5) %}
            marginal
          {% elif (states.sensor.heartworm_avg_57.state|int < 5) %}
            none
          {% endif %}"""

    icon_template_str = """{% if is_state('sensor.heartworm_risk',"extreme") %}
            mdi:hazard-lights
          {% elif is_state('sensor.heartworm_risk',"high") %}
            mdi:triangle-outline
          {% elif is_state('sensor.heartworm_risk',"moderate") %}
            mdi:alert-circle-outline
          {% elif is_state('sensor.heartworm_risk',"slight") %}
            mdi:exclamation
          {% elif is_state('sensor.heartworm_risk',"marginal") %}
            mdi:heart
          {% elif is_state('sensor.heartworm_risk',"none") %}
            mdi:snowflake
          {% endif %}"""

    await async_setup_component(
       .opp,
        sensor.DOMAIN,
        {
            "sensor": {
                "platform": "template",
                "sensors": {
                    "heartworm_risk": {
                        "value_template": value_template_str,
                        "icon_template": icon_template_str,
                    },
                },
            }
        },
    )

    await opp.async_block_till_done()
    await.opp.async_start()
    await opp.async_block_till_done()

    assert len.opp.states.async_all()) == 5

   .opp.states.async_set("sensor.heartworm_high_80", 10)

    await opp.async_block_till_done()
    await opp.async_block_till_done()

    assert "Template loop detected" not in caplog.text

    state = opp.states.get("sensor.heartworm_risk")
    assert state.state == "extreme"
    assert state.attributes[ATTR_ICON] == "mdi:hazard-lights"

    await opp.async_block_till_done()
    assert state.state == "extreme"
    assert state.attributes[ATTR_ICON] == "mdi:hazard-lights"
    assert "Template loop detected" not in caplog.text


async def test_duplicate_templates.opp):
    """Test template entity where the value and friendly name as the same template."""
   .opp.states.async_set("sensor.test_state", "Abc")

    with assert_setup_component(1, sensor.DOMAIN):
        assert await async_setup_component(
           .opp,
            sensor.DOMAIN,
            {
                "sensor": {
                    "platform": "template",
                    "sensors": {
                        "test_template_sensor": {
                            "value_template": "{{ states.sensor.test_state.state }}",
                            "friendly_name_template": "{{ states.sensor.test_state.state }}",
                        }
                    },
                }
            },
        )

    await opp.async_block_till_done()
    await.opp.async_start()
    await opp.async_block_till_done()

    state = opp.states.get("sensor.test_template_sensor")
    assert state.attributes["friendly_name"] == "Abc"
    assert state.state == "Abc"

   .opp.states.async_set("sensor.test_state", "Def")
    await opp.async_block_till_done()

    state = opp.states.get("sensor.test_template_sensor")
    assert state.attributes["friendly_name"] == "Def"
    assert state.state == "Def"
