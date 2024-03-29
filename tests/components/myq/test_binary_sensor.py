"""The scene tests for the myq platform."""

from openpeerpower.const import STATE_ON

from .util import async_init_integration


async def test_create_binary_sensors(opp):
    """Test creation of binary_sensors."""

    await async_init_integration(opp)

    state = opp.states.get("binary_sensor.happy_place_myq_gateway")
    assert state.state == STATE_ON
    expected_attributes = {"device_class": "connectivity"}
    # Only test for a subset of attributes in case
    # OPP changes the implementation and a new one appears
    assert all(
        state.attributes[key] == expected_attributes[key] for key in expected_attributes
    )
