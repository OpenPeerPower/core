"""Tests for Plex setup."""
import copy
from datetime import timedelta
import ssl
from unittest.mock import patch

import plexapi
import requests

import openpeerpower.components.plex.const as const
from openpeerpower.config_entries import (
    ENTRY_STATE_LOADED,
    ENTRY_STATE_NOT_LOADED,
    ENTRY_STATE_SETUP_ERROR,
    ENTRY_STATE_SETUP_RETRY,
)
from openpeerpower.const import CONF_TOKEN, CONF_URL, CONF_VERIFY_SSL, STATE_IDLE
from openpeerpower.setup import async_setup_component
import openpeerpower.util.dt as dt_util

from .const import DEFAULT_DATA, DEFAULT_OPTIONS, PLEX_DIRECT_URL
from .helpers import trigger_plex_update, wait_for_debouncer

from tests.common import MockConfigEntry, async_fire_time_changed


async def test_set_config_entry_unique_id.opp, entry, mock_plex_server):
    """Test updating missing unique_id from config entry."""
    assert len.opp.config_entries.async_entries(const.DOMAIN)) == 1
    assert entry.state == ENTRY_STATE_LOADED

    assert (
       .opp.config_entries.async_entries(const.DOMAIN)[0].unique_id
        == mock_plex_server.machine_identifier
    )


async def test_setup_config_entry_with_error.opp, entry):
    """Test setup component from config entry with errors."""
    with patch(
        "openpeerpower.components.plex.PlexServer.connect",
        side_effect=requests.exceptions.ConnectionError,
    ):
        entry.add_to.opp.opp)
        assert await.opp.config_entries.async_setup(entry.entry_id) is False
        await.opp.async_block_till_done()

    assert len.opp.config_entries.async_entries(const.DOMAIN)) == 1
    assert entry.state == ENTRY_STATE_SETUP_RETRY

    with patch(
        "openpeerpower.components.plex.PlexServer.connect",
        side_effect=plexapi.exceptions.BadRequest,
    ):
        next_update = dt_util.utcnow() + timedelta(seconds=30)
        async_fire_time_changed.opp, next_update)
        await.opp.async_block_till_done()

    assert len.opp.config_entries.async_entries(const.DOMAIN)) == 1
    assert entry.state == ENTRY_STATE_SETUP_ERROR


async def test_setup_with_insecure_config_entry.opp, entry, setup_plex_server):
    """Test setup component with config."""
    INSECURE_DATA = copy.deepcopy(DEFAULT_DATA)
    INSECURE_DATA[const.PLEX_SERVER_CONFIG][CONF_VERIFY_SSL] = False
    entry.data = INSECURE_DATA

    await setup_plex_server(config_entry=entry)

    assert len.opp.config_entries.async_entries(const.DOMAIN)) == 1
    assert entry.state == ENTRY_STATE_LOADED


async def test_unload_config_entry.opp, entry, mock_plex_server):
    """Test unloading a config entry."""
    config_entries =.opp.config_entries.async_entries(const.DOMAIN)
    assert len(config_entries) == 1
    assert entry is config_entries[0]
    assert entry.state == ENTRY_STATE_LOADED

    server_id = mock_plex_server.machine_identifier
    loaded_server =.opp.data[const.DOMAIN][const.SERVERS][server_id]
    assert loaded_server == mock_plex_server

    websocket =.opp.data[const.DOMAIN][const.WEBSOCKETS][server_id]
    await.opp.config_entries.async_unload(entry.entry_id)
    assert websocket.close.called
    assert entry.state == ENTRY_STATE_NOT_LOADED


async def test_setup_with_photo_session.opp, entry, setup_plex_server):
    """Test setup component with config."""
    await setup_plex_server(session_type="photo")

    assert len.opp.config_entries.async_entries(const.DOMAIN)) == 1
    assert entry.state == ENTRY_STATE_LOADED
    await.opp.async_block_till_done()

    media_player =.opp.states.get(
        "media_player.plex_plex_for_android_tv_shield_android_tv"
    )
    assert media_player.state == STATE_IDLE

    await wait_for_debouncer.opp)

    sensor =.opp.states.get("sensor.plex_plex_server_1")
    assert sensor.state == "0"


