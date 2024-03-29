"""The scene tests for the myq platform."""

from openpeerpower.const import STATE_CLOSED

from .util import async_init_integration


async def test_create_covers(opp):
    """Test creation of covers."""

    await async_init_integration(opp)

    state = opp.states.get("cover.large_garage_door")
    assert state.state == STATE_CLOSED
    expected_attributes = {
        "device_class": "garage",
        "friendly_name": "Large Garage Door",
        "supported_features": 3,
    }
    # Only test for a subset of attributes in case
    # OPP changes the implementation and a new one appears
    assert all(
        state.attributes[key] == expected_attributes[key] for key in expected_attributes
    )

    state = opp.states.get("cover.small_garage_door")
    assert state.state == STATE_CLOSED
    expected_attributes = {
        "device_class": "garage",
        "friendly_name": "Small Garage Door",
        "supported_features": 3,
    }
    # Only test for a subset of attributes in case
    # OPP changes the implementation and a new one appears
    assert all(
        state.attributes[key] == expected_attributes[key] for key in expected_attributes
    )

    state = opp.states.get("cover.gate")
    assert state.state == STATE_CLOSED
    expected_attributes = {
        "device_class": "gate",
        "friendly_name": "Gate",
        "supported_features": 3,
    }
    # Only test for a subset of attributes in case
    # OPP changes the implementation and a new one appears
    assert all(
        state.attributes[key] == expected_attributes[key] for key in expected_attributes
    )
