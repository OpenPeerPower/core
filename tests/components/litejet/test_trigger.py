"""The tests for the litejet component."""
from datetime import timedelta
import logging
from unittest import mock
from unittest.mock import patch

import pytest

from openpeerpower import setup
import openpeerpower.components.automation as automation
import openpeerpower.util.dt as dt_util

from . import async_init_integration

from tests.common import async_fire_time_changed, async_mock_service
from tests.components.blueprint.conftest import stub_blueprint_populate  # noqa: F401

_LOGGER = logging.getLogger(__name__)

ENTITY_SWITCH = "switch.mock_switch_1"
ENTITY_SWITCH_NUMBER = 1
ENTITY_OTHER_SWITCH = "switch.mock_switch_2"
ENTITY_OTHER_SWITCH_NUMBER = 2


@pytest.fixture
def calls(opp):
    """Track calls to a mock service."""
    return async_mock_service(opp, "test", "automation")


async def simulate_press(opp, mock_litejet, number):
    """Test to simulate a press."""
    _LOGGER.info("*** simulate press of %d", number)
    callback = mock_litejet.switch_pressed_callbacks.get(number)
    with mock.patch(
        "openpeerpower.helpers.condition.dt_util.utcnow",
        return_value=mock_litejet.start_time + mock_litejet.last_delta,
    ):
        if callback is not None:
            await opp.async_add_executor_job(callback)
        await opp.async_block_till_done()


async def simulate_release(opp, mock_litejet, number):
    """Test to simulate releasing."""
    _LOGGER.info("*** simulate release of %d", number)
    callback = mock_litejet.switch_released_callbacks.get(number)
    with mock.patch(
        "openpeerpower.helpers.condition.dt_util.utcnow",
        return_value=mock_litejet.start_time + mock_litejet.last_delta,
    ):
        if callback is not None:
            await opp.async_add_executor_job(callback)
        await opp.async_block_till_done()


async def simulate_time(opp, mock_litejet, delta):
    """Test to simulate time."""
    _LOGGER.info(
        "*** simulate time change by %s: %s", delta, mock_litejet.start_time + delta
    )
    mock_litejet.last_delta = delta
    with mock.patch(
        "openpeerpower.helpers.condition.dt_util.utcnow",
        return_value=mock_litejet.start_time + delta,
    ):
        _LOGGER.info("now=%s", dt_util.utcnow())
        async_fire_time_changed(opp, mock_litejet.start_time + delta)
        await opp.async_block_till_done()
        _LOGGER.info("done with now=%s", dt_util.utcnow())


async def setup_automation(opp, trigger):
    """Test setting up the automation."""
    await async_init_integration(opp, use_switch=True)
    assert await setup.async_setup_component(
        opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "alias": "My Test",
                    "trigger": trigger,
                    "action": {"service": "test.automation"},
                }
            ]
        },
    )
    await opp.async_block_till_done()


async def test_simple(opp, calls, mock_litejet):
    """Test the simplest form of a LiteJet trigger."""
    await setup_automation(
        opp, {"platform": "litejet", "number": ENTITY_OTHER_SWITCH_NUMBER}
    )

    await simulate_press(opp, mock_litejet, ENTITY_OTHER_SWITCH_NUMBER)
    await simulate_release(opp, mock_litejet, ENTITY_OTHER_SWITCH_NUMBER)

    assert len(calls) == 1


async def test_held_more_than_short(opp, calls, mock_litejet):
    """Test a too short hold."""
    await setup_automation(
        opp,
        {
            "platform": "litejet",
            "number": ENTITY_OTHER_SWITCH_NUMBER,
            "held_more_than": {"milliseconds": "200"},
        },
    )

    await simulate_press(opp, mock_litejet, ENTITY_OTHER_SWITCH_NUMBER)
    await simulate_time(opp, mock_litejet, timedelta(seconds=0.1))
    await simulate_release(opp, mock_litejet, ENTITY_OTHER_SWITCH_NUMBER)
    assert len(calls) == 0


async def test_held_more_than_long(opp, calls, mock_litejet):
    """Test a hold that is long enough."""
    await setup_automation(
        opp,
        {
            "platform": "litejet",
            "number": ENTITY_OTHER_SWITCH_NUMBER,
            "held_more_than": {"milliseconds": "200"},
        },
    )

    await simulate_press(opp, mock_litejet, ENTITY_OTHER_SWITCH_NUMBER)
    assert len(calls) == 0
    await simulate_time(opp, mock_litejet, timedelta(seconds=0.3))
    assert len(calls) == 1
    await simulate_release(opp, mock_litejet, ENTITY_OTHER_SWITCH_NUMBER)
    assert len(calls) == 1