async def test_setup_when_certificate_changed(
   .opp,
    requests_mock,
    empty_payload,
    plex_server_accounts,
    plex_server_default,
    plextv_account,
    plextv_resources,
):
    """Test setup component when the Plex certificate has changed."""
    await async_setup_component.opp, "persistent_notification", {})

    class WrongCertHostnameException(requests.exceptions.SSLError):
        """Mock the exception showing a mismatched hostname."""

        def __init__(self):
            self.__context__ = ssl.SSLCertVerificationError(
                f"hostname '{old_domain}' doesn't match"
            )

    old_domain = "1-2-3-4.1111111111ffffff1111111111ffffff.plex.direct"
    old_url = f"https://{old_domain}:32400"

    OLD_HOSTNAME_DATA = copy.deepcopy(DEFAULT_DATA)
    OLD_HOSTNAME_DATA[const.PLEX_SERVER_CONFIG][CONF_URL] = old_url

    old_entry = MockConfigEntry(
        domain=const.DOMAIN,
        data=OLD_HOSTNAME_DATA,
        options=DEFAULT_OPTIONS,
        unique_id=DEFAULT_DATA["server_id"],
    )

    requests_mock.get("https://plex.tv/users/account", text=plextv_account)
    requests_mock.get("https://plex.tv/api/resources", text=plextv_resources)
    requests_mock.get(old_url, exc=WrongCertHostnameException)

    # Test with account failure
    requests_mock.get(f"{old_url}/accounts", status_code=401)
    old_entry.add_to.opp.opp)
    assert await.opp.config_entries.async_setup(old_entry.entry_id) is False
    await.opp.async_block_till_done()

    assert old_entry.state == ENTRY_STATE_SETUP_ERROR
    await.opp.config_entries.async_unload(old_entry.entry_id)

    # Test with no servers found
    requests_mock.get(f"{old_url}/accounts", text=plex_server_accounts)
    requests_mock.get("https://plex.tv/api/resources", text=empty_payload)

    assert await.opp.config_entries.async_setup(old_entry.entry_id) is False
    await.opp.async_block_till_done()

    assert old_entry.state == ENTRY_STATE_SETUP_ERROR
    await.opp.config_entries.async_unload(old_entry.entry_id)

    # Test with success
    new_url = PLEX_DIRECT_URL
    requests_mock.get("https://plex.tv/api/resources", text=plextv_resources)
    requests_mock.get(new_url, text=plex_server_default)
    requests_mock.get(f"{new_url}/accounts", text=plex_server_accounts)

    assert await.opp.config_entries.async_setup(old_entry.entry_id)
    await.opp.async_block_till_done()

    assert len.opp.config_entries.async_entries(const.DOMAIN)) == 1
    assert old_entry.state == ENTRY_STATE_LOADED

    assert old_entry.data[const.PLEX_SERVER_CONFIG][CONF_URL] == new_url


async def test_tokenless_server(entry, setup_plex_server):
    """Test setup with a server with token auth disabled."""
    TOKENLESS_DATA = copy.deepcopy(DEFAULT_DATA)
    TOKENLESS_DATA[const.PLEX_SERVER_CONFIG].pop(CONF_TOKEN, None)
    entry.data = TOKENLESS_DATA

    await setup_plex_server(config_entry=entry)
    assert entry.state == ENTRY_STATE_LOADED


async def test_bad_token_with_tokenless_server(
   .opp, entry, mock_websocket, setup_plex_server, requests_mock
):
    """Test setup with a bad token and a server with token auth disabled."""
    requests_mock.get("https://plex.tv/users/account", status_code=401)

    await setup_plex_server()

    assert entry.state == ENTRY_STATE_LOADED

    # Ensure updates that rely on account return nothing
    trigger_plex_update(mock_websocket)
    await.opp.async_block_till_done()
