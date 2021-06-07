"""The tests for the litejet component."""
from unittest.mock import patch

from serial import SerialException

from openpeerpower import config_entries
from openpeerpower.components.litejet.const import DOMAIN
from openpeerpower.const import CONF_PORT

from tests.common import MockConfigEntry


async def test_show_config_form(opp):
    """Test show configuration form."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"


async def test_create_entry(opp, mock_litejet):
    """Test create entry from user input."""
    test_data = {CONF_PORT: "/dev/test"}

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=test_data
    )

    assert result["type"] == "create_entry"
    assert result["title"] == "/dev/test"
    assert result["data"] == test_data


async def test_flow_entry_already_exists(opp):
    """Test user input when a config entry already exists."""
    first_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_PORT: "/dev/first"},
    )
    first_entry.add_to_opp(opp)

    test_data = {CONF_PORT: "/dev/test"}

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=test_data
    )

    assert result["type"] == "abort"
    assert result["reason"] == "single_instance_allowed"


async def test_flow_open_failed(opp):
    """Test user input when serial port open fails."""
    test_data = {CONF_PORT: "/dev/test"}

    with patch("pylitejet.LiteJet") as mock_pylitejet:
        mock_pylitejet.side_effect = SerialException

        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=test_data
        )

    assert result["type"] == "form"
    assert result["errors"][CONF_PORT] == "open_failed"


async def test_import_step(opp):
    """Test initializing via import step."""
    test_data = {CONF_PORT: "/dev/imported"}
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data=test_data
    )

    assert result["type"] == "create_entry"
    assert result["title"] == test_data[CONF_PORT]
    assert result["data"] == test_data
