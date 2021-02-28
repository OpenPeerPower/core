"""Test the AlarmDecoder config flow."""
from unittest.mock import patch

from alarmdecoder.util import NoDeviceError
import pytest

from openpeerpower import config_entries, data_entry_flow
from openpeerpower.components.alarmdecoder import config_flow
from openpeerpower.components.alarmdecoder.const import (
    CONF_ALT_NIGHT_MODE,
    CONF_AUTO_BYPASS,
    CONF_CODE_ARM_REQUIRED,
    CONF_DEVICE_BAUD,
    CONF_DEVICE_PATH,
    CONF_RELAY_ADDR,
    CONF_RELAY_CHAN,
    CONF_ZONE_LOOP,
    CONF_ZONE_NAME,
    CONF_ZONE_NUMBER,
    CONF_ZONE_RFID,
    CONF_ZONE_TYPE,
    DEFAULT_ARM_OPTIONS,
    DEFAULT_ZONE_OPTIONS,
    DOMAIN,
    OPTIONS_ARM,
    OPTIONS_ZONES,
    PROTOCOL_SERIAL,
    PROTOCOL_SOCKET,
)
from openpeerpower.components.binary_sensor import DEVICE_CLASS_WINDOW
from openpeerpower.const import CONF_HOST, CONF_PORT, CONF_PROTOCOL
from openpeerpower.core import OpenPeerPower

from tests.common import MockConfigEntry


@pytest.mark.parametrize(
    "protocol,connection,title",
    [
        (
            PROTOCOL_SOCKET,
            {
                CONF_HOST: "alarmdecoder123",
                CONF_PORT: 10001,
            },
            "alarmdecoder123:10001",
        ),
        (
            PROTOCOL_SERIAL,
            {
                CONF_DEVICE_PATH: "/dev/ttyUSB123",
                CONF_DEVICE_BAUD: 115000,
            },
            "/dev/ttyUSB123",
        ),
    ],
)
async def test_setups(opp: OpenPeerPower, protocol, connection, title):
    """Test flow for setting up the available AlarmDecoder protocols."""

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PROTOCOL: protocol},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "protocol"

    with patch("openpeerpower.components.alarmdecoder.config_flow.AdExt.open"), patch(
        "openpeerpower.components.alarmdecoder.config_flow.AdExt.close"
    ), patch(
        "openpeerpower.components.alarmdecoder.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.alarmdecoder.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], connection
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == title
        assert result["data"] == {
            **connection,
            CONF_PROTOCOL: protocol,
        }
        await opp.async_block_till_done()

    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_setup_connection_error(opp: OpenPeerPower):
    """Test flow for setup with a connection error."""

    port = 1001
    host = "alarmdecoder"
    protocol = PROTOCOL_SOCKET
    connection_settings = {CONF_HOST: host, CONF_PORT: port}

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PROTOCOL: protocol},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "protocol"

    with patch(
        "openpeerpower.components.alarmdecoder.config_flow.AdExt.open",
        side_effect=NoDeviceError,
    ), patch("openpeerpower.components.alarmdecoder.config_flow.AdExt.close"):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], connection_settings
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["errors"] == {"base": "cannot_connect"}


async def test_options_arm_flow(opp: OpenPeerPower):
    """Test arm options flow."""
    user_input = {
        CONF_ALT_NIGHT_MODE: True,
        CONF_AUTO_BYPASS: True,
        CONF_CODE_ARM_REQUIRED: True,
    }
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_opp(opp)

    await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    result = await opp.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"edit_selection": "Arming Settings"},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "arm_settings"

    with patch(
        "openpeerpower.components.alarmdecoder.async_setup_entry", return_value=True
    ):
        result = await opp.config_entries.options.async_configure(
            result["flow_id"],
            user_input=user_input,
        )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert entry.options == {
        OPTIONS_ARM: user_input,
        OPTIONS_ZONES: DEFAULT_ZONE_OPTIONS,
    }


