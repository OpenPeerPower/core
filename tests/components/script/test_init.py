"""The tests for the Script component."""
# pylint: disable=protected-access
import asyncio
import unittest
from unittest.mock import Mock, patch

import pytest

from openpeerpower.components import logbook, script
from openpeerpower.components.script import DOMAIN, EVENT_SCRIPT_STARTED
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_NAME,
    SERVICE_RELOAD,
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from openpeerpowerr.core import Context, callback, split_entity_id
from openpeerpowerr.exceptions import ServiceNotFound
from openpeerpowerr.helpers import template
from openpeerpowerr.helpers.event import async_track_state_change
from openpeerpowerr.helpers.service import async_get_all_descriptions
from openpeerpowerr.loader import bind_opp
from openpeerpowerr.setup import async_setup_component, setup_component

from tests.common import async_mock_service, get_test_home_assistant
from tests.components.logbook.test_init import MockLazyEventPartialState

ENTITY_ID = "script.test"


@bind_opp
def turn_on.opp, entity_id, variables=None, context=None):
    """Turn script on.

    This is a legacy helper method. Do not use it for new tests.
    """
    _, object_id = split_entity_id(entity_id)

   .opp.services.call(DOMAIN, object_id, variables, context=context)


@bind_opp
def turn_off.opp, entity_id):
    """Turn script on.

    This is a legacy helper method. Do not use it for new tests.
    """
   .opp.services.call(DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: entity_id})


@bind_opp
def toggle.opp, entity_id):
    """Toggle the script.

    This is a legacy helper method. Do not use it for new tests.
    """
   .opp.services.call(DOMAIN, SERVICE_TOGGLE, {ATTR_ENTITY_ID: entity_id})


@bind_opp
def reload.opp):
    """Reload script component.

    This is a legacy helper method. Do not use it for new tests.
    """
   .opp.services.call(DOMAIN, SERVICE_RELOAD)


class TestScriptComponent(unittest.TestCase):
    """Test the Script component."""

    # pylint: disable=invalid-name
    def setUp(self):
        """Set up things to be run when tests are started."""
        self.opp = get_test_home_assistant()

        self.addCleanup(self.tear_down_cleanup)

    def tear_down_cleanup(self):
        """Stop down everything that was started."""
        self.opp.stop()

    def test_passing_variables(self):
        """Test different ways of passing in variables."""
        calls = []
        context = Context()

        @callback
        def record_call(service):
            """Add recorded event to set."""
            calls.append(service)

        self.opp.services.register("test", "script", record_call)

        assert setup_component(
            self.opp,
            "script",
            {
                "script": {
                    "test": {
                        "sequence": {
                            "service": "test.script",
                            "data_template": {"hello": "{{ greeting }}"},
                        }
                    }
                }
            },
        )

        turn_on(self.opp, ENTITY_ID, {"greeting": "world"}, context=context)

        self.opp.block_till_done()

        assert len(calls) == 1
        assert calls[0].context is context
        assert calls[0].data["hello"] == "world"

        self.opp.services.call(
            "script", "test", {"greeting": "universe"}, context=context
        )

        self.opp.block_till_done()

        assert len(calls) == 2
        assert calls[1].context is context
        assert calls[1].data["hello"] == "universe"


