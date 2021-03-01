"""Test the services for the Flo by Moen integration."""
from openpeerpower.components.flo.const import DOMAIN as FLO_DOMAIN
from openpeerpower.components.flo.switch import (
    ATTR_REVERT_TO_MODE,
    ATTR_SLEEP_MINUTES,
    SERVICE_RUN_HEALTH_TEST,
    SERVICE_SET_AWAY_MODE,
    SERVICE_SET_HOME_MODE,
    SERVICE_SET_SLEEP_MODE,
    SYSTEM_MODE_HOME,
)
from openpeerpower.const import ATTR_ENTITY_ID, CONF_PASSWORD, CONF_USERNAME
from openpeerpower.setup import async_setup_component

from .common import TEST_PASSWORD, TEST_USER_ID

SWITCH_ENTITY_ID = "switch.shutoff_valve"


async def test_services(opp, config_entry, aioclient_mock_fixture, aioclient_mock):
    """Test Flo services."""
    config_entry.add_to_opp(opp)
    assert await async_setup_component(
        opp, FLO_DOMAIN, {CONF_USERNAME: TEST_USER_ID, CONF_PASSWORD: TEST_PASSWORD}
    )
    await opp.async_block_till_done()

    assert len(opp.data[FLO_DOMAIN][config_entry.entry_id]["devices"]) == 1
    assert aioclient_mock.call_count == 4

    await opp.services.async_call(
        FLO_DOMAIN,
        SERVICE_RUN_HEALTH_TEST,
        {ATTR_ENTITY_ID: SWITCH_ENTITY_ID},
        blocking=True,
    )
    await opp.async_block_till_done()
    assert aioclient_mock.call_count == 5

    await opp.services.async_call(
        FLO_DOMAIN,
        SERVICE_SET_AWAY_MODE,
        {ATTR_ENTITY_ID: SWITCH_ENTITY_ID},
        blocking=True,
    )
    await opp.async_block_till_done()
    assert aioclient_mock.call_count == 6

    await opp.services.async_call(
        FLO_DOMAIN,
        SERVICE_SET_HOME_MODE,
        {ATTR_ENTITY_ID: SWITCH_ENTITY_ID},
        blocking=True,
    )
    await opp.async_block_till_done()
    assert aioclient_mock.call_count == 7

    await opp.services.async_call(
        FLO_DOMAIN,
        SERVICE_SET_SLEEP_MODE,
        {
            ATTR_ENTITY_ID: SWITCH_ENTITY_ID,
            ATTR_REVERT_TO_MODE: SYSTEM_MODE_HOME,
            ATTR_SLEEP_MINUTES: 120,
        },
        blocking=True,
    )
    await opp.async_block_till_done()
    assert aioclient_mock.call_count == 8
