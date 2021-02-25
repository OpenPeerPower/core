"""The tests for the Sure Petcare binary sensor platform."""
from surepy import MESTART_RESOURCE

from openpeerpower.components.surepetcare.const import DOMAIN
from openpeerpower.setup import async_setup_component

from . import MOCK_API_DATA, MOCK_CONFIG, _patch_sensor_setup

EXPECTED_ENTITY_IDS = {
    "binary_sensor.pet_flap_pet_flap_connectivity": "household-id-13576-connectivity",
    "binary_sensor.pet_flap_cat_flap_connectivity": "household-id-13579-connectivity",
    "binary_sensor.feeder_feeder_connectivity": "household-id-12345-connectivity",
    "binary_sensor.pet_pet": "household-id-24680",
    "binary_sensor.hub_hub": "household-id-hub-id",
}


async def test_binary_sensors(opp, surepetcare) -> None:
    """Test the generation of unique ids."""
    instance = surepetcare.return_value
    instance._resource[MESTART_RESOURCE] = {"data": MOCK_API_DATA}

    with _patch_sensor_setup():
        assert await async_setup_component(opp, DOMAIN, MOCK_CONFIG)
        await opp.async_block_till_done()

    entity_registry = await opp.helpers.entity_registry.async_get_registry()
    state_entity_ids = opp.states.async_entity_ids()

    for entity_id, unique_id in EXPECTED_ENTITY_IDS.items():
        assert entity_id in state_entity_ids
        entity = entity_registry.async_get(entity_id)
        assert entity.unique_id == unique_id