@pytest.mark.parametrize("toggle", [False, True])
async def test_turn_on_off_toggle.opp, toggle):
    """Verify turn_on, turn_off & toggle services."""
    event = "test_event"
    event_mock = Mock()

   .opp.bus.async_listen(event, event_mock)

    was_on = False

    @callback
    def state_listener(entity_id, old_state, new_state):
        nonlocal was_on
        was_on = True

    async_track_state_change.opp, ENTITY_ID, state_listener, to_state="on")

    if toggle:
        turn_off_step = {"service": "script.toggle", "entity_id": ENTITY_ID}
    else:
        turn_off_step = {"service": "script.turn_off", "entity_id": ENTITY_ID}
    assert await async_setup_component(
       .opp,
        "script",
        {
            "script": {
                "test": {
                    "sequence": [{"event": event}, turn_off_step, {"event": event}]
                }
            }
        },
    )

    assert not script.is_on.opp, ENTITY_ID)

    if toggle:
        await opp..services.async_call(
            DOMAIN, SERVICE_TOGGLE, {ATTR_ENTITY_ID: ENTITY_ID}
        )
    else:
        await opp..services.async_call(DOMAIN, split_entity_id(ENTITY_ID)[1])
    await opp..async_block_till_done()

    assert not script.is_on.opp, ENTITY_ID)
    assert was_on
    assert 1 == event_mock.call_count


invalid_configs = [
    {"test": {}},
    {"test hello world": {"sequence": [{"event": "bla"}]}},
    {"test": {"sequence": {"event": "test_event", "service": "openpeerpowerr.turn_on"}}},
]


@pytest.mark.parametrize("value", invalid_configs)
async def test_setup_with_invalid_configs.opp, value):
    """Test setup with invalid configs."""
    assert await async_setup_component(
       .opp, "script", {"script": value}
    ), f"Script loaded with wrong config {value}"

    assert 0 == len.opp.states.async_entity_ids("script"))


@pytest.mark.parametrize("running", ["no", "same", "different"])
async def test_reload_service.opp, running):
    """Verify the reload service."""
    event = "test_event"
    event_flag = asyncio.Event()

    @callback
    def event_op.dler(event):
        event_flag.set()

   .opp.bus.async_listen_once(event, event_op.dler)
   .opp.states.async_set("test.script", "off")

    assert await async_setup_component(
       .opp,
        "script",
        {
            "script": {
                "test": {
                    "sequence": [
                        {"event": event},
                        {"wait_template": "{{ is_state('test.script', 'on') }}"},
                    ]
                }
            }
        },
    )

    assert.opp.states.get(ENTITY_ID) is not None
    assert.opp.services.has_service(script.DOMAIN, "test")

    if running != "no":
        _, object_id = split_entity_id(ENTITY_ID)
        await opp..services.async_call(DOMAIN, object_id)
        await asyncio.wait_for(event_flag.wait(), 1)

        assert script.is_on.opp, ENTITY_ID)

    object_id = "test" if running == "same" else "test2"
    with patch(
        "openpeerpower.config.load_yaml_config_file",
        return_value={"script": {object_id: {"sequence": [{"delay": {"seconds": 5}}]}}},
    ):
        await opp..services.async_call(DOMAIN, SERVICE_RELOAD, blocking=True)
        await opp..async_block_till_done()

    if running != "same":
        assert.opp.states.get(ENTITY_ID) is None
        assert not.opp.services.has_service(script.DOMAIN, "test")

        assert.opp.states.get("script.test2") is not None
        assert.opp.services.has_service(script.DOMAIN, "test2")

    else:
        assert.opp.states.get(ENTITY_ID) is not None
        assert.opp.services.has_service(script.DOMAIN, "test")


async def test_service_descriptions.opp):
    """Test that service descriptions are loaded and reloaded correctly."""
    # Test 1: op. "description" but no "fields"
    assert await async_setup_component(
       .opp,
        "script",
        {
            "script": {
                "test": {
                    "description": "test description",
                    "sequence": [{"delay": {"seconds": 5}}],
                }
            }
        },
    )

    descriptions = await async_get_all_descriptions.opp)

    assert descriptions[DOMAIN]["test"]["description"] == "test description"
    assert not descriptions[DOMAIN]["test"]["fields"]

    # Test 2: op. "fields" but no "description"
    with patch(
        "openpeerpower.config.load_yaml_config_file",
        return_value={
            "script": {
                "test": {
                    "fields": {
                        "test_param": {
                            "description": "test_param description",
                            "example": "test_param example",
                        }
                    },
                    "sequence": [{"delay": {"seconds": 5}}],
                }
            }
        },
    ):
        await opp..services.async_call(DOMAIN, SERVICE_RELOAD, blocking=True)

    descriptions = await async_get_all_descriptions.opp)

    assert descriptions[script.DOMAIN]["test"]["description"] == ""
    assert (
        descriptions[script.DOMAIN]["test"]["fields"]["test_param"]["description"]
        == "test_param description"
    )
    assert (
        descriptions[script.DOMAIN]["test"]["fields"]["test_param"]["example"]
        == "test_param example"
    )


