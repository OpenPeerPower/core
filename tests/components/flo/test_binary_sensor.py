"""Test Flo by Moen binary sensor entities."""
from openpeerpower.components.flo.const import DOMAIN as FLO_DOMAIN
from openpeerpower.const import (
    ATTR_FRIENDLY_NAME,
    CONF_PASSWORD,
    CONF_USERNAME,
    STATE_OFF,
    STATE_ON,
)
from openpeerpower.setup import async_setup_component

from .common import TEST_PASSWORD, TEST_USER_ID


async def test_binary_sensors(opp, config_entry, aioclient_mock_fixture):
    """Test Flo by Moen sensors."""
    config_entry.add_to_opp(opp)
    assert await async_setup_component(
        opp, FLO_DOMAIN, {CONF_USERNAME: TEST_USER_ID, CONF_PASSWORD: TEST_PASSWORD}
    )
    await opp.async_block_till_done()

    assert len(opp.data[FLO_DOMAIN][config_entry.entry_id]["devices"]) == 2

    valve_state = opp.states.get("binary_sensor.pending_system_alerts")
    assert valve_state.state == STATE_ON
    assert valve_state.attributes.get("info") == 0
    assert valve_state.attributes.get("warning") == 2
    assert valve_state.attributes.get("critical") == 0
    assert valve_state.attributes.get(ATTR_FRIENDLY_NAME) == "Pending System Alerts"

    detector_state = opp.states.get("binary_sensor.water_detected")
    assert detector_state.state == STATE_OFF
