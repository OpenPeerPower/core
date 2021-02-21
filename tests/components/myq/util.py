"""Tests for the myq integration."""
import json
import logging
from unittest.mock import patch

from pymyq.const import ACCOUNTS_ENDPOINT, DEVICES_ENDPOINT

from openpeerpower.components.myq.const import DOMAIN
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME
from openpeerpowerr.core import OpenPeerPower

from tests.common import MockConfigEntry, load_fixture

_LOGGER = logging.getLogger(__name__)


async def async_init_integration(
   .opp: OpenPeerPower,
    skip_setup: bool = False,
) -> MockConfigEntry:
    """Set up the myq integration in Open Peer Power."""

    devices_fixture = "myq/devices.json"
    devices_json = load_fixture(devices_fixture)
    devices_dict = json.loads(devices_json)

    def _op.dle_mock_api_oauth_authenticate():
        return 1234, 1800

    def _op.dle_mock_api_request(method, returns, url, **kwargs):
        _LOGGER.debug("URL: %s", url)
        if url == ACCOUNTS_ENDPOINT:
            _LOGGER.debug("Accounts")
            return None, {"accounts": [{"id": 1, "name": "mock"}]}
        if url == DEVICES_ENDPOINT.format(account_id=1):
            _LOGGER.debug("Devices")
            return None, devices_dict
        _LOGGER.debug("Something else")
        return None, {}

    with patch(
        "pymyq.api.API._oauth_authenticate",
        side_effect=_op.dle_mock_api_oauth_authenticate,
    ), patch("pymyq.api.API.request", side_effect=_op.dle_mock_api_request):
        entry = MockConfigEntry(
            domain=DOMAIN, data={CONF_USERNAME: "mock", CONF_PASSWORD: "mock"}
        )
        entry.add_to_opp.opp)

        if not skip_setup:
            await.opp.config_entries.async_setup(entry.entry_id)
            await opp.async_block_till_done()

    return entry
