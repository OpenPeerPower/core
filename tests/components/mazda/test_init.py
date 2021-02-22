"""Tests for the Mazda Connected Services integration."""
from unittest.mock import patch

from pymazda import MazdaAuthenticationException, MazdaException

from openpeerpower.components.mazda.const import DATA_COORDINATOR, DOMAIN
from openpeerpower.config_entries import (
    ENTRY_STATE_LOADED,
    ENTRY_STATE_SETUP_ERROR,
    ENTRY_STATE_SETUP_RETRY,
)
from openpeerpower.const import CONF_EMAIL, CONF_PASSWORD, CONF_REGION
from openpeerpower.core import OpenPeerPower

from tests.common import MockConfigEntry
from tests.components.mazda import init_integration

FIXTURE_USER_INPUT = {
    CONF_EMAIL: "example@example.com",
    CONF_PASSWORD: "password",
    CONF_REGION: "MNAO",
}


async def test_config_entry_not_ready.opp: OpenPeerPower) -> None:
    """Test the Mazda configuration entry not ready."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=FIXTURE_USER_INPUT)
    config_entry.add_to.opp.opp)

    with patch(
        "openpeerpower.components.mazda.MazdaAPI.validate_credentials",
        side_effect=MazdaException("Unknown error"),
    ):
        await.opp.config_entries.async_setup(config_entry.entry_id)
        await.opp.async_block_till_done()

    assert config_entry.state == ENTRY_STATE_SETUP_RETRY


async def test_init_auth_failure.opp: OpenPeerPower):
    """Test auth failure during setup."""
    with patch(
        "openpeerpower.components.mazda.MazdaAPI.validate_credentials",
        side_effect=MazdaAuthenticationException("Login failed"),
    ):
        config_entry = MockConfigEntry(domain=DOMAIN, data=FIXTURE_USER_INPUT)
        config_entry.add_to.opp.opp)

        await.opp.config_entries.async_setup(config_entry.entry_id)
        await.opp.async_block_till_done()

    entries = opp.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].state == ENTRY_STATE_SETUP_ERROR

    flows = opp.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["step_id"] == "reauth"


async def test_update_auth_failure.opp: OpenPeerPower):
    """Test auth failure during data update."""
    with patch(
        "openpeerpower.components.mazda.MazdaAPI.validate_credentials",
        return_value=True,
    ), patch("openpeerpower.components.mazda.MazdaAPI.get_vehicles", return_value={}):
        config_entry = MockConfigEntry(domain=DOMAIN, data=FIXTURE_USER_INPUT)
        config_entry.add_to.opp.opp)

        await.opp.config_entries.async_setup(config_entry.entry_id)
        await.opp.async_block_till_done()

    entries = opp.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].state == ENTRY_STATE_LOADED

    coordinator = opp.data[DOMAIN][config_entry.entry_id][DATA_COORDINATOR]
    with patch(
        "openpeerpower.components.mazda.MazdaAPI.validate_credentials",
        side_effect=MazdaAuthenticationException("Login failed"),
    ), patch(
        "openpeerpower.components.mazda.MazdaAPI.get_vehicles",
        side_effect=MazdaAuthenticationException("Login failed"),
    ):
        await coordinator.async_refresh()
        await.opp.async_block_till_done()

    flows = opp.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["step_id"] == "reauth"


async def test_unload_config_entry.opp: OpenPeerPower) -> None:
    """Test the Mazda configuration entry unloading."""
    entry = await init_integration.opp)
    assert.opp.data[DOMAIN]

    await.opp.config_entries.async_unload(entry.entry_id)
    await.opp.async_block_till_done()
    assert not.opp.data.get(DOMAIN)
