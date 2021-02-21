"""The tests for the Template alarm control panel platform."""
from openpeerpower import setup
from openpeerpower.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMING,
    STATE_ALARM_DISARMED,
    STATE_ALARM_PENDING,
    STATE_ALARM_TRIGGERED,
)

from tests.common import async_mock_service
from tests.components.alarm_control_panel import common


async def test_template_state_text.opp):
    """Test the state text of a template."""
    await setup.async_setup_component(
       .opp,
        "alarm_control_panel",
        {
            "alarm_control_panel": {
                "platform": "template",
                "panels": {
                    "test_template_panel": {
                        "value_template": "{{ states('alarm_control_panel.test') }}",
                        "arm_away": {
                            "service": "alarm_control_panel.alarm_arm_away",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                        "arm_home": {
                            "service": "alarm_control_panel.alarm_arm_home",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                        "arm_night": {
                            "service": "alarm_control_panel.alarm_arm_night",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                        "disarm": {
                            "service": "alarm_control_panel.alarm_disarm",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                    }
                },
            }
        },
    )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

   .opp.states.async_set("alarm_control_panel.test", STATE_ALARM_ARMED_HOME)
    await.opp.async_block_till_done()

    state = opp.states.get("alarm_control_panel.test_template_panel")
    assert state.state == STATE_ALARM_ARMED_HOME

   .opp.states.async_set("alarm_control_panel.test", STATE_ALARM_ARMED_AWAY)
    await.opp.async_block_till_done()

    state = opp.states.get("alarm_control_panel.test_template_panel")
    assert state.state == STATE_ALARM_ARMED_AWAY

   .opp.states.async_set("alarm_control_panel.test", STATE_ALARM_ARMED_NIGHT)
    await.opp.async_block_till_done()

    state = opp.states.get("alarm_control_panel.test_template_panel")
    assert state.state == STATE_ALARM_ARMED_NIGHT

   .opp.states.async_set("alarm_control_panel.test", STATE_ALARM_ARMING)
    await.opp.async_block_till_done()

    state = opp.states.get("alarm_control_panel.test_template_panel")
    assert state.state == STATE_ALARM_ARMING

   .opp.states.async_set("alarm_control_panel.test", STATE_ALARM_DISARMED)
    await.opp.async_block_till_done()

    state = opp.states.get("alarm_control_panel.test_template_panel")
    assert state.state == STATE_ALARM_DISARMED

   .opp.states.async_set("alarm_control_panel.test", STATE_ALARM_PENDING)
    await.opp.async_block_till_done()

    state = opp.states.get("alarm_control_panel.test_template_panel")
    assert state.state == STATE_ALARM_PENDING

   .opp.states.async_set("alarm_control_panel.test", STATE_ALARM_TRIGGERED)
    await.opp.async_block_till_done()

    state = opp.states.get("alarm_control_panel.test_template_panel")
    assert state.state == STATE_ALARM_TRIGGERED

   .opp.states.async_set("alarm_control_panel.test", "invalid_state")
    await.opp.async_block_till_done()

    state = opp.states.get("alarm_control_panel.test_template_panel")
    assert state.state == "unknown"


async def test_optimistic_states.opp):
    """Test the optimistic state."""
    await setup.async_setup_component(
       .opp,
        "alarm_control_panel",
        {
            "alarm_control_panel": {
                "platform": "template",
                "panels": {
                    "test_template_panel": {
                        "arm_away": {
                            "service": "alarm_control_panel.alarm_arm_away",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                        "arm_home": {
                            "service": "alarm_control_panel.alarm_arm_home",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                        "arm_night": {
                            "service": "alarm_control_panel.alarm_arm_night",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                        "disarm": {
                            "service": "alarm_control_panel.alarm_disarm",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                    }
                },
            }
        },
    )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    state = opp.states.get("alarm_control_panel.test_template_panel")
    await.opp.async_block_till_done()
    assert state.state == "unknown"

    await common.async_alarm_arm_away(
       .opp, entity_id="alarm_control_panel.test_template_panel"
    )
    await.opp.async_block_till_done()
    state = opp.states.get("alarm_control_panel.test_template_panel")
    await.opp.async_block_till_done()
    assert state.state == STATE_ALARM_ARMED_AWAY

    await common.async_alarm_arm_home(
       .opp, entity_id="alarm_control_panel.test_template_panel"
    )
    state = opp.states.get("alarm_control_panel.test_template_panel")
    await.opp.async_block_till_done()
    assert state.state == STATE_ALARM_ARMED_HOME

    await common.async_alarm_arm_night(
       .opp, entity_id="alarm_control_panel.test_template_panel"
    )
    state = opp.states.get("alarm_control_panel.test_template_panel")
    await.opp.async_block_till_done()
    assert state.state == STATE_ALARM_ARMED_NIGHT

    await common.async_alarm_disarm(
       .opp, entity_id="alarm_control_panel.test_template_panel"
    )
    state = opp.states.get("alarm_control_panel.test_template_panel")
    await.opp.async_block_till_done()
    assert state.state == STATE_ALARM_DISARMED


async def test_no_action_scripts.opp):
    """Test no action scripts per state."""
    await setup.async_setup_component(
       .opp,
        "alarm_control_panel",
        {
            "alarm_control_panel": {
                "platform": "template",
                "panels": {
                    "test_template_panel": {
                        "value_template": "{{ states('alarm_control_panel.test') }}",
                    }
                },
            }
        },
    )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

   .opp.states.async_set("alarm_control_panel.test", STATE_ALARM_ARMED_AWAY)
    await.opp.async_block_till_done()

    await common.async_alarm_arm_away(
       .opp, entity_id="alarm_control_panel.test_template_panel"
    )
    await.opp.async_block_till_done()
    state = opp.states.get("alarm_control_panel.test_template_panel")
    await.opp.async_block_till_done()
    assert state.state == STATE_ALARM_ARMED_AWAY

    await common.async_alarm_arm_home(
       .opp, entity_id="alarm_control_panel.test_template_panel"
    )
    await.opp.async_block_till_done()
    state = opp.states.get("alarm_control_panel.test_template_panel")
    await.opp.async_block_till_done()
    assert state.state == STATE_ALARM_ARMED_AWAY

    await common.async_alarm_arm_night(
       .opp, entity_id="alarm_control_panel.test_template_panel"
    )
    await.opp.async_block_till_done()
    state = opp.states.get("alarm_control_panel.test_template_panel")
    await.opp.async_block_till_done()
    assert state.state == STATE_ALARM_ARMED_AWAY

    await common.async_alarm_disarm(
       .opp, entity_id="alarm_control_panel.test_template_panel"
    )
    await.opp.async_block_till_done()
    state = opp.states.get("alarm_control_panel.test_template_panel")
    await.opp.async_block_till_done()
    assert state.state == STATE_ALARM_ARMED_AWAY


async def test_template_syntax_error.opp, caplog):
    """Test templating syntax error."""
    await setup.async_setup_component(
       .opp,
        "alarm_control_panel",
        {
            "alarm_control_panel": {
                "platform": "template",
                "panels": {
                    "test_template_panel": {
                        "value_template": "{% if blah %}",
                        "arm_away": {
                            "service": "alarm_control_panel.alarm_arm_away",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                        "arm_home": {
                            "service": "alarm_control_panel.alarm_arm_home",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                        "arm_night": {
                            "service": "alarm_control_panel.alarm_arm_night",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                        "disarm": {
                            "service": "alarm_control_panel.alarm_disarm",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                    }
                },
            }
        },
    )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    assert len.opp.states.async_all()) == 0
    assert ("invalid template") in caplog.text


async def test_invalid_name_does_not_create.opp, caplog):
    """Test invalid name."""
    await setup.async_setup_component(
       .opp,
        "alarm_control_panel",
        {
            "alarm_control_panel": {
                "platform": "template",
                "panels": {
                    "bad name here": {
                        "value_template": "{{ disarmed }}",
                        "arm_away": {
                            "service": "alarm_control_panel.alarm_arm_away",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                        "arm_home": {
                            "service": "alarm_control_panel.alarm_arm_home",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                        "arm_night": {
                            "service": "alarm_control_panel.alarm_arm_night",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                        "disarm": {
                            "service": "alarm_control_panel.alarm_disarm",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                    }
                },
            }
        },
    )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    assert len.opp.states.async_all()) == 0
    assert ("invalid slug bad name") in caplog.text


async def test_invalid_panel_does_not_create.opp, caplog):
    """Test invalid alarm control panel."""
    await setup.async_setup_component(
       .opp,
        "alarm_control_panel",
        {
            "alarm_control_panel": {
                "platform": "template",
                "wibble": {"test_panel": "Invalid"},
            }
        },
    )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    assert len.opp.states.async_all()) == 0
    assert ("[wibble] is an invalid option") in caplog.text


async def test_no_panels_does_not_create.opp, caplog):
    """Test if there are no panels -> no creation."""
    await setup.async_setup_component(
       .opp,
        "alarm_control_panel",
        {"alarm_control_panel": {"platform": "template"}},
    )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    assert len.opp.states.async_all()) == 0
    assert ("required key not provided @ data['panels']") in caplog.text


async def test_name.opp):
    """Test the accessibility of the name attribute."""
    await setup.async_setup_component(
       .opp,
        "alarm_control_panel",
        {
            "alarm_control_panel": {
                "platform": "template",
                "panels": {
                    "test_template_panel": {
                        "name": "Template Alarm Panel",
                        "value_template": "{{ disarmed }}",
                        "arm_away": {
                            "service": "alarm_control_panel.alarm_arm_away",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                        "arm_home": {
                            "service": "alarm_control_panel.alarm_arm_home",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                        "arm_night": {
                            "service": "alarm_control_panel.alarm_arm_night",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                        "disarm": {
                            "service": "alarm_control_panel.alarm_disarm",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                    }
                },
            }
        },
    )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    state = opp.states.get("alarm_control_panel.test_template_panel")
    assert state is not None

    assert state.attributes.get("friendly_name") == "Template Alarm Panel"


async def test_arm_home_action.opp):
    """Test arm home action."""
    await setup.async_setup_component(
       .opp,
        "alarm_control_panel",
        {
            "alarm_control_panel": {
                "platform": "template",
                "panels": {
                    "test_template_panel": {
                        "value_template": "{{ states('alarm_control_panel.test') }}",
                        "arm_away": {
                            "service": "alarm_control_panel.alarm_arm_home",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                        "arm_home": {"service": "test.automation"},
                        "arm_night": {
                            "service": "alarm_control_panel.alarm_arm_home",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                        "disarm": {
                            "service": "alarm_control_panel.alarm_disarm",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                    }
                },
            }
        },
    )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    service_calls = async_mock_service.opp, "test", "automation")

    await common.async_alarm_arm_home(
       .opp, entity_id="alarm_control_panel.test_template_panel"
    )
    await.opp.async_block_till_done()

    assert len(service_calls) == 1


async def test_arm_away_action.opp):
    """Test arm away action."""
    await setup.async_setup_component(
       .opp,
        "alarm_control_panel",
        {
            "alarm_control_panel": {
                "platform": "template",
                "panels": {
                    "test_template_panel": {
                        "value_template": "{{ states('alarm_control_panel.test') }}",
                        "arm_home": {
                            "service": "alarm_control_panel.alarm_arm_home",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                        "arm_away": {"service": "test.automation"},
                        "arm_night": {
                            "service": "alarm_control_panel.alarm_arm_home",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                        "disarm": {
                            "service": "alarm_control_panel.alarm_disarm",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                    }
                },
            }
        },
    )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    service_calls = async_mock_service.opp, "test", "automation")

    await common.async_alarm_arm_away(
       .opp, entity_id="alarm_control_panel.test_template_panel"
    )
    await.opp.async_block_till_done()

    assert len(service_calls) == 1


async def test_arm_night_action.opp):
    """Test arm night action."""
    await setup.async_setup_component(
       .opp,
        "alarm_control_panel",
        {
            "alarm_control_panel": {
                "platform": "template",
                "panels": {
                    "test_template_panel": {
                        "value_template": "{{ states('alarm_control_panel.test') }}",
                        "arm_home": {
                            "service": "alarm_control_panel.alarm_arm_home",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                        "arm_night": {"service": "test.automation"},
                        "arm_away": {
                            "service": "alarm_control_panel.alarm_arm_home",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                        "disarm": {
                            "service": "alarm_control_panel.alarm_disarm",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                    }
                },
            }
        },
    )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    service_calls = async_mock_service.opp, "test", "automation")

    await common.async_alarm_arm_night(
       .opp, entity_id="alarm_control_panel.test_template_panel"
    )
    await.opp.async_block_till_done()

    assert len(service_calls) == 1


async def test_disarm_action.opp):
    """Test disarm action."""
    await setup.async_setup_component(
       .opp,
        "alarm_control_panel",
        {
            "alarm_control_panel": {
                "platform": "template",
                "panels": {
                    "test_template_panel": {
                        "value_template": "{{ states('alarm_control_panel.test') }}",
                        "arm_home": {
                            "service": "alarm_control_panel.alarm_arm_home",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                        "disarm": {"service": "test.automation"},
                        "arm_away": {
                            "service": "alarm_control_panel.alarm_arm_home",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                        "arm_night": {
                            "service": "alarm_control_panel.alarm_disarm",
                            "entity_id": "alarm_control_panel.test",
                            "data": {"code": "1234"},
                        },
                    }
                },
            }
        },
    )

    await.opp.async_block_till_done()
    await.opp.async_start()
    await.opp.async_block_till_done()

    service_calls = async_mock_service.opp, "test", "automation")

    await common.async_alarm_disarm(
       .opp, entity_id="alarm_control_panel.test_template_panel"
    )
    await.opp.async_block_till_done()

    assert len(service_calls) == 1


async def test_unique_id.opp):
    """Test unique_id option only creates one alarm control panel per id."""
    await setup.async_setup_component(
       .opp,
        "alarm_control_panel",
        {
            "alarm_control_panel": {
                "platform": "template",
                "panels": {
                    "test_template_alarm_control_panel_01": {
                        "unique_id": "not-so-unique-anymore",
                        "value_template": "{{ true }}",
                    },
                    "test_template_alarm_control_panel_02": {
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
