"""Test the Panasonic Viera remote entity."""

from unittest.mock import call

from panasonic_viera import Keys

from openpeerpower.components.panasonic_viera.const import ATTR_UDN, DOMAIN
from openpeerpower.components.remote import (
    ATTR_COMMAND,
    DOMAIN as REMOTE_DOMAIN,
    SERVICE_SEND_COMMAND,
)
from openpeerpower.const import ATTR_ENTITY_ID, SERVICE_TURN_OFF, SERVICE_TURN_ON

from .conftest import MOCK_CONFIG_DATA, MOCK_DEVICE_INFO, MOCK_ENCRYPTION_DATA

from tests.common import MockConfigEntry


async def setup_panasonic_viera(opp):
    """Initialize integration for tests."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=MOCK_DEVICE_INFO[ATTR_UDN],
        data={**MOCK_CONFIG_DATA, **MOCK_ENCRYPTION_DATA, **MOCK_DEVICE_INFO},
    )

    mock_entry.add_to_opp(opp)

    await opp.config_entries.async_setup(mock_entry.entry_id)
    await opp.async_block_till_done()


async def test_onoff(opp, mock_remote):
    """Test the on/off service calls."""

    await setup_panasonic_viera(opp)

    data = {ATTR_ENTITY_ID: "remote.panasonic_viera_tv"}

    await opp.services.async_call(REMOTE_DOMAIN, SERVICE_TURN_OFF, data)
    await opp.services.async_call(REMOTE_DOMAIN, SERVICE_TURN_ON, data)
    await opp.async_block_till_done()

    power = getattr(Keys.power, "value", Keys.power)
    assert mock_remote.send_key.call_args_list == [call(power), call(power)]


async def test_send_command(opp, mock_remote):
    """Test the send_command service call."""

    await setup_panasonic_viera(opp)

    data = {ATTR_ENTITY_ID: "remote.panasonic_viera_tv", ATTR_COMMAND: "command"}
    await opp.services.async_call(REMOTE_DOMAIN, SERVICE_SEND_COMMAND, data)
    await opp.async_block_till_done()

    assert mock_remote.send_key.call_args == call("command")
