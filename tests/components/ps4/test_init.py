"""Tests for the PS4 Integration."""
from unittest.mock import MagicMock, patch

from openpeerpower import config_entries, data_entry_flow
from openpeerpower.components import ps4
from openpeerpower.components.media_player.const import (
    ATTR_MEDIA_CONTENT_TYPE,
    ATTR_MEDIA_TITLE,
    MEDIA_TYPE_GAME,
)
from openpeerpower.components.ps4.const import (
    ATTR_MEDIA_IMAGE_URL,
    COMMANDS,
    CONFIG_ENTRY_VERSION as VERSION,
    DEFAULT_REGION,
    DOMAIN,
    PS4_DATA,
)
from openpeerpower.const import (
    ATTR_COMMAND,
    ATTR_ENTITY_ID,
    ATTR_LOCKED,
    CONF_HOST,
    CONF_NAME,
    CONF_REGION,
    CONF_TOKEN,
)
from openpeerpower.exceptions import OpenPeerPowerError
from openpeerpower.setup import async_setup_component
from openpeerpower.util import location

from tests.common import MockConfigEntry, mock_registry

MOCK_HOST = "192.168.0.1"
MOCK_NAME = "test_ps4"
MOCK_REGION = "Some Region"
MOCK_CREDS = "1234567890A"

MOCK_DEVICE = {CONF_HOST: MOCK_HOST, CONF_NAME: MOCK_NAME, CONF_REGION: MOCK_REGION}

MOCK_DATA = {CONF_TOKEN: MOCK_CREDS, "devices": [MOCK_DEVICE]}

MOCK_FLOW_RESULT = {
    "version": VERSION,
    "handler": DOMAIN,
    "type": data_entry_flow.RESULT_TYPE_CREATE_ENTRY,
    "title": "test_ps4",
    "data": MOCK_DATA,
}

MOCK_ENTRY_ID = "SomeID"

MOCK_CONFIG = MockConfigEntry(domain=DOMAIN, data=MOCK_DATA, entry_id=MOCK_ENTRY_ID)

MOCK_LOCATION = location.LocationInfo(
    "0.0.0.0",
    "US",
    "United States",
    "CA",
    "California",
    "San Diego",
    "92122",
    "America/Los_Angeles",
    32.8594,
    -117.2073,
    True,
)

MOCK_DEVICE_VERSION_1 = {
    CONF_HOST: MOCK_HOST,
    CONF_NAME: MOCK_NAME,
    CONF_REGION: "Some Region",
}

MOCK_DATA_VERSION_1 = {CONF_TOKEN: MOCK_CREDS, "devices": [MOCK_DEVICE_VERSION_1]}

MOCK_DEVICE_ID = "somedeviceid"

MOCK_ENTRY_VERSION_1 = MockConfigEntry(
    domain=DOMAIN, data=MOCK_DATA_VERSION_1, entry_id=MOCK_ENTRY_ID, version=1
)

MOCK_UNIQUE_ID = "someuniqueid"

MOCK_ID = "CUSA00123"
MOCK_URL = "http://someurl.jpeg"
MOCK_TITLE = "Some Title"
MOCK_TYPE = MEDIA_TYPE_GAME

MOCK_GAMES_DATA_OLD_STR_FORMAT = {"mock_id": "mock_title", "mock_id2": "mock_title2"}

MOCK_GAMES_DATA = {
    ATTR_LOCKED: False,
    ATTR_MEDIA_CONTENT_TYPE: MEDIA_TYPE_GAME,
    ATTR_MEDIA_IMAGE_URL: MOCK_URL,
    ATTR_MEDIA_TITLE: MOCK_TITLE,
}

MOCK_GAMES_DATA_LOCKED = {
    ATTR_LOCKED: True,
    ATTR_MEDIA_CONTENT_TYPE: MEDIA_TYPE_GAME,
    ATTR_MEDIA_IMAGE_URL: MOCK_URL,
    ATTR_MEDIA_TITLE: MOCK_TITLE,
}

