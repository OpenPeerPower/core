"""Common methods used across tests for Ecobee."""
from unittest.mock import patch

from openpeerpower.components.ecobee.const import CONF_REFRESH_TOKEN, DOMAIN
from openpeerpower.const import CONF_API_KEY
from openpeerpower.setup import async_setup_component

from tests.common import MockConfigEntry


async def setup_platform(opp, platform):
    """Set up the ecobee platform."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_API_KEY: "ABC123",
            CONF_REFRESH_TOKEN: "EFG456",
        },
    )
    mock_entry.add_to_opp(opp)

    with patch("openpeerpower.components.ecobee.const.PLATFORMS", [platform]):
        assert await async_setup_component(opp, DOMAIN, {})

    await opp.async_block_till_done()

    return mock_entry
