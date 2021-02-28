"""Test the SmartTub sensor platform."""

from . import trigger_update


async def test_state_update(spa, setup_entry, opp, smarttub_api):
    """Test the state entity."""

    entity_id = f"sensor.{spa.brand}_{spa.model}_state"
    state = opp.states.get(entity_id)
    assert state is not None
    assert state.state == "normal"

    spa.get_status.return_value["state"] = "BAD"
    await trigger_update(opp)
    state = opp.states.get(entity_id)
    assert state is not None
    assert state.state == "bad"