async def test_held_less_than_short(opp, calls, mock_litejet):
    """Test a hold that is short enough."""
    await setup_automation(
        opp,
        {
            "platform": "litejet",
            "number": ENTITY_OTHER_SWITCH_NUMBER,
            "held_less_than": {"milliseconds": "200"},
        },
    )

    await simulate_press(opp, mock_litejet, ENTITY_OTHER_SWITCH_NUMBER)
    await simulate_time(opp, mock_litejet, timedelta(seconds=0.1))
    assert len(calls) == 0
    await simulate_release(opp, mock_litejet, ENTITY_OTHER_SWITCH_NUMBER)
    assert len(calls) == 1


async def test_held_less_than_long(opp, calls, mock_litejet):
    """Test a hold that is too long."""
    await setup_automation(
        opp,
        {
            "platform": "litejet",
            "number": ENTITY_OTHER_SWITCH_NUMBER,
            "held_less_than": {"milliseconds": "200"},
        },
    )

    await simulate_press(opp, mock_litejet, ENTITY_OTHER_SWITCH_NUMBER)
    assert len(calls) == 0
    await simulate_time(opp, mock_litejet, timedelta(seconds=0.3))
    assert len(calls) == 0
    await simulate_release(opp, mock_litejet, ENTITY_OTHER_SWITCH_NUMBER)
    assert len(calls) == 0


async def test_held_in_range_short(opp, calls, mock_litejet):
    """Test an in-range trigger with a too short hold."""
    await setup_automation(
        opp,
        {
            "platform": "litejet",
            "number": ENTITY_OTHER_SWITCH_NUMBER,
            "held_more_than": {"milliseconds": "100"},
            "held_less_than": {"milliseconds": "300"},
        },
    )

    await simulate_press(opp, mock_litejet, ENTITY_OTHER_SWITCH_NUMBER)
    await simulate_time(opp, mock_litejet, timedelta(seconds=0.05))
    await simulate_release(opp, mock_litejet, ENTITY_OTHER_SWITCH_NUMBER)
    assert len(calls) == 0


async def test_held_in_range_just_right(opp, calls, mock_litejet):
    """Test an in-range trigger with a just right hold."""
    await setup_automation(
        opp,
        {
            "platform": "litejet",
            "number": ENTITY_OTHER_SWITCH_NUMBER,
            "held_more_than": {"milliseconds": "100"},
            "held_less_than": {"milliseconds": "300"},
        },
    )

    await simulate_press(opp, mock_litejet, ENTITY_OTHER_SWITCH_NUMBER)
    assert len(calls) == 0
    await simulate_time(opp, mock_litejet, timedelta(seconds=0.2))
    assert len(calls) == 0
    await simulate_release(opp, mock_litejet, ENTITY_OTHER_SWITCH_NUMBER)
    assert len(calls) == 1


async def test_held_in_range_long(opp, calls, mock_litejet):
    """Test an in-range trigger with a too long hold."""
    await setup_automation(
        opp,
        {
            "platform": "litejet",
            "number": ENTITY_OTHER_SWITCH_NUMBER,
            "held_more_than": {"milliseconds": "100"},
            "held_less_than": {"milliseconds": "300"},
        },
    )

    await simulate_press(opp, mock_litejet, ENTITY_OTHER_SWITCH_NUMBER)
    assert len(calls) == 0
    await simulate_time(opp, mock_litejet, timedelta(seconds=0.4))
    assert len(calls) == 0
    await simulate_release(opp, mock_litejet, ENTITY_OTHER_SWITCH_NUMBER)
    assert len(calls) == 0


async def test_reload(opp, calls, mock_litejet):
    """Test reloading automation."""
    await setup_automation(
        opp,
        {
            "platform": "litejet",
            "number": ENTITY_OTHER_SWITCH_NUMBER,
            "held_more_than": {"milliseconds": "100"},
            "held_less_than": {"milliseconds": "300"},
        },
    )

    with patch(
        "openpeerpower.config.load_yaml_config_file",
        autospec=True,
        return_value={
            "automation": {
                "trigger": {
                    "platform": "litejet",
                    "number": ENTITY_OTHER_SWITCH_NUMBER,
                    "held_more_than": {"milliseconds": "1000"},
                },
                "action": {"service": "test.automation"},
            }
        },
    ):
        await opp.services.async_call(
            "automation",
            "reload",
            blocking=True,
        )
        await opp.async_block_till_done()

    await simulate_press(opp, mock_litejet, ENTITY_OTHER_SWITCH_NUMBER)
    assert len(calls) == 0
    await simulate_time(opp, mock_litejet, timedelta(seconds=0.5))
    assert len(calls) == 0
    await simulate_time(opp, mock_litejet, timedelta(seconds=1.25))
    assert len(calls) == 1
