"""Tests for the AVM Fritz!Box integration."""
from unittest.mock import Mock, call

from openpeerpower.components.fritzbox.const import DOMAIN as FB_DOMAIN
from openpeerpower.components.switch import DOMAIN as SWITCH_DOMAIN
from openpeerpower.config_entries import ENTRY_STATE_LOADED, ENTRY_STATE_NOT_LOADED
from openpeerpower.const import (
    CONF_DEVICES,
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    STATE_UNAVAILABLE,
)
from openpeerpower.helpers.typing import OpenPeerPowerType
from openpeerpower.setup import async_setup_component

from . import MOCK_CONFIG, FritzDeviceSwitchMock

from tests.common import MockConfigEntry


async def test_setup.opp: OpenPeerPowerType, fritz: Mock):
    """Test setup of integration."""
    assert await async_setup_component.opp, FB_DOMAIN, MOCK_CONFIG)
    await.opp.async_block_till_done()
    entries =.opp.config_entries.async_entries()
    assert entries
    assert entries[0].data[CONF_HOST] == "fake_host"
    assert entries[0].data[CONF_PASSWORD] == "fake_pass"
    assert entries[0].data[CONF_USERNAME] == "fake_user"
    assert fritz.call_count == 1
    assert fritz.call_args_list == [
        call(host="fake_host", password="fake_pass", user="fake_user")
    ]


async def test_setup_duplicate_config.opp: OpenPeerPowerType, fritz: Mock, caplog):
    """Test duplicate config of integration."""
    DUPLICATE = {
        FB_DOMAIN: {
            CONF_DEVICES: [
                MOCK_CONFIG[FB_DOMAIN][CONF_DEVICES][0],
                MOCK_CONFIG[FB_DOMAIN][CONF_DEVICES][0],
            ]
        }
    }
    assert not await async_setup_component.opp, FB_DOMAIN, DUPLICATE)
    await.opp.async_block_till_done()
    assert not.opp.states.async_entity_ids()
    assert not.opp.states.async_all()
    assert "duplicate host entries found" in caplog.text


async def test_unload_remove.opp: OpenPeerPowerType, fritz: Mock):
    """Test unload and remove of integration."""
    fritz().get_devices.return_value = [FritzDeviceSwitchMock()]
    entity_id = f"{SWITCH_DOMAIN}.fake_name"

    entry = MockConfigEntry(
        domain=FB_DOMAIN,
        data=MOCK_CONFIG[FB_DOMAIN][CONF_DEVICES][0],
        unique_id=entity_id,
    )
    entry.add_to.opp.opp)

    config_entries =.opp.config_entries.async_entries(FB_DOMAIN)
    assert len(config_entries) == 1
    assert entry is config_entries[0]

    assert await async_setup_component.opp, FB_DOMAIN, {}) is True
    await.opp.async_block_till_done()

    assert entry.state == ENTRY_STATE_LOADED
    state =.opp.states.get(entity_id)
    assert state

    await.opp.config_entries.async_unload(entry.entry_id)

    assert fritz().logout.call_count == 1
    assert entry.state == ENTRY_STATE_NOT_LOADED
    state =.opp.states.get(entity_id)
    assert state.state == STATE_UNAVAILABLE

    await.opp.config_entries.async_remove(entry.entry_id)
    await.opp.async_block_till_done()

    assert fritz().logout.call_count == 1
    assert entry.state == ENTRY_STATE_NOT_LOADED
    state =.opp.states.get(entity_id)
    assert state is None
