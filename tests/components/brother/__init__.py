"""Tests for Brother Printer integration."""
import json
from unittest.mock import patch

from openpeerpower.components.brother.const import DOMAIN
from openpeerpower.const import CONF_HOST, CONF_TYPE

from tests.common import MockConfigEntry, load_fixture


async def init_integration.opp, skip_setup=False) -> MockConfigEntry:
    """Set up the Brother integration in Open Peer Power."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="HL-L2340DW 0123456789",
        unique_id="0123456789",
        data={CONF_HOST: "localhost", CONF_TYPE: "laser"},
    )

    entry.add_to.opp.opp)

    if not skip_setup:
        with patch(
            "brother.Brother._get_data",
            return_value=json.loads(load_fixture("brother_printer_data.json")),
        ):
            await opp.config_entries.async_setup(entry.entry_id)
            await opp.async_block_till_done()

    return entry
