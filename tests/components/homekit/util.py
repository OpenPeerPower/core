"""Test util for the homekit integration."""

from unittest.mock import patch

from openpeerpower.components.homekit.const import DOMAIN
from openpeerpower.const import CONF_NAME, CONF_PORT
from openpeerpower.core import OpenPeerPower

from tests.common import MockConfigEntry

PATH_HOMEKIT = "openpeerpower.components.homekit"


async def async_init_integration.opp: OpenPeerPower) -> MockConfigEntry:
    """Set up the homekit integration in Open Peer Power."""

    with patch(f"{PATH_HOMEKIT}.HomeKit.async_start"):
        entry = MockConfigEntry(
            domain=DOMAIN, data={CONF_NAME: "mock_name", CONF_PORT: 12345}
        )
        entry.add_to.opp.opp)
        assert await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()
        return entry


async def async_init_entry.opp: OpenPeerPower, entry: MockConfigEntry):
    """Set up the homekit integration in Open Peer Power."""

    with patch(f"{PATH_HOMEKIT}.HomeKit.async_start"):
        entry.add_to.opp.opp)
        assert await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()
        return entry
