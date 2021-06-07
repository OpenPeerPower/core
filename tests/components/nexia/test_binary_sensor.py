"""The binary_sensor tests for the nexia platform."""

from openpeerpower.const import STATE_OFF, STATE_ON

from .util import async_init_integration


async def test_create_binary_sensors(opp):
    """Test creation of binary sensors."""

    await async_init_integration(opp)

    state = opp.states.get("binary_sensor.master_suite_blower_active")
    assert state.state == STATE_ON
    expected_attributes = {
        "attribution": "Data provided by mynexia.com",
        "friendly_name": "Master Suite Blower Active",
    }
    # Only test for a subset of attributes in case
    # OPP changes the implementation and a new one appears
    assert all(
        state.attributes[key] == expected_attributes[key] for key in expected_attributes
    )

    state = opp.states.get("binary_sensor.downstairs_east_wing_blower_active")
    assert state.state == STATE_OFF
    expected_attributes = {
        "attribution": "Data provided by mynexia.com",
        "friendly_name": "Downstairs East Wing Blower Active",
    }
    # Only test for a subset of attributes in case
    # OPP changes the implementation and a new one appears
    assert all(
        state.attributes[key] == expected_attributes[key] for key in expected_attributes
    )
