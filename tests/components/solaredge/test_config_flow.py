"""Tests for the SolarEdge config flow."""
from unittest.mock import Mock, patch

import pytest
from requests.exceptions import ConnectTimeout, HTTPError

from openpeerpower import data_entry_flow
from openpeerpower.components.solaredge.const import CONF_SITE_ID, DEFAULT_NAME, DOMAIN
from openpeerpower.config_entries import SOURCE_USER
from openpeerpower.const import CONF_API_KEY, CONF_NAME
from openpeerpower.core import OpenPeerPower

from tests.common import MockConfigEntry

NAME = "solaredge site 1 2 3"
SITE_ID = "1a2b3c4d5e6f7g8h"
API_KEY = "a1b2c3d4e5f6g7h8"


@pytest.fixture(name="test_api")
def mock_controller():
    """Mock a successful Solaredge API."""
    api = Mock()
    api.get_details.return_value = {"details": {"status": "active"}}
    with patch("solaredge.Solaredge", return_value=api):
        yield api


async def test_user(opp: OpenPeerPower, test_api: Mock) -> None:
    """Test user config."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result.get("type") == data_entry_flow.RESULT_TYPE_FORM
    assert result.get("step_id") == "user"

    # test with all provided
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_NAME: NAME, CONF_API_KEY: API_KEY, CONF_SITE_ID: SITE_ID},
    )
    assert result.get("type") == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result.get("title") == "solaredge_site_1_2_3"

    data = result.get("data")
    assert data
    assert data[CONF_SITE_ID] == SITE_ID
    assert data[CONF_API_KEY] == API_KEY


async def test_abort_if_already_setup(opp: OpenPeerPower, test_api: str) -> None:
    """Test we abort if the site_id is already setup."""
    MockConfigEntry(
        domain="solaredge",
        data={CONF_NAME: DEFAULT_NAME, CONF_SITE_ID: SITE_ID, CONF_API_KEY: API_KEY},
    ).add_to_opp(opp)

    # user: Should fail, same SITE_ID
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_NAME: "test", CONF_SITE_ID: SITE_ID, CONF_API_KEY: "test"},
    )
    assert result.get("type") == data_entry_flow.RESULT_TYPE_FORM
    assert result.get("errors") == {CONF_SITE_ID: "already_configured"}


async def test_asserts(opp: OpenPeerPower, test_api: Mock) -> None:
    """Test the _site_in_configuration_exists method."""

    # test with inactive site
    test_api.get_details.return_value = {"details": {"status": "NOK"}}

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_NAME: NAME, CONF_API_KEY: API_KEY, CONF_SITE_ID: SITE_ID},
    )
    assert result.get("type") == data_entry_flow.RESULT_TYPE_FORM
    assert result.get("errors") == {CONF_SITE_ID: "site_not_active"}

    # test with api_failure
    test_api.get_details.return_value = {}
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_NAME: NAME, CONF_API_KEY: API_KEY, CONF_SITE_ID: SITE_ID},
    )
    assert result.get("type") == data_entry_flow.RESULT_TYPE_FORM
    assert result.get("errors") == {CONF_SITE_ID: "invalid_api_key"}

    # test with ConnectionTimeout
    test_api.get_details.side_effect = ConnectTimeout()
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_NAME: NAME, CONF_API_KEY: API_KEY, CONF_SITE_ID: SITE_ID},
    )
    assert result.get("type") == data_entry_flow.RESULT_TYPE_FORM
    assert result.get("errors") == {CONF_SITE_ID: "could_not_connect"}

    # test with HTTPError
    test_api.get_details.side_effect = HTTPError()
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_NAME: NAME, CONF_API_KEY: API_KEY, CONF_SITE_ID: SITE_ID},
    )
    assert result.get("type") == data_entry_flow.RESULT_TYPE_FORM
    assert result.get("errors") == {CONF_SITE_ID: "could_not_connect"}
