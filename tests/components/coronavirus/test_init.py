"""Test init of Coronavirus integration."""
from openpeerpower.components.coronavirus.const import DOMAIN, OPTION_WORLDWIDE
from openpeerpower.helpers import entity_registry
from openpeerpower.setup import async_setup_component

from tests.common import MockConfigEntry, mock_registry


async def test_migration(opp):
    """Test that we can migrate coronavirus to stable unique ID."""
    nl_entry = MockConfigEntry(domain=DOMAIN, title="Netherlands", data={"country": 34})
    nl_entry.add_to_opp(opp)
    worldwide_entry = MockConfigEntry(
        domain=DOMAIN, title="Worldwide", data={"country": OPTION_WORLDWIDE}
    )
    worldwide_entry.add_to_opp(opp)
    mock_registry(
        opp,
        {
            "sensor.netherlands_confirmed": entity_registry.RegistryEntry(
                entity_id="sensor.netherlands_confirmed",
                unique_id="34-confirmed",
                platform="coronavirus",
                config_entry_id=nl_entry.entry_id,
            ),
            "sensor.worldwide_confirmed": entity_registry.RegistryEntry(
                entity_id="sensor.worldwide_confirmed",
                unique_id="__worldwide-confirmed",
                platform="coronavirus",
                config_entry_id=worldwide_entry.entry_id,
            ),
        },
    )
    assert await async_setup_component(opp, DOMAIN, {})
    await opp.async_block_till_done()

    ent_reg = await entity_registry.async_get_registry(opp)

    sensor_nl = ent_reg.async_get("sensor.netherlands_confirmed")
    assert sensor_nl.unique_id == "Netherlands-confirmed"

    sensor_worldwide = ent_reg.async_get("sensor.worldwide_confirmed")
    assert sensor_worldwide.unique_id == "__worldwide-confirmed"

    assert opp.states.get("sensor.netherlands_confirmed").state == "10"
    assert opp.states.get("sensor.worldwide_confirmed").state == "11"

    assert nl_entry.unique_id == "Netherlands"
    assert worldwide_entry.unique_id == OPTION_WORLDWIDE
