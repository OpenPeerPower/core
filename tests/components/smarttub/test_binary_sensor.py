"""Test the SmartTub binary sensor platform."""

from openpeerpower.components.binary_sensor import DEVICE_CLASS_CONNECTIVITY, STATE_ON


async def test_binary_sensors(spa, setup_entry, opp):
    """Test the binary sensors."""

    entity_id = f"binary_sensor.{spa.brand}_{spa.model}_online"
    state = opp.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes.get("device_class") == DEVICE_CLASS_CONNECTIVITY
