"""The config flow tests for the forked_daapd media player platform."""
from unittest.mock import AsyncMock, patch

import pytest

from openpeerpower import data_entry_flow
from openpeerpower.components.forked_daapd.const import (
    CONF_LIBRESPOT_JAVA_PORT,
    CONF_MAX_PLAYLISTS,
    CONF_TTS_PAUSE_TIME,
    CONF_TTS_VOLUME,
    DOMAIN,
)
from openpeerpower.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from openpeerpower.const import CONF_HOST, CONF_PASSWORD, CONF_PORT

from tests.common import MockConfigEntry

SAMPLE_CONFIG = {
    "websocket_port": 3688,
    "version": "25.0",
    "buildoptions": [
        "ffmpeg",
        "iTunes XML",
        "Spotify",
        "LastFM",
        "MPD",
        "Device verification",
        "Websockets",
        "ALSA",
    ],
}


@pytest.fixture(name="config_entry")
def config_entry_fixture():
    """Create opp.config_entry fixture."""
    data = {
        CONF_HOST: "192.168.1.1",
        CONF_PORT: "2345",
        CONF_PASSWORD: "",
    }
    return MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="",
        data=data,
        options={},
        source=SOURCE_USER,
        entry_id=1,
    )


async def test_show_form(opp):
    """Test that the form is served with no input."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == SOURCE_USER


async def test_config_flow(opp, config_entry):
    """Test that the user step works."""
    with patch(
        "openpeerpower.components.forked_daapd.config_flow.ForkedDaapdAPI.test_connection",
        new=AsyncMock(),
    ) as mock_test_connection, patch(
        "openpeerpower.components.forked_daapd.media_player.ForkedDaapdAPI.get_request",
        autospec=True,
    ) as mock_get_request:
        mock_get_request.return_value = SAMPLE_CONFIG
        mock_test_connection.return_value = ["ok", "My Music on myhost"]
        config_data = config_entry.data
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=config_data
        )
        await opp.async_block_till_done()
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == "My Music on myhost"
        assert result["data"][CONF_HOST] == config_data[CONF_HOST]
        assert result["data"][CONF_PORT] == config_data[CONF_PORT]
        assert result["data"][CONF_PASSWORD] == config_data[CONF_PASSWORD]

        # Also test that creating a new entry with the same host aborts
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=config_entry.data,
        )
        await opp.async_block_till_done()
        assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT


async def test_zeroconf_updates_title(opp, config_entry):
    """Test that zeroconf updates title and aborts with same host."""
    MockConfigEntry(domain=DOMAIN, data={CONF_HOST: "different host"}).add_to_opp(opp)
    config_entry.add_to_opp(opp)
    assert len(opp.config_entries.async_entries(DOMAIN)) == 2
    discovery_info = {
        "host": "192.168.1.1",
        "port": 23,
        "properties": {"mtd-version": "27.0", "Machine Name": "zeroconf_test"},
    }
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )
    await opp.async_block_till_done()
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert config_entry.title == "zeroconf_test"
    assert len(opp.config_entries.async_entries(DOMAIN)) == 2


async def test_config_flow_no_websocket(opp, config_entry):
    """Test config flow setup without websocket enabled on server."""
    with patch(
        "openpeerpower.components.forked_daapd.config_flow.ForkedDaapdAPI.test_connection",
        new=AsyncMock(),
    ) as mock_test_connection:
        # test invalid config data
        mock_test_connection.return_value = ["websocket_not_enabled"]
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=config_entry.data
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM


async def test_config_flow_zeroconf_invalid(opp):
    """Test that an invalid zeroconf entry doesn't work."""
    # test with no discovery properties
    discovery_info = {"host": "127.0.0.1", "port": 23}
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )  # doesn't create the entry, tries to show form but gets abort
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "not_forked_daapd"
    # test with forked-daapd version < 27
    discovery_info = {
        "host": "127.0.0.1",
        "port": 23,
        "properties": {"mtd-version": "26.3", "Machine Name": "forked-daapd"},
    }
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )  # doesn't create the entry, tries to show form but gets abort
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "not_forked_daapd"
    # test with verbose mtd-version from Firefly
    discovery_info = {
        "host": "127.0.0.1",
        "port": 23,
        "properties": {"mtd-version": "0.2.4.1", "Machine Name": "firefly"},
    }
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )  # doesn't create the entry, tries to show form but gets abort
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "not_forked_daapd"
    # test with svn mtd-version from Firefly
    discovery_info = {
        "host": "127.0.0.1",
        "port": 23,
        "properties": {"mtd-version": "svn-1676", "Machine Name": "firefly"},
    }
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )  # doesn't create the entry, tries to show form but gets abort
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "not_forked_daapd"


async def test_config_flow_zeroconf_valid(opp):
    """Test that a valid zeroconf entry works."""
    discovery_info = {
        "host": "192.168.1.1",
        "port": 23,
        "properties": {
            "mtd-version": "27.0",
            "Machine Name": "zeroconf_test",
            "Machine ID": "5E55EEFF",
        },
    }
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=discovery_info
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM


async def test_options_flow(opp, config_entry):
    """Test config flow options."""

    with patch(
        "openpeerpower.components.forked_daapd.media_player.ForkedDaapdAPI.get_request",
        autospec=True,
    ) as mock_get_request:
        mock_get_request.return_value = SAMPLE_CONFIG
        config_entry.add_to_opp(opp)
        await config_entry.async_setup(opp)
        await opp.async_block_till_done()

        result = await opp.config_entries.options.async_init(config_entry.entry_id)
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM

        result = await opp.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_TTS_PAUSE_TIME: 0.05,
                CONF_TTS_VOLUME: 0.8,
                CONF_LIBRESPOT_JAVA_PORT: 0,
                CONF_MAX_PLAYLISTS: 8,
            },
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
