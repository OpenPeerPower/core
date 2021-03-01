"""Define tests for device-related endpoints."""
from datetime import timedelta

from openpeerpower.components.flo.const import DOMAIN as FLO_DOMAIN
from openpeerpower.components.flo.device import FloDeviceDataUpdateCoordinator
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME
from openpeerpower.setup import async_setup_component
from openpeerpower.util import dt

from .common import TEST_PASSWORD, TEST_USER_ID

from tests.common import async_fire_time_changed


async def test_device(opp, config_entry, aioclient_mock_fixture, aioclient_mock):
    """Test Flo by Moen device."""
    config_entry.add_to_opp(opp)
    assert await async_setup_component(
        opp, FLO_DOMAIN, {CONF_USERNAME: TEST_USER_ID, CONF_PASSWORD: TEST_PASSWORD}
    )
    await opp.async_block_till_done()
    assert len(opp.data[FLO_DOMAIN][config_entry.entry_id]["devices"]) == 1

    device: FloDeviceDataUpdateCoordinator = opp.data[FLO_DOMAIN][
        config_entry.entry_id
    ]["devices"][0]
    assert device.api_client is not None
    assert device.available
    assert device.consumption_today == 3.674
    assert device.current_flow_rate == 0
    assert device.current_psi == 54.20000076293945
    assert device.current_system_mode == "home"
    assert device.target_system_mode == "home"
    assert device.firmware_version == "6.1.1"
    assert device.device_type == "flo_device_v2"
    assert device.id == "98765"
    assert device.last_heard_from_time == "2020-07-24T12:45:00Z"
    assert device.location_id == "mmnnoopp"
    assert device.opp is not None
    assert device.temperature == 70
    assert device.mac_address == "111111111111"
    assert device.model == "flo_device_075_v2"
    assert device.manufacturer == "Flo by Moen"
    assert device.device_name == "Flo by Moen flo_device_075_v2"
    assert device.rssi == -47
    assert device.pending_info_alerts_count == 0
    assert device.pending_critical_alerts_count == 0
    assert device.pending_warning_alerts_count == 2
    assert device.has_alerts is True
    assert device.last_known_valve_state == "open"
    assert device.target_valve_state == "open"

    call_count = aioclient_mock.call_count

    async_fire_time_changed(opp, dt.utcnow() + timedelta(seconds=90))
    await opp.async_block_till_done()

    assert aioclient_mock.call_count == call_count + 2
