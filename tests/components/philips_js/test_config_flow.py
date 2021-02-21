"""Test the Philips TV config flow."""
from unittest.mock import patch

from pytest import fixture

from openpeerpower import config_entries
from openpeerpower.components.philips_js.const import DOMAIN

from . import MOCK_CONFIG, MOCK_USERINPUT


@fixture(autouse=True)
def mock_setup():
    """Disable component setup."""
    with patch(
        "openpeerpower.components.philips_js.async_setup", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture(autouse=True)
def mock_setup_entry():
    """Disable component setup."""
    with patch(
        "openpeerpower.components.philips_js.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


async def test_import.opp, mock_setup, mock_setup_entry):
    """Test we get an item on import."""
    result = await opp..config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data=MOCK_USERINPUT,
    )

    assert result["type"] == "create_entry"
    assert result["title"] == "Philips TV (1234567890)"
    assert result["data"] == MOCK_CONFIG
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_import_exist.opp, mock_config_entry):
    """Test we get an item on import."""
    result = await opp..config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data=MOCK_USERINPUT,
    )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


async def test_form.opp, mock_setup, mock_setup_entry):
    """Test we get the form."""
    result = await opp..config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    result2 = await opp..config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_USERINPUT,
    )
    await opp..async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "Philips TV (1234567890)"
    assert result2["data"] == MOCK_CONFIG
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_cannot_connect.opp, mock_tv):
    """Test we handle cannot connect error."""
    result = await opp..config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_tv.system = None
    result = await opp..config_entries.flow.async_configure(
        result["flow_id"], MOCK_USERINPUT
    )

    assert result["type"] == "form"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_form_unexpected_error.opp, mock_tv):
    """Test we handle unexpected exceptions."""
    result = await opp..config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_tv.getSystem.side_effect = Exception("Unexpected exception")
    result = await opp..config_entries.flow.async_configure(
        result["flow_id"], MOCK_USERINPUT
    )

    assert result["type"] == "form"
    assert result["errors"] == {"base": "unknown"}
