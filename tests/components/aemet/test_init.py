"""Define tests for the AEMET OpenData init."""

from unittest.mock import patch

import requests_mock

from openpeerpower.components.aemet.const import DOMAIN
from openpeerpower.config_entries import ConfigEntryState
from openpeerpower.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
import openpeerpower.util.dt as dt_util

from .util import aemet_requests_mock

from tests.common import MockConfigEntry

CONFIG = {
    CONF_NAME: "aemet",
    CONF_API_KEY: "foo",
    CONF_LATITUDE: 40.30403754,
    CONF_LONGITUDE: -3.72935236,
}


async def test_unload_entry(opp):
    """Test that the options form."""

    now = dt_util.parse_datetime("2021-01-09 12:00:00+00:00")
    with patch("openpeerpower.util.dt.now", return_value=now), patch(
        "openpeerpower.util.dt.utcnow", return_value=now
    ), requests_mock.mock() as _m:
        aemet_requests_mock(_m)

        config_entry = MockConfigEntry(
            domain=DOMAIN, unique_id="aemet_unique_id", data=CONFIG
        )
        config_entry.add_to_opp(opp)

        assert await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()
        assert config_entry.state is ConfigEntryState.LOADED

        await opp.config_entries.async_unload(config_entry.entry_id)
        await opp.async_block_till_done()
        assert config_entry.state is ConfigEntryState.NOT_LOADED
