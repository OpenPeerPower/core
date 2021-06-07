"""Test the surepetcare sensor platform."""
from openpeerpower.components.surepetcare.const import DOMAIN
from openpeerpower.helpers import entity_registry as er
from openpeerpower.setup import async_setup_component

from . import HOUSEHOLD_ID, MOCK_CONFIG

EXPECTED_ENTITY_IDS = {
    "sensor.pet_flap_pet_flap_battery_level": f"{HOUSEHOLD_ID}-13576-battery",
    "sensor.cat_flap_cat_flap_battery_level": f"{HOUSEHOLD_ID}-13579-battery",
    "sensor.feeder_feeder_battery_level": f"{HOUSEHOLD_ID}-12345-battery",
}


async def test_binary_sensors(opp, surepetcare) -> None:
    """Test the generation of unique ids."""
    assert await async_setup_component(opp, DOMAIN, MOCK_CONFIG)
    await opp.async_block_till_done()

    entity_registry = er.async_get(opp)
    state_entity_ids = opp.states.async_entity_ids()

    for entity_id, unique_id in EXPECTED_ENTITY_IDS.items():
        assert entity_id in state_entity_ids
        state = opp.states.get(entity_id)
        assert state
        assert state.state == "100"
        entity = entity_registry.async_get(entity_id)
        assert entity.unique_id == unique_id
