"""Tests for the switch domain for Flo by Moen."""
from openpeerpower.components.flo.const import DOMAIN as FLO_DOMAIN
from openpeerpower.components.switch import DOMAIN
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME, STATE_OFF, STATE_ON
from openpeerpower.setup import async_setup_component

from .common import TEST_PASSWORD, TEST_USER_ID


async def test_valve_switches(opp, config_entry, aioclient_mock_fixture):
    """Test Flo by Moen valve switches."""
    config_entry.add_to(opp.opp)
    assert await async_setup_component(
        opp. FLO_DOMAIN, {CONF_USERNAME: TEST_USER_ID, CONF_PASSWORD: TEST_PASSWORD}
    )
    await opp.async_block_till_done()

    assert len.opp.data[FLO_DOMAIN][config_entry.entry_id]["devices"]) == 1

    entity_id = "switch.shutoff_valve"
    assert opp.states.get(entity_id).state == STATE_ON

    await opp.services.async_call(
        DOMAIN, "turn_off", {"entity_id": entity_id}, blocking=True
    )
    assert opp.states.get(entity_id).state == STATE_OFF

    await opp.services.async_call(
        DOMAIN, "turn_on", {"entity_id": entity_id}, blocking=True
    )
    assert opp.states.get(entity_id).state == STATE_ON