MOCK_GAMES = {MOCK_ID: MOCK_GAMES_DATA}
MOCK_GAMES_LOCKED = {MOCK_ID: MOCK_GAMES_DATA_LOCKED}


async def test_ps4_integration_setup_opp):
    """Test PS4 integration is setup."""
    await ps4.async_setup_opp, {})
    await.opp.async_block_till_done()
    assert.opp.data[PS4_DATA].protocol is not None


async def test_creating_entry_sets_up_media_player.opp):
    """Test setting up PS4 loads the media player."""
    mock_flow = "openpeerpower.components.ps4.PlayStation4FlowHandler.async_step_user"
    with patch(
        "openpeerpower.components.ps4.media_player.async_setup_entry",
        return_value=True,
    ) as mock_setup, patch(mock_flow, return_value=MOCK_FLOW_RESULT):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY

        await.opp.async_block_till_done()

    assert len(mock_setup.mock_calls) == 1


async def test_config_flow_entry_migrate.opp):
    """Test that config flow entry is migrated correctly."""
    # Start with the config entry at Version 1.
    manager = opp.config_entries
    mock_entry = MOCK_ENTRY_VERSION_1
    mock_entry.add_to_manager(manager)
    mock_e_registry = mock_registry.opp)
    mock_entity_id = f"media_player.ps4_{MOCK_UNIQUE_ID}"
    mock_e_entry = mock_e_registry.async_get_or_create(
        "media_player",
        "ps4",
        MOCK_UNIQUE_ID,
        config_entry=mock_entry,
        device_id=MOCK_DEVICE_ID,
    )
    assert len(mock_e_registry.entities) == 1
    assert mock_e_entry.entity_id == mock_entity_id
    assert mock_e_entry.unique_id == MOCK_UNIQUE_ID

    with patch(
        "openpeerpower.util.location.async_detect_location_info",
        return_value=MOCK_LOCATION,
    ), patch(
        "openpeerpower.helpers.entity_registry.async_get_registry",
        return_value=mock_e_registry,
    ):
        await ps4.async_migrate_entry.opp, mock_entry)

    await.opp.async_block_till_done()

    assert len(mock_e_registry.entities) == 1
    for entity in mock_e_registry.entities.values():
        mock_entity = entity

    # Test that entity_id remains the same.
    assert mock_entity.entity_id == mock_entity_id
    assert mock_entity.device_id == MOCK_DEVICE_ID

    # Test that last four of credentials is appended to the unique_id.
    assert mock_entity.unique_id == "{}_{}".format(MOCK_UNIQUE_ID, MOCK_CREDS[-4:])

    # Test that config entry is at the current version.
    assert mock_entry.version == VERSION
    assert mock_entry.data[CONF_TOKEN] == MOCK_CREDS
    assert mock_entry.data["devices"][0][CONF_HOST] == MOCK_HOST
    assert mock_entry.data["devices"][0][CONF_NAME] == MOCK_NAME
    assert mock_entry.data["devices"][0][CONF_REGION] == DEFAULT_REGION


async def test_media_player_is_setup_opp):
    """Test media_player is setup correctly."""
    await setup_mock_component.opp)
    assert len.opp.data[PS4_DATA].devices) == 1


async def setup_mock_component.opp):
    """Set up Mock Media Player."""
    entry = MockConfigEntry(domain=ps4.DOMAIN, data=MOCK_DATA, version=VERSION)
    entry.add_to_manager.opp.config_entries)
    await async_setup_component.opp, DOMAIN, {DOMAIN: {}})
    await.opp.async_block_till_done()


