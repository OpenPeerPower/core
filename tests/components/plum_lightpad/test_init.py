"""Tests for the Plum Lightpad config flow."""
from unittest.mock import Mock, patch

from aiohttp import ContentTypeError
from requests.exceptions import HTTPError

from openpeerpower.components.plum_lightpad.const import DOMAIN
from openpeerpower.core import OpenPeerPower
from openpeerpower.setup import async_setup_component

from tests.common import MockConfigEntry


async def test_async_setup_no_domain_config(opp: OpenPeerPower):
    """Test setup without configuration is noop."""
    result = await async_setup_component(opp, DOMAIN, {})

    assert result is True
    assert DOMAIN not in opp.data


async def test_async_setup_imports_from_config(opp: OpenPeerPower):
    """Test that specifying config will setup an entry."""
    with patch(
        "openpeerpower.components.plum_lightpad.utils.Plum.loadCloudData"
    ) as mock_loadCloudData, patch(
        "openpeerpower.components.plum_lightpad.async_setup_entry",
        return_value=True,
    ) as mock_async_setup_entry:
        result = await async_setup_component(
            opp,
            DOMAIN,
            {
                DOMAIN: {
                    "username": "test-plum-username",
                    "password": "test-plum-password",
                }
            },
        )
        await opp.async_block_till_done()

    assert result is True
    assert len(mock_loadCloudData.mock_calls) == 1
    assert len(mock_async_setup_entry.mock_calls) == 1


async def test_async_setup_entry_sets_up_light(opp: OpenPeerPower):
    """Test that configuring entry sets up light domain."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"username": "test-plum-username", "password": "test-plum-password"},
    )
    config_entry.add_to_opp(opp)

    with patch(
        "openpeerpower.components.plum_lightpad.utils.Plum.loadCloudData"
    ) as mock_loadCloudData, patch(
        "openpeerpower.components.plum_lightpad.light.async_setup_entry"
    ) as mock_light_async_setup_entry:
        result = await opp.config_entries.async_setup(config_entry.entry_id)
        assert result is True

        await opp.async_block_till_done()

    assert len(mock_loadCloudData.mock_calls) == 1
    assert len(mock_light_async_setup_entry.mock_calls) == 1


async def test_async_setup_entry_handles_auth_error(opp: OpenPeerPower):
    """Test that configuring entry handles Plum Cloud authentication error."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"username": "test-plum-username", "password": "test-plum-password"},
    )
    config_entry.add_to_opp(opp)

    with patch(
        "openpeerpower.components.plum_lightpad.utils.Plum.loadCloudData",
        side_effect=ContentTypeError(Mock(), None),
    ), patch(
        "openpeerpower.components.plum_lightpad.light.async_setup_entry"
    ) as mock_light_async_setup_entry:
        result = await opp.config_entries.async_setup(config_entry.entry_id)

    assert result is False
    assert len(mock_light_async_setup_entry.mock_calls) == 0


async def test_async_setup_entry_handles_http_error(opp: OpenPeerPower):
    """Test that configuring entry handles HTTP error."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"username": "test-plum-username", "password": "test-plum-password"},
    )
    config_entry.add_to_opp(opp)

    with patch(
        "openpeerpower.components.plum_lightpad.utils.Plum.loadCloudData",
        side_effect=HTTPError,
    ), patch(
        "openpeerpower.components.plum_lightpad.light.async_setup_entry"
    ) as mock_light_async_setup_entry:
        result = await opp.config_entries.async_setup(config_entry.entry_id)

    assert result is False
    assert len(mock_light_async_setup_entry.mock_calls) == 0
