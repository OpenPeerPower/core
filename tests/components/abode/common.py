"""Common methods used across tests for Abode."""
from unittest.mock import patch

from openpeerpower.components.abode import DOMAIN as ABODE_DOMAIN
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME
from openpeerpower.setup import async_setup_component

from tests.common import MockConfigEntry


async def setup_platform.opp, platform):
    """Set up the Abode platform."""
    mock_entry = MockConfigEntry(
        domain=ABODE_DOMAIN,
        data={CONF_USERNAME: "user@email.com", CONF_PASSWORD: "password"},
    )
    mock_entry.add_to.opp.opp)

    with patch("openpeerpower.components.abode.ABODE_PLATFORMS", [platform]), patch(
        "abodepy.event_controller.sio"
    ), patch("abodepy.utils.save_cache"):
        assert await async_setup_component.opp, ABODE_DOMAIN, {})
    await opp.async_block_till_done()

    return mock_entry
