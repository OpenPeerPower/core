"""Tests for homekit_controller init."""

from unittest.mock import patch

from aiohomekit.model.characteristics import CharacteristicsTypes
from aiohomekit.model.services import ServicesTypes

from openpeerpower.const import EVENT_OPENPEERPOWER_STOP

from tests.components.homekit_controller.common import setup_test_component


def create_motion_sensor_service(accessory):
    """Define motion characteristics as per page 225 of HAP spec."""
    service = accessory.add_service(ServicesTypes.MOTION_SENSOR)
    cur_state = service.add_char(CharacteristicsTypes.MOTION_DETECTED)
    cur_state.value = 0


async def test_unload_on_stop(opp, utcnow):
    """Test async_unload is called on stop."""
    await setup_test_component(opp, create_motion_sensor_service)
    with patch(
        "openpeerpower.components.homekit_controller.HKDevice.async_unload"
    ) as async_unlock_mock:
        opp.bus.async_fire(EVENT_OPENPEERPOWER_STOP)
        await opp.async_block_till_done()

    assert async_unlock_mock.called
