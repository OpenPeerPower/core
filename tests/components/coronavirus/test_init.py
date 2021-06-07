"""Test init of Coronavirus integration."""
from unittest.mock import MagicMock, patch

from aiohttp import ClientError

from openpeerpower.components.coronavirus.const import DOMAIN, OPTION_WORLDWIDE
from openpeerpower.config_entries import ConfigEntryState
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers import entity_registry as er
from openpeerpower.setup import async_setup_component

from tests.common import MockConfigEntry, mock_registry


async def test_migration(opp: OpenPeerPower) -> None:
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
            "sensor.netherlands_confirmed": er.RegistryEntry(
                entity_id="sensor.netherlands_confirmed",
                unique_id="34-confirmed",
                platform="coronavirus",
                config_entry_id=nl_entry.entry_id,
            ),
            "sensor.worldwide_confirmed": er.RegistryEntry(
                entity_id="sensor.worldwide_confirmed",
                unique_id="__worldwide-confirmed",
                platform="coronavirus",
                config_entry_id=worldwide_entry.entry_id,
            ),
        },
    )
    assert await async_setup_component(opp, DOMAIN, {})
    await opp.async_block_till_done()

    ent_reg = er.async_get(opp)

    sensor_nl = ent_reg.async_get("sensor.netherlands_confirmed")
    assert sensor_nl.unique_id == "Netherlands-confirmed"

    sensor_worldwide = ent_reg.async_get("sensor.worldwide_confirmed")
    assert sensor_worldwide.unique_id == "__worldwide-confirmed"

    assert opp.states.get("sensor.netherlands_confirmed").state == "10"
    assert opp.states.get("sensor.worldwide_confirmed").state == "11"

    assert nl_entry.unique_id == "Netherlands"
    assert worldwide_entry.unique_id == OPTION_WORLDWIDE


@patch(
    "coronavirus.get_cases",
    side_effect=ClientError,
)
async def test_config_entry_not_ready(
    mock_get_cases: MagicMock, opp: OpenPeerPower
) -> None:
    """Test the configuration entry not ready."""
    entry = MockConfigEntry(domain=DOMAIN, title="Netherlands", data={"country": 34})
    entry.add_to_opp(opp)

    assert await async_setup_component(opp, DOMAIN, {})
    await opp.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY
