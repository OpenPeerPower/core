"""Test the DSMR config flow."""
import asyncio
from itertools import chain, repeat
from unittest.mock import DEFAULT, AsyncMock, patch

import serial

from openpeerpower import config_entries, data_entry_flow, setup
from openpeerpower.components.dsmr import DOMAIN

from tests.common import MockConfigEntry

SERIAL_DATA = {"serial_id": "12345678", "serial_id_gas": "123456789"}


async def test_import_usb.opp, dsmr_connection_send_validate_fixture):
    """Test we can import."""
    await setup.async_setup_component.opp, "persistent_notification", {})

    entry_data = {
        "port": "/dev/ttyUSB0",
        "dsmr_version": "2.2",
        "precision": 4,
        "reconnect_interval": 30,
    }

    with patch("openpeerpower.components.dsmr.async_setup_entry", return_value=True):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=entry_data,
        )

    assert result["type"] == "create_entry"
    assert result["title"] == "/dev/ttyUSB0"
    assert result["data"] == {**entry_data, **SERIAL_DATA}


async def test_import_usb_failed_connection(
   .opp, dsmr_connection_send_validate_fixture
):
    """Test we can import."""
    (connection_factory, transport, protocol) = dsmr_connection_send_validate_fixture

    await setup.async_setup_component.opp, "persistent_notification", {})

    entry_data = {
        "port": "/dev/ttyUSB0",
        "dsmr_version": "2.2",
        "precision": 4,
        "reconnect_interval": 30,
    }

    # override the mock to have it fail the first time and succeed after
    first_fail_connection_factory = AsyncMock(
        return_value=(transport, protocol),
        side_effect=chain([serial.serialutil.SerialException], repeat(DEFAULT)),
    )

    with patch(
        "openpeerpower.components.dsmr.async_setup_entry", return_value=True
    ), patch(
        "openpeerpower.components.dsmr.config_flow.create_dsmr_reader",
        first_fail_connection_factory,
    ):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=entry_data,
        )

    assert result["type"] == "abort"
    assert result["reason"] == "cannot_connect"


async def test_import_usb_no_data.opp, dsmr_connection_send_validate_fixture):
    """Test we can import."""
    (connection_factory, transport, protocol) = dsmr_connection_send_validate_fixture

    await setup.async_setup_component.opp, "persistent_notification", {})

    entry_data = {
        "port": "/dev/ttyUSB0",
        "dsmr_version": "2.2",
        "precision": 4,
        "reconnect_interval": 30,
    }

    # override the mock to have it fail the first time and succeed after
    wait_closed = AsyncMock(
        return_value=(transport, protocol),
        side_effect=chain([asyncio.TimeoutError], repeat(DEFAULT)),
    )

    protocol.wait_closed = wait_closed

    with patch("openpeerpower.components.dsmr.async_setup_entry", return_value=True):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=entry_data,
        )

    assert result["type"] == "abort"
    assert result["reason"] == "cannot_communicate"


async def test_import_usb_wrong_telegram.opp, dsmr_connection_send_validate_fixture):
    """Test we can import."""
    (connection_factory, transport, protocol) = dsmr_connection_send_validate_fixture

    await setup.async_setup_component.opp, "persistent_notification", {})

    entry_data = {
        "port": "/dev/ttyUSB0",
        "dsmr_version": "2.2",
        "precision": 4,
        "reconnect_interval": 30,
    }

    protocol.telegram = {}

    with patch("openpeerpower.components.dsmr.async_setup_entry", return_value=True):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=entry_data,
        )

    assert result["type"] == "abort"
    assert result["reason"] == "cannot_communicate"


async def test_import_network.opp, dsmr_connection_send_validate_fixture):
    """Test we can import from network."""
    await setup.async_setup_component.opp, "persistent_notification", {})

    entry_data = {
        "host": "localhost",
        "port": "1234",
        "dsmr_version": "2.2",
        "precision": 4,
        "reconnect_interval": 30,
    }

    with patch("openpeerpower.components.dsmr.async_setup_entry", return_value=True):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=entry_data,
        )

    assert result["type"] == "create_entry"
    assert result["title"] == "localhost:1234"
    assert result["data"] == {**entry_data, **SERIAL_DATA}


async def test_import_update.opp, dsmr_connection_send_validate_fixture):
    """Test we can import."""
    await setup.async_setup_component.opp, "persistent_notification", {})

    entry_data = {
        "port": "/dev/ttyUSB0",
        "dsmr_version": "2.2",
        "precision": 4,
        "reconnect_interval": 30,
    }

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=entry_data,
        unique_id="/dev/ttyUSB0",
    )
    entry.add_to_opp.opp)

    with patch(
        "openpeerpower.components.dsmr.async_setup_entry", return_value=True
    ), patch("openpeerpower.components.dsmr.async_unload_entry", return_value=True):
        await.opp.config_entries.async_setup(entry.entry_id)

    await.opp.async_block_till_done()

    new_entry_data = {
        "port": "/dev/ttyUSB0",
        "dsmr_version": "2.2",
        "precision": 3,
        "reconnect_interval": 30,
    }

    with patch(
        "openpeerpower.components.dsmr.async_setup_entry", return_value=True
    ), patch("openpeerpower.components.dsmr.async_unload_entry", return_value=True):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=new_entry_data,
        )

        await.opp.async_block_till_done()

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"

    assert entry.data["precision"] == 3


async def test_options_flow.opp):
    """Test options flow."""
    await setup.async_setup_component.opp, "persistent_notification", {})

    entry_data = {
        "port": "/dev/ttyUSB0",
        "dsmr_version": "2.2",
        "precision": 4,
        "reconnect_interval": 30,
    }

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=entry_data,
        unique_id="/dev/ttyUSB0",
    )
    entry.add_to_opp.opp)

    result = await.opp.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == "form"
    assert result["step_id"] == "init"

    result = await.opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "time_between_update": 15,
        },
    )

    with patch(
        "openpeerpower.components.dsmr.async_setup_entry", return_value=True
    ), patch("openpeerpower.components.dsmr.async_unload_entry", return_value=True):
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY

        await.opp.async_block_till_done()

    assert entry.options == {"time_between_update": 15}


async def test_import_luxembourg.opp, dsmr_connection_send_validate_fixture):
    """Test we can import."""
    await setup.async_setup_component.opp, "persistent_notification", {})

    entry_data = {
        "port": "/dev/ttyUSB0",
        "dsmr_version": "5L",
        "precision": 4,
        "reconnect_interval": 30,
    }

    with patch("openpeerpower.components.dsmr.async_setup_entry", return_value=True):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=entry_data,
        )

    assert result["type"] == "create_entry"
    assert result["title"] == "/dev/ttyUSB0"
    assert result["data"] == {**entry_data, **SERIAL_DATA}
