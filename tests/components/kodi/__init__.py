"""Tests for the Kodi integration."""
from unittest.mock import patch

from openpeerpower.components.kodi.const import CONF_WS_PORT, DOMAIN
from openpeerpower.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
)

from .util import MockConnection

from tests.common import MockConfigEntry


async def init_integration.opp) -> MockConfigEntry:
    """Set up the Kodi integration in Open Peer Power."""
    entry_data = {
        CONF_NAME: "name",
        CONF_HOST: "1.1.1.1",
        CONF_PORT: 8080,
        CONF_WS_PORT: 9090,
        CONF_USERNAME: "user",
        CONF_PASSWORD: "pass",
        CONF_SSL: False,
    }
    entry = MockConfigEntry(domain=DOMAIN, data=entry_data, title="name")
    entry.add_to.opp.opp)

    with patch("openpeerpower.components.kodi.Kodi.ping", return_value=True), patch(
        "openpeerpower.components.kodi.Kodi.get_application_properties",
        return_value={"version": {"major": 1, "minor": 1}},
    ), patch(
        "openpeerpower.components.kodi.get_kodi_connection",
        return_value=MockConnection(),
    ):
        await.opp.config_entries.async_setup(entry.entry_id)
        await.opp.async_block_till_done()

    return entry
