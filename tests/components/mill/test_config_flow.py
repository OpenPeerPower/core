"""Tests for Mill config flow."""
from unittest.mock import patch

import pytest

from openpeerpower.components.mill.const import DOMAIN
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME

from tests.common import MockConfigEntry


@pytest.fixture(name="mill_setup", autouse=True)
def mill_setup_fixture():
    """Patch mill setup entry."""
    with patch("openpeerpower.components.mill.async_setup_entry", return_value=True):
        yield


async def test_show_config_form.opp):
    """Test show configuration form."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"


async def test_create_entry.opp):
    """Test create entry from user input."""
    test_data = {
        CONF_USERNAME: "user",
        CONF_PASSWORD: "pswd",
    }

    with patch("mill.Mill.connect", return_value=True):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}, data=test_data
        )

    assert result["type"] == "create_entry"
    assert result["title"] == test_data[CONF_USERNAME]
    assert result["data"] == test_data


async def test_flow_entry_already_exists(opp):
    """Test user input for config_entry that already exists."""

    test_data = {
        CONF_USERNAME: "user",
        CONF_PASSWORD: "pswd",
    }

    first_entry = MockConfigEntry(
        domain="mill",
        data=test_data,
        unique_id=test_data[CONF_USERNAME],
    )
    first_entry.add_to_opp(opp)

    with patch("mill.Mill.connect", return_value=True):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}, data=test_data
        )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


async def test_connection_error(opp):
    """Test connection error."""

    test_data = {
        CONF_USERNAME: "user",
        CONF_PASSWORD: "pswd",
    }

    first_entry = MockConfigEntry(
        domain="mill",
        data=test_data,
        unique_id=test_data[CONF_USERNAME],
    )
    first_entry.add_to_opp(opp)

    with patch("mill.Mill.connect", return_value=False):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}, data=test_data
        )

    assert result["type"] == "form"
    assert result["errors"]["cannot_connect"] == "cannot_connect"