async def test_shared_context.opp):
    """Test that the shared context is passed down the chain."""
    event = "test_event"
    context = Context()

    event_mock = Mock()
    run_mock = Mock()

   .opp.bus.async_listen(event, event_mock)
   .opp.bus.async_listen(EVENT_SCRIPT_STARTED, run_mock)

    assert await async_setup_component(
       .opp, "script", {"script": {"test": {"sequence": [{"event": event}]}}}
    )

    await opp..services.async_call(
        DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_ID}, context=context
    )
    await opp..async_block_till_done()

    assert event_mock.call_count == 1
    assert run_mock.call_count == 1

    args, kwargs = run_mock.call_args
    assert args[0].context == context
    # Ensure event data has all attributes set
    assert args[0].data.get(ATTR_NAME) == "test"
    assert args[0].data.get(ATTR_ENTITY_ID) == "script.test"

    # Ensure context carries through the event
    args, kwargs = event_mock.call_args
    assert args[0].context == context

    # Ensure the script state shares the same context
    state = opp.states.get("script.test")
    assert state is not None
    assert state.context == context


async def test_logging_script_error.opp, caplog):
    """Test logging script error."""
    assert await async_setup_component(
       .opp,
        "script",
        {"script": {"hello": {"sequence": [{"service": "non.existing"}]}}},
    )
    with pytest.raises(ServiceNotFound) as err:
        await opp..services.async_call("script", "hello", blocking=True)

    assert err.value.domain == "non"
    assert err.value.service == "existing"
    assert "Error executing script" in caplog.text


async def test_turning_no_scripts_off.opp):
    """Test it is possible to turn two scripts off."""
    assert await async_setup_component.opp, "script", {})

    # Testing it doesn't raise
    await opp..services.async_call(
        DOMAIN, SERVICE_TURN_OFF, {"entity_id": []}, blocking=True
    )


async def test_async_get_descriptions_script.opp):
    """Test async_set_service_schema for the script integration."""
    script_config = {
        DOMAIN: {
            "test1": {"sequence": [{"service": "openpeerpowerr.restart"}]},
            "test2": {
                "description": "test2",
                "fields": {
                    "param": {
                        "description": "param_description",
                        "example": "param_example",
                    }
                },
                "sequence": [{"service": "openpeerpowerr.restart"}],
            },
        }
    }

    await async_setup_component.opp, DOMAIN, script_config)
    descriptions = await opp..helpers.service.async_get_all_descriptions()

    assert descriptions[DOMAIN]["test1"]["description"] == ""
    assert not descriptions[DOMAIN]["test1"]["fields"]

    assert descriptions[DOMAIN]["test2"]["description"] == "test2"
    assert (
        descriptions[DOMAIN]["test2"]["fields"]["param"]["description"]
        == "param_description"
    )
    assert (
        descriptions[DOMAIN]["test2"]["fields"]["param"]["example"] == "param_example"
    )


