"""Define tests for the AEMET OpenData config flow."""

from unittest.mock import MagicMock, patch

import requests_mock

from openpeerpower import data_entry_flow
from openpeerpower.components.aemet.const import DOMAIN
from openpeerpower.config_entries import ENTRY_STATE_LOADED, SOURCE_USER
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


async def test_form.opp):
    """Test that the form is served with valid input."""

    with patch(
        "openpeerpower.components.aemet.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.aemet.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry, requests_mock.mock() as _m:
        aemet_requests_mock(_m)

        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == SOURCE_USER
        assert result["errors"] == {}

        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], CONFIG
        )

        await opp.async_block_till_done()

        conf_entries = opp.config_entries.async_entries(DOMAIN)
        entry = conf_entries[0]
        assert entry.state == ENTRY_STATE_LOADED

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == CONFIG[CONF_NAME]
        assert result["data"][CONF_LATITUDE] == CONFIG[CONF_LATITUDE]
        assert result["data"][CONF_LONGITUDE] == CONFIG[CONF_LONGITUDE]
        assert result["data"][CONF_API_KEY] == CONFIG[CONF_API_KEY]

        assert len(mock_setup.mock_calls) == 1
        assert len(mock_setup_entry.mock_calls) == 1


async def test_form_duplicated_id.opp):
    """Test that the options form."""

    now = dt_util.parse_datetime("2021-01-09 12:00:00+00:00")
    with patch("openpeerpower.util.dt.now", return_value=now), patch(
        "openpeerpower.util.dt.utcnow", return_value=now
    ), requests_mock.mock() as _m:
        aemet_requests_mock(_m)

        entry = MockConfigEntry(
            domain=DOMAIN, unique_id="40.30403754--3.72935236", data=CONFIG
        )
        entry.add_to_opp(opp)

        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
        )

        assert result["type"] == "abort"
        assert result["reason"] == "already_configured"


async def test_form_api_offline.opp):
    """Test setting up with api call error."""
    mocked_aemet = MagicMock()

    mocked_aemet.get_conventional_observation_stations.return_value = None

    with patch(
        "openpeerpower.components.aemet.config_flow.AEMET",
        return_value=mocked_aemet,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONFIG
        )

        assert result["errors"] == {"base": "invalid_api_key"}
