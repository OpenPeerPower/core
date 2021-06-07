"""Tests for Met.no."""
from unittest.mock import patch

from openpeerpower.components.met.const import CONF_TRACK_HOME, DOMAIN
from openpeerpower.const import CONF_ELEVATION, CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME

from tests.common import MockConfigEntry


async def init_integration(opp, track_home=False) -> MockConfigEntry:
    """Set up the Met integration in Open Peer Power."""
    entry_data = {
        CONF_NAME: "test",
        CONF_LATITUDE: 0,
        CONF_LONGITUDE: 1.0,
        CONF_ELEVATION: 1.0,
    }

    if track_home:
        entry_data = {CONF_TRACK_HOME: True}

    entry = MockConfigEntry(domain=DOMAIN, data=entry_data)
    with patch(
        "openpeerpower.components.met.metno.MetWeatherData.fetching_data",
        return_value=True,
    ):
        entry.add_to_opp(opp)
        await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()

    return entry
