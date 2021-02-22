"""Test discovery of entities for device-specific schemas for the Z-Wave JS integration."""


async def test_iblinds_v2.opp, client, iblinds_v2, integration):
    """Test that an iBlinds v2.0 multilevel switch value is discovered as a cover."""

    node = iblinds_v2
    assert node.device_class.specific == "Unused"

    state = opp.states.get("light.window_blind_controller")
    assert not state

    state = opp.states.get("cover.window_blind_controller")
    assert state
