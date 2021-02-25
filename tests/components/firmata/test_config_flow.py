"""Test the Firmata config flow."""
from unittest.mock import patch

from pymata_express.pymata_express_serial import serial

from openpeerpower import config_entries, setup
from openpeerpower.components.firmata.const import CONF_SERIAL_PORT, DOMAIN
from openpeerpower.const import CONF_NAME
from openpeerpower.core import OpenPeerPower


async def test_import_cannot_connect_pymata.opp: OpenPeerPower) -> None:
    """Test we fail with an invalid board."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    with patch(
        "openpeerpower.components.firmata.board.PymataExpress.start_aio",
        side_effect=RuntimeError,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={CONF_SERIAL_PORT: "/dev/nonExistent"},
        )

        assert result["type"] == "abort"
        assert result["reason"] == "cannot_connect"


async def test_import_cannot_connect_serial.opp: OpenPeerPower) -> None:
    """Test we fail with an invalid board."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    with patch(
        "openpeerpower.components.firmata.board.PymataExpress.start_aio",
        side_effect=serial.serialutil.SerialException,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={CONF_SERIAL_PORT: "/dev/nonExistent"},
        )

        assert result["type"] == "abort"
        assert result["reason"] == "cannot_connect"


async def test_import_cannot_connect_serial_timeout.opp: OpenPeerPower) -> None:
    """Test we fail with an invalid board."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    with patch(
        "openpeerpower.components.firmata.board.PymataExpress.start_aio",
        side_effect=serial.serialutil.SerialTimeoutException,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={CONF_SERIAL_PORT: "/dev/nonExistent"},
        )

        assert result["type"] == "abort"
        assert result["reason"] == "cannot_connect"


async def test_import.opp: OpenPeerPower) -> None:
    """Test we create an entry from config."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    with patch(
        "openpeerpower.components.firmata.board.PymataExpress", autospec=True
    ), patch(
        "openpeerpower.components.firmata.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.firmata.async_setup_entry", return_value=True
    ) as mock_setup_entry:

        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={CONF_SERIAL_PORT: "/dev/nonExistent"},
        )

        assert result["type"] == "create_entry"
        assert result["title"] == "serial-/dev/nonExistent"
        assert result["data"] == {
            CONF_NAME: "serial-/dev/nonExistent",
            CONF_SERIAL_PORT: "/dev/nonExistent",
        }
        await opp.async_block_till_done()
        assert len(mock_setup.mock_calls) == 1
        assert len(mock_setup_entry.mock_calls) == 1