def test_games_reformat_to_dict.opp):
    """Test old data format is converted to new format."""
    with patch(
        "openpeerpower.components.ps4.load_json",
        return_value=MOCK_GAMES_DATA_OLD_STR_FORMAT,
    ), patch("openpeerpower.components.ps4.save_json", side_effect=MagicMock()), patch(
        "os.path.isfile", return_value=True
    ):
        mock_games = ps4.load_games.opp, MOCK_ENTRY_ID)

    # New format is a nested dict.
    assert isinstance(mock_games, dict)
    assert mock_games["mock_id"][ATTR_MEDIA_TITLE] == "mock_title"
    assert mock_games["mock_id2"][ATTR_MEDIA_TITLE] == "mock_title2"
    for mock_game in mock_games:
        mock_data = mock_games[mock_game]
        assert isinstance(mock_data, dict)
        assert mock_data
        assert mock_data[ATTR_MEDIA_IMAGE_URL] is None
        assert mock_data[ATTR_LOCKED] is False
        assert mock_data[ATTR_MEDIA_CONTENT_TYPE] == MEDIA_TYPE_GAME


def test_load_games.opp):
    """Test that games are loaded correctly."""
    with patch(
        "openpeerpower.components.ps4.load_json", return_value=MOCK_GAMES
    ), patch("openpeerpower.components.ps4.save_json", side_effect=MagicMock()), patch(
        "os.path.isfile", return_value=True
    ):
        mock_games = ps4.load_games.opp, MOCK_ENTRY_ID)

    assert isinstance(mock_games, dict)

    mock_data = mock_games[MOCK_ID]
    assert isinstance(mock_data, dict)
    assert mock_data[ATTR_MEDIA_TITLE] == MOCK_TITLE
    assert mock_data[ATTR_MEDIA_IMAGE_URL] == MOCK_URL
    assert mock_data[ATTR_LOCKED] is False
    assert mock_data[ATTR_MEDIA_CONTENT_TYPE] == MEDIA_TYPE_GAME


def test_loading_games_returns_dict.opp):
    """Test that loading games always returns a dict."""
    with patch(
        "openpeerpower.components.ps4.load_json", side_effect=OpenPeerPowerError
    ), patch("openpeerpower.components.ps4.save_json", side_effect=MagicMock()), patch(
        "os.path.isfile", return_value=True
    ):
        mock_games = ps4.load_games.opp, MOCK_ENTRY_ID)

    assert isinstance(mock_games, dict)
    assert not mock_games

    with patch(
        "openpeerpower.components.ps4.load_json", return_value="Some String"
    ), patch("openpeerpower.components.ps4.save_json", side_effect=MagicMock()), patch(
        "os.path.isfile", return_value=True
    ):
        mock_games = ps4.load_games.opp, MOCK_ENTRY_ID)

    assert isinstance(mock_games, dict)
    assert not mock_games

    with patch("openpeerpower.components.ps4.load_json", return_value=[]), patch(
        "openpeerpower.components.ps4.save_json", side_effect=MagicMock()
    ), patch("os.path.isfile", return_value=True):
        mock_games = ps4.load_games.opp, MOCK_ENTRY_ID)

    assert isinstance(mock_games, dict)
    assert not mock_games


async def test_send_command.opp):
    """Test send_command service."""
    await setup_mock_component.opp)

    mock_func = "{}{}".format(
        "openpeerpower.components.ps4", ".media_player.PS4Device.async_send_command"
    )

    mock_devices =.opp.data[PS4_DATA].devices
    assert len(mock_devices) == 1
    mock_entity = mock_devices[0]
    assert mock_entity.entity_id == f"media_player.{MOCK_NAME}"

    # Test that all commands call service function.
    with patch(mock_func, return_value=True) as mock_service:
        for mock_command in COMMANDS:
            await.opp.services.async_call(
                DOMAIN,
                "send_command",
                {ATTR_ENTITY_ID: mock_entity.entity_id, ATTR_COMMAND: mock_command},
            )
            await.opp.async_block_till_done()
    assert len(mock_service.mock_calls) == len(COMMANDS)
