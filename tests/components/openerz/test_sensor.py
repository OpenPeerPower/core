"""Tests for OpenERZ component."""
from unittest.mock import MagicMock, patch

from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.setup import async_setup_component

MOCK_CONFIG = {
    "sensor": {
        "platform": "openerz",
        "name": "test_name",
        "zip": 1234,
        "waste_type": "glass",
    }
}


async def test_sensor_state.opp):
    """Test whether default waste type set properly."""
    with patch(
        "openpeerpower.components.openerz.sensor.OpenERZConnector"
    ) as patched_connector:
        pickup_instance = MagicMock()
        pickup_instance.find_next_pickup.return_value = "2020-12-12"
        patched_connector.return_value = pickup_instance

        await async_setup_component(opp, SENSOR_DOMAIN, MOCK_CONFIG)
        await opp.async_block_till_done()

        entity_id = "sensor.test_name"
        test_openerz_state = opp.states.get(entity_id)

        assert test_openerz_state.state == "2020-12-12"
        assert test_openerz_state.name == "test_name"
        pickup_instance.find_next_pickup.assert_called_once()
