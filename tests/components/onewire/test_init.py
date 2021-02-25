"""Tests for 1-Wire config flow."""
from unittest.mock import patch

from pyownet.protocol import ConnError, OwnetError

from openpeerpower.components.onewire.const import CONF_TYPE_OWSERVER, DOMAIN
from openpeerpower.config_entries import (
    CONN_CLASS_LOCAL_POLL,
    ENTRY_STATE_LOADED,
    ENTRY_STATE_NOT_LOADED,
    ENTRY_STATE_SETUP_RETRY,
)
from openpeerpower.const import CONF_HOST, CONF_PORT, CONF_TYPE

from . import setup_onewire_owserver_integration, setup_onewire_sysbus_integration

from tests.common import MockConfigEntry


async def test_owserver_connect_failure.opp):
    """Test connection failure raises ConfigEntryNotReady."""
    config_entry_owserver = MockConfigEntry(
        domain=DOMAIN,
        source="user",
        data={
            CONF_TYPE: CONF_TYPE_OWSERVER,
            CONF_HOST: "1.2.3.4",
            CONF_PORT: "1234",
        },
        unique_id=f"{CONF_TYPE_OWSERVER}:1.2.3.4:1234",
        connection_class=CONN_CLASS_LOCAL_POLL,
        options={},
        entry_id="2",
    )
    config_entry_owserver.add_to_opp(opp)

    with patch(
        "openpeerpower.components.onewire.onewirehub.protocol.proxy",
        side_effect=ConnError,
    ):
        await opp.config_entries.async_setup(config_entry_owserver.entry_id)
        await opp.async_block_till_done()

    assert len.opp.config_entries.async_entries(DOMAIN)) == 1
    assert config_entry_owserver.state == ENTRY_STATE_SETUP_RETRY
    assert not opp.data.get(DOMAIN)


async def test_failed_owserver_listing.opp):
    """Create the 1-Wire integration."""
    config_entry_owserver = MockConfigEntry(
        domain=DOMAIN,
        source="user",
        data={
            CONF_TYPE: CONF_TYPE_OWSERVER,
            CONF_HOST: "1.2.3.4",
            CONF_PORT: "1234",
        },
        unique_id=f"{CONF_TYPE_OWSERVER}:1.2.3.4:1234",
        connection_class=CONN_CLASS_LOCAL_POLL,
        options={},
        entry_id="2",
    )
    config_entry_owserver.add_to_opp(opp)

    with patch("openpeerpower.components.onewire.onewirehub.protocol.proxy") as owproxy:
        owproxy.return_value.dir.side_effect = OwnetError
        await opp.config_entries.async_setup(config_entry_owserver.entry_id)
        await opp.async_block_till_done()

        return config_entry_owserver


async def test_unload_entry.opp):
    """Test being able to unload an entry."""
    config_entry_owserver = await setup_onewire_owserver_integration.opp)
    config_entry_sysbus = await setup_onewire_sysbus_integration.opp)

    assert len.opp.config_entries.async_entries(DOMAIN)) == 2
    assert config_entry_owserver.state == ENTRY_STATE_LOADED
    assert config_entry_sysbus.state == ENTRY_STATE_LOADED

    assert await opp.config_entries.async_unload(config_entry_owserver.entry_id)
    assert await opp.config_entries.async_unload(config_entry_sysbus.entry_id)
    await opp.async_block_till_done()

    assert config_entry_owserver.state == ENTRY_STATE_NOT_LOADED
    assert config_entry_sysbus.state == ENTRY_STATE_NOT_LOADED
    assert not opp.data.get(DOMAIN)