async def test_extraction_functions.opp):
    """Test extraction functions."""
    assert await async_setup_component(
       .opp,
        DOMAIN,
        {
            DOMAIN: {
                "test1": {
                    "sequence": [
                        {
                            "service": "test.script",
                            "data": {"entity_id": "light.in_both"},
                        },
                        {
                            "service": "test.script",
                            "data": {"entity_id": "light.in_first"},
                        },
                        {
                            "entity_id": "light.device_in_both",
                            "domain": "light",
                            "type": "turn_on",
                            "device_id": "device-in-both",
                        },
                    ]
                },
                "test2": {
                    "sequence": [
                        {
                            "service": "test.script",
                            "data": {"entity_id": "light.in_both"},
                        },
                        {
                            "condition": "state",
                            "entity_id": "sensor.condition",
                            "state": "100",
                        },
                        {"scene": "scene.hello"},
                        {
                            "entity_id": "light.device_in_both",
                            "domain": "light",
                            "type": "turn_on",
                            "device_id": "device-in-both",
                        },
                        {
                            "entity_id": "light.device_in_last",
                            "domain": "light",
                            "type": "turn_on",
                            "device_id": "device-in-last",
                        },
                    ],
                },
            }
        },
    )

    assert set(script.scripts_with_entity.opp, "light.in_both")) == {
        "script.test1",
        "script.test2",
    }
    assert set(script.entities_in_script.opp, "script.test1")) == {
        "light.in_both",
        "light.in_first",
    }
    assert set(script.scripts_with_device.opp, "device-in-both")) == {
        "script.test1",
        "script.test2",
    }
    assert set(script.devices_in_script.opp, "script.test2")) == {
        "device-in-both",
        "device-in-last",
    }


async def test_config_basic.opp):
    """Test passing info in config."""
    assert await async_setup_component(
       .opp,
        "script",
        {
            "script": {
                "test_script": {
                    "alias": "Script Name",
                    "icon": "mdi:party",
                    "sequence": [],
                }
            }
        },
    )

    test_script = opp.states.get("script.test_script")
    assert test_script.name == "Script Name"
    assert test_script.attributes["icon"] == "mdi:party"


async def test_logbook_humanify_script_started_event.opp):
    """Test humanifying script started event."""
   .opp.config.components.add("recorder")
    await async_setup_component.opp, DOMAIN, {})
    await async_setup_component.opp, "logbook", {})
    entity_attr_cache = logbook.EntityAttributeCache.opp)

    event1, event2 = list(
        logbook.humanify(
           .opp,
            [
                MockLazyEventPartialState(
                    EVENT_SCRIPT_STARTED,
                    {ATTR_ENTITY_ID: "script.hello", ATTR_NAME: "Hello Script"},
                ),
                MockLazyEventPartialState(
                    EVENT_SCRIPT_STARTED,
                    {ATTR_ENTITY_ID: "script.bye", ATTR_NAME: "Bye Script"},
                ),
            ],
            entity_attr_cache,
            {},
        )
    )

    assert event1["name"] == "Hello Script"
    assert event1["domain"] == "script"
    assert event1["message"] == "started"
    assert event1["entity_id"] == "script.hello"

    assert event2["name"] == "Bye Script"
    assert event2["domain"] == "script"
    assert event2["message"] == "started"
    assert event2["entity_id"] == "script.bye"


