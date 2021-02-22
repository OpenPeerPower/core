"""Tests for the Sonsrr integration."""
from unittest.mock import patch

from openpeerpower.components.sonarr.const import DOMAIN
from openpeerpower.config_entries import (
    ENTRY_STATE_LOADED,
    ENTRY_STATE_NOT_LOADED,
    ENTRY_STATE_SETUP_ERROR,
    ENTRY_STATE_SETUP_RETRY,
    SOURCE_REAUTH,
)
from openpeerpower.const import CONF_SOURCE
from openpeerpower.core import OpenPeerPower

from tests.components.sonarr import setup_integration
from tests.test_util.aiohttp import AiohttpClientMocker


async def test_config_entry_not_ready(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the configuration entry not ready."""
    entry = await setup_integration.opp, aioclient_mock, connection_error=True)
    assert entry.state == ENTRY_STATE_SETUP_RETRY


async def test_config_entry_reauth(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the configuration entry needing to be re-authenticated."""
    with patch.object.opp.config_entries.flow, "async_init") as mock_flow_init:
        entry = await setup_integration.opp, aioclient_mock, invalid_auth=True)

    assert entry.state == ENTRY_STATE_SETUP_ERROR

    mock_flow_init.assert_called_once_with(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_REAUTH},
        data={"config_entry_id": entry.entry_id, **entry.data},
    )


async def test_unload_config_entry(
    opp: OpenPeerPower, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the configuration entry unloading."""
    with patch(
        "openpeerpower.components.sonarr.sensor.async_setup_entry",
        return_value=True,
    ):
        entry = await setup_integration.opp, aioclient_mock)

    assert.opp.data[DOMAIN]
    assert entry.entry_id in.opp.data[DOMAIN]
    assert entry.state == ENTRY_STATE_LOADED

    await.opp.config_entries.async_unload(entry.entry_id)
    await.opp.async_block_till_done()

    assert entry.entry_id not in.opp.data[DOMAIN]
    assert entry.state == ENTRY_STATE_NOT_LOADED