async def test_options_zone_flow(opp: OpenPeerPower):
    """Test options flow for adding/deleting zones."""
    zone_number = "2"
    zone_settings = {CONF_ZONE_NAME: "Front Entry", CONF_ZONE_TYPE: DEVICE_CLASS_WINDOW}
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_opp(opp)

    await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    result = await opp.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"edit_selection": "Zones"},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "zone_select"

    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_ZONE_NUMBER: zone_number},
    )

    with patch(
        "openpeerpower.components.alarmdecoder.async_setup_entry", return_value=True
    ):
        result = await opp.config_entries.options.async_configure(
            result["flow_id"],
            user_input=zone_settings,
        )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert entry.options == {
        OPTIONS_ARM: DEFAULT_ARM_OPTIONS,
        OPTIONS_ZONES: {zone_number: zone_settings},
    }

    # Make sure zone can be removed...
    result = await opp.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"edit_selection": "Zones"},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "zone_select"

    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_ZONE_NUMBER: zone_number},
    )

    with patch(
        "openpeerpower.components.alarmdecoder.async_setup_entry", return_value=True
    ):
        result = await opp.config_entries.options.async_configure(
            result["flow_id"],
            user_input={},
        )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert entry.options == {
        OPTIONS_ARM: DEFAULT_ARM_OPTIONS,
        OPTIONS_ZONES: {},
    }


async def test_options_zone_flow_validation(opp: OpenPeerPower):
    """Test input validation for zone options flow."""
    zone_number = "2"
    zone_settings = {CONF_ZONE_NAME: "Front Entry", CONF_ZONE_TYPE: DEVICE_CLASS_WINDOW}
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_opp(opp)

    await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    result = await opp.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"edit_selection": "Zones"},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "zone_select"

    # Zone Number must be int
    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_ZONE_NUMBER: "asd"},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "zone_select"
    assert result["errors"] == {CONF_ZONE_NUMBER: "int"}

    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_ZONE_NUMBER: zone_number},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "zone_details"

    # CONF_RELAY_ADDR & CONF_RELAY_CHAN are inclusive
    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={**zone_settings, CONF_RELAY_ADDR: "1"},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "zone_details"
    assert result["errors"] == {"base": "relay_inclusive"}

    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={**zone_settings, CONF_RELAY_CHAN: "1"},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "zone_details"
    assert result["errors"] == {"base": "relay_inclusive"}

    # CONF_RELAY_ADDR, CONF_RELAY_CHAN must be int
    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={**zone_settings, CONF_RELAY_ADDR: "abc", CONF_RELAY_CHAN: "abc"},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "zone_details"
    assert result["errors"] == {
        CONF_RELAY_ADDR: "int",
        CONF_RELAY_CHAN: "int",
    }

    # CONF_ZONE_LOOP depends on CONF_ZONE_RFID
    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={**zone_settings, CONF_ZONE_LOOP: "1"},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "zone_details"
    assert result["errors"] == {CONF_ZONE_LOOP: "loop_rfid"}

    # CONF_ZONE_LOOP must be int
    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={**zone_settings, CONF_ZONE_RFID: "rfid123", CONF_ZONE_LOOP: "ab"},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "zone_details"
    assert result["errors"] == {CONF_ZONE_LOOP: "int"}

    # CONF_ZONE_LOOP must be between [1,4]
    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={**zone_settings, CONF_ZONE_RFID: "rfid123", CONF_ZONE_LOOP: "5"},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "zone_details"
    assert result["errors"] == {CONF_ZONE_LOOP: "loop_range"}

    # All valid settings
    with patch(
        "openpeerpower.components.alarmdecoder.async_setup_entry", return_value=True
    ):
        result = await opp.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                **zone_settings,
                CONF_ZONE_RFID: "rfid123",
                CONF_ZONE_LOOP: "2",
                CONF_RELAY_ADDR: "12",
                CONF_RELAY_CHAN: "1",
            },
        )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert entry.options == {
        OPTIONS_ARM: DEFAULT_ARM_OPTIONS,
        OPTIONS_ZONES: {
            zone_number: {
                **zone_settings,
                CONF_ZONE_RFID: "rfid123",
                CONF_ZONE_LOOP: 2,
                CONF_RELAY_ADDR: 12,
                CONF_RELAY_CHAN: 1,
            }
        },
    }


@pytest.mark.parametrize(
    "protocol,connection",
    [
        (
            PROTOCOL_SOCKET,
            {
                CONF_HOST: "alarmdecoder123",
                CONF_PORT: 10001,
            },
        ),
        (
            PROTOCOL_SERIAL,
            {
                CONF_DEVICE_PATH: "/dev/ttyUSB123",
                CONF_DEVICE_BAUD: 115000,
            },
        ),
    ],
)
async def test_one_device_allowed(opp, protocol, connection):
    """Test that only one AlarmDecoder device is allowed."""
    flow = config_flow.AlarmDecoderFlowHandler()
    flow.opp = opp

    MockConfigEntry(
        domain=DOMAIN,
        data=connection,
    ).add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PROTOCOL: protocol},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "protocol"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], connection
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"