@pytest.mark.parametrize("concurrently", [False, True])
async def test_concurrent_script.opp, concurrently):
    """Test calling script concurrently or not."""
    if concurrently:
        call_script_2 = {
            "service": "script.turn_on",
            "data": {"entity_id": "script.script2"},
        }
    else:
        call_script_2 = {"service": "script.script2"}
    assert await async_setup_component(
       .opp,
        "script",
        {
            "script": {
                "script1": {
                    "mode": "parallel",
                    "sequence": [
                        call_script_2,
                        {
                            "wait_template": "{{ is_state('input_boolean.test1', 'on') }}"
                        },
                        {"service": "test.script", "data": {"value": "script1"}},
                    ],
                },
                "script2": {
                    "mode": "parallel",
                    "sequence": [
                        {"service": "test.script", "data": {"value": "script2a"}},
                        {
                            "wait_template": "{{ is_state('input_boolean.test2', 'on') }}"
                        },
                        {"service": "test.script", "data": {"value": "script2b"}},
                    ],
                },
            }
        },
    )

    service_called = asyncio.Event()
    service_values = []

    async def async_service_op.dler(service):
        nonlocal service_values
        service_values.append(service.data.get("value"))
        service_called.set()

   .opp.services.async_register("test", "script", async_service_op.dler)
   .opp.states.async_set("input_boolean.test1", "off")
   .opp.states.async_set("input_boolean.test2", "off")

    await opp..services.async_call("script", "script1")
    await asyncio.wait_for(service_called.wait(), 1)
    service_called.clear()

    assert "script2a" == service_values[-1]
    assert script.is_on.opp, "script.script1")
    assert script.is_on.opp, "script.script2")

    if not concurrently:
       .opp.states.async_set("input_boolean.test2", "on")
        await asyncio.wait_for(service_called.wait(), 1)
        service_called.clear()

        assert "script2b" == service_values[-1]

   .opp.states.async_set("input_boolean.test1", "on")
    await asyncio.wait_for(service_called.wait(), 1)
    service_called.clear()

    assert "script1" == service_values[-1]
    assert concurrently == script.is_on.opp, "script.script2")

    if concurrently:
       .opp.states.async_set("input_boolean.test2", "on")
        await asyncio.wait_for(service_called.wait(), 1)
        service_called.clear()

        assert "script2b" == service_values[-1]

    await opp..async_block_till_done()

    assert not script.is_on.opp, "script.script1")
    assert not script.is_on.opp, "script.script2")


async def test_script_variables.opp, caplog):
    """Test defining scripts."""
    assert await async_setup_component(
       .opp,
        "script",
        {
            "script": {
                "script1": {
                    "variables": {
                        "test_var": "from_config",
                        "templated_config_var": "{{ var_from_service | default('config-default') }}",
                    },
                    "sequence": [
                        {
                            "service": "test.script",
                            "data": {
                                "value": "{{ test_var }}",
                                "templated_config_var": "{{ templated_config_var }}",
                            },
                        },
                    ],
                },
                "script2": {
                    "variables": {
                        "test_var": "from_config",
                    },
                    "sequence": [
                        {
                            "service": "test.script",
                            "data": {
                                "value": "{{ test_var }}",
                            },
                        },
                    ],
                },
                "script3": {
                    "variables": {
                        "test_var": "{{ break + 1 }}",
                    },
                    "sequence": [
                        {
                            "service": "test.script",
                            "data": {
                                "value": "{{ test_var }}",
                            },
                        },
                    ],
                },
            }
        },
    )

    mock_calls = async_mock_service.opp, "test", "script")

    await opp..services.async_call(
        "script", "script1", {"var_from_service": "hello"}, blocking=True
    )

    assert len(mock_calls) == 1
    assert mock_calls[0].data["value"] == "from_config"
    assert mock_calls[0].data["templated_config_var"] == "hello"

    await opp..services.async_call(
        "script", "script1", {"test_var": "from_service"}, blocking=True
    )

    assert len(mock_calls) == 2
    assert mock_calls[1].data["value"] == "from_service"
    assert mock_calls[1].data["templated_config_var"] == "config-default"

    # Call script with vars but no templates in it
    await opp..services.async_call(
        "script", "script2", {"test_var": "from_service"}, blocking=True
    )

    assert len(mock_calls) == 3
    assert mock_calls[2].data["value"] == "from_service"

    assert "Error rendering variables" not in caplog.text
    with pytest.raises(template.TemplateError):
        await opp..services.async_call("script", "script3", blocking=True)
    assert "Error rendering variables" in caplog.text
    assert len(mock_calls) == 3

    await opp..services.async_call("script", "script3", {"break": 0}, blocking=True)

    assert len(mock_calls) == 4
    assert mock_calls[3].data["value"] == 1
