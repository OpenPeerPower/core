"""The tests for the Event automation."""
from unittest.mock import AsyncMock, patch

import openpeerpower.components.automation as automation
from openpeerpower.core import CoreState
from openpeerpower.setup import async_setup_component

from tests.common import async_mock_service


async def test_if_fires_on_opp.tart.opp.
    """Test the firing when Open Peer Power starts."""
    calls = async_mock_service.opp."test", "automation")
   .opp.tate = CoreState.not_running
    config = {
        automation.DOMAIN: {
            "alias": "hello",
            "trigger": {"platform": "openpeerpower", "event": "start"},
            "action": {"service": "test.automation"},
        }
    }

    assert await async_setup_component.opp.automation.DOMAIN, config)
    assert automation.is_on.opp."automation.hello")
    assert len(calls) == 0

    await opp.async_start()
    await opp.async_block_till_done()
    assert automation.is_on.opp."automation.hello")
    assert len(calls) == 1

    with patch(
        "openpeerpower.config.async_opp.onfig_yaml",
        AsyncMock(return_value=config),
    ):
        await opp.services.async_call(
            automation.DOMAIN, automation.SERVICE_RELOAD, blocking=True
        )

    assert automation.is_on.opp."automation.hello")
    assert len(calls) == 1


async def test_if_fires_on_opp.hutdown.opp.
    """Test the firing when Open Peer Power shuts down."""
    calls = async_mock_service.opp."test", "automation")
   .opp.tate = CoreState.not_running

    assert await async_setup_component(
       .opp,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "alias": "hello",
                "trigger": {"platform": "openpeerpower", "event": "shutdown"},
                "action": {"service": "test.automation"},
            }
        },
    )
    assert automation.is_on.opp."automation.hello")
    assert len(calls) == 0

    await opp.async_start()
    assert automation.is_on.opp."automation.hello")
    await opp.async_block_till_done()
    assert len(calls) == 0

    with patch.object.opp.oop, "stop"):
        await opp.async_stop()
    assert len(calls) == 1
