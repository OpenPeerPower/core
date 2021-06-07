"""Test the Panasonic Viera setup process."""
from unittest.mock import patch

from openpeerpower.components.panasonic_viera.const import (
    ATTR_DEVICE_INFO,
    ATTR_UDN,
    DEFAULT_NAME,
    DOMAIN,
)
from openpeerpower.config_entries import ConfigEntryState
from openpeerpower.const import CONF_HOST, STATE_UNAVAILABLE
from openpeerpower.setup import async_setup_component

from .conftest import (
    MOCK_CONFIG_DATA,
    MOCK_DEVICE_INFO,
    MOCK_ENCRYPTION_DATA,
    get_mock_remote,
)

from tests.common import MockConfigEntry


async def test_setup_entry_encrypted(opp, mock_remote):
    """Test setup with encrypted config entry."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=MOCK_DEVICE_INFO[ATTR_UDN],
        data={**MOCK_CONFIG_DATA, **MOCK_ENCRYPTION_DATA, **MOCK_DEVICE_INFO},
    )

    mock_entry.add_to_opp(opp)

    await opp.config_entries.async_setup(mock_entry.entry_id)
    await opp.async_block_till_done()

    state_tv = opp.states.get("media_player.panasonic_viera_tv")
    state_remote = opp.states.get("remote.panasonic_viera_tv")

    assert state_tv
    assert state_tv.name == DEFAULT_NAME

    assert state_remote
    assert state_remote.name == DEFAULT_NAME


async def test_setup_entry_encrypted_missing_device_info(opp, mock_remote):
    """Test setup with encrypted config entry and missing device info."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=MOCK_CONFIG_DATA[CONF_HOST],
        data={**MOCK_CONFIG_DATA, **MOCK_ENCRYPTION_DATA},
    )

    mock_entry.add_to_opp(opp)

    await opp.config_entries.async_setup(mock_entry.entry_id)
    await opp.async_block_till_done()

    assert mock_entry.data[ATTR_DEVICE_INFO] == MOCK_DEVICE_INFO
    assert mock_entry.unique_id == MOCK_DEVICE_INFO[ATTR_UDN]

    state_tv = opp.states.get("media_player.panasonic_viera_tv")
    state_remote = opp.states.get("remote.panasonic_viera_tv")

    assert state_tv
    assert state_tv.name == DEFAULT_NAME

    assert state_remote
    assert state_remote.name == DEFAULT_NAME


async def test_setup_entry_encrypted_missing_device_info_none(opp):
    """Test setup with encrypted config entry and device info set to None."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=MOCK_CONFIG_DATA[CONF_HOST],
        data={**MOCK_CONFIG_DATA, **MOCK_ENCRYPTION_DATA},
    )

    mock_entry.add_to_opp(opp)

    mock_remote = get_mock_remote(device_info=None)

    with patch(
        "openpeerpower.components.panasonic_viera.RemoteControl",
        return_value=mock_remote,
    ):
        await opp.config_entries.async_setup(mock_entry.entry_id)
        await opp.async_block_till_done()

        assert mock_entry.data[ATTR_DEVICE_INFO] is None
        assert mock_entry.unique_id == MOCK_CONFIG_DATA[CONF_HOST]

        state_tv = opp.states.get("media_player.panasonic_viera_tv")
        state_remote = opp.states.get("remote.panasonic_viera_tv")

        assert state_tv
        assert state_tv.name == DEFAULT_NAME

        assert state_remote
        assert state_remote.name == DEFAULT_NAME


async def test_setup_entry_unencrypted(opp, mock_remote):
    """Test setup with unencrypted config entry."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=MOCK_DEVICE_INFO[ATTR_UDN],
        data={**MOCK_CONFIG_DATA, **MOCK_DEVICE_INFO},
    )

    mock_entry.add_to_opp(opp)

    await opp.config_entries.async_setup(mock_entry.entry_id)
    await opp.async_block_till_done()

    state_tv = opp.states.get("media_player.panasonic_viera_tv")
    state_remote = opp.states.get("remote.panasonic_viera_tv")

    assert state_tv
    assert state_tv.name == DEFAULT_NAME

    assert state_remote
    assert state_remote.name == DEFAULT_NAME


async def test_setup_entry_unencrypted_missing_device_info(opp, mock_remote):
    """Test setup with unencrypted config entry and missing device info."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=MOCK_CONFIG_DATA[CONF_HOST],
        data=MOCK_CONFIG_DATA,
    )

    mock_entry.add_to_opp(opp)

    await opp.config_entries.async_setup(mock_entry.entry_id)
    await opp.async_block_till_done()

    assert mock_entry.data[ATTR_DEVICE_INFO] == MOCK_DEVICE_INFO
    assert mock_entry.unique_id == MOCK_DEVICE_INFO[ATTR_UDN]

    state_tv = opp.states.get("media_player.panasonic_viera_tv")
    state_remote = opp.states.get("remote.panasonic_viera_tv")

    assert state_tv
    assert state_tv.name == DEFAULT_NAME

    assert state_remote
    assert state_remote.name == DEFAULT_NAME


async def test_setup_entry_unencrypted_missing_device_info_none(opp):
    """Test setup with unencrypted config entry and device info set to None."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=MOCK_CONFIG_DATA[CONF_HOST],
        data=MOCK_CONFIG_DATA,
    )

    mock_entry.add_to_opp(opp)

    mock_remote = get_mock_remote(device_info=None)

    with patch(
        "openpeerpower.components.panasonic_viera.RemoteControl",
        return_value=mock_remote,
    ):
        await opp.config_entries.async_setup(mock_entry.entry_id)
        await opp.async_block_till_done()

        assert mock_entry.data[ATTR_DEVICE_INFO] is None
        assert mock_entry.unique_id == MOCK_CONFIG_DATA[CONF_HOST]

        state_tv = opp.states.get("media_player.panasonic_viera_tv")
        state_remote = opp.states.get("remote.panasonic_viera_tv")

        assert state_tv
        assert state_tv.name == DEFAULT_NAME

        assert state_remote
        assert state_remote.name == DEFAULT_NAME


async def test_setup_config_flow_initiated(opp):
    """Test if config flow is initiated in setup."""
    assert (
        await async_setup_component(
            opp,
            DOMAIN,
            {DOMAIN: {CONF_HOST: "0.0.0.0"}},
        )
        is True
    )

    assert len(opp.config_entries.flow.async_progress()) == 1


async def test_setup_unload_entry(opp, mock_remote):
    """Test if config entry is unloaded."""
    mock_entry = MockConfigEntry(
        domain=DOMAIN, unique_id=MOCK_DEVICE_INFO[ATTR_UDN], data=MOCK_CONFIG_DATA
    )

    mock_entry.add_to_opp(opp)

    await opp.config_entries.async_setup(mock_entry.entry_id)
    await opp.async_block_till_done()

    await opp.config_entries.async_unload(mock_entry.entry_id)
    assert mock_entry.state is ConfigEntryState.NOT_LOADED

    state_tv = opp.states.get("media_player.panasonic_viera_tv")
    state_remote = opp.states.get("remote.panasonic_viera_tv")

    assert state_tv.state == STATE_UNAVAILABLE
    assert state_remote.state == STATE_UNAVAILABLE

    await opp.config_entries.async_remove(mock_entry.entry_id)
    await opp.async_block_till_done()

    state_tv = opp.states.get("media_player.panasonic_viera_tv")
    state_remote = opp.states.get("remote.panasonic_viera_tv")

    assert state_tv is None
    assert state_remote is None
