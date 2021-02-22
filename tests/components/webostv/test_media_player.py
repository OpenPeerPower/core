"""The tests for the LG webOS media player platform."""

from unittest.mock import patch

import pytest

from openpeerpower.components import media_player
from openpeerpower.components.media_player.const import (
    ATTR_INPUT_SOURCE,
    ATTR_MEDIA_VOLUME_MUTED,
    SERVICE_SELECT_SOURCE,
)
from openpeerpower.components.webostv.const import (
    ATTR_BUTTON,
    ATTR_COMMAND,
    ATTR_PAYLOAD,
    DOMAIN,
    SERVICE_BUTTON,
    SERVICE_COMMAND,
)
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    CONF_HOST,
    CONF_NAME,
    SERVICE_VOLUME_MUTE,
)
from openpeerpower.setup import async_setup_component

NAME = "fake"
ENTITY_ID = f"{media_player.DOMAIN}.{NAME}"


@pytest.fixture(name="client")
def client_fixture():
    """Patch of client library for tests."""
    with patch(
        "openpeerpower.components.webostv.WebOsClient", autospec=True
    ) as mock_client_class:
        client = mock_client_class.return_value
        client.software_info = {"device_id": "a1:b1:c1:d1:e1:f1"}
        client.client_key = "0123456789"
        yield client


async def setup_webostv.opp):
    """Initialize webostv and media_player for tests."""
    assert await async_setup_component(
       .opp,
        DOMAIN,
        {DOMAIN: {CONF_HOST: "fake", CONF_NAME: NAME}},
    )
    await opp.async_block_till_done()


async def test_mute.opp, client):
    """Test simple service call."""

    await setup_webostv.opp)

    data = {
        ATTR_ENTITY_ID: ENTITY_ID,
        ATTR_MEDIA_VOLUME_MUTED: True,
    }
    await opp.services.async_call(media_player.DOMAIN, SERVICE_VOLUME_MUTE, data)
    await opp.async_block_till_done()

    client.set_mute.assert_called_once()


async def test_select_source_with_empty_source_list.opp, client):
    """Ensure we don't call client methods when we don't have sources."""

    await setup_webostv.opp)

    data = {
        ATTR_ENTITY_ID: ENTITY_ID,
        ATTR_INPUT_SOURCE: "nonexistent",
    }
    await opp.services.async_call(media_player.DOMAIN, SERVICE_SELECT_SOURCE, data)
    await opp.async_block_till_done()

    client.launch_app.assert_not_called()
    client.set_input.assert_not_called()


async def test_button.opp, client):
    """Test generic button functionality."""

    await setup_webostv.opp)

    data = {
        ATTR_ENTITY_ID: ENTITY_ID,
        ATTR_BUTTON: "test",
    }
    await opp.services.async_call(DOMAIN, SERVICE_BUTTON, data)
    await opp.async_block_till_done()

    client.button.assert_called_once()
    client.button.assert_called_with("test")


async def test_command.opp, client):
    """Test generic command functionality."""
    await setup_webostv.opp)

    data = {
        ATTR_ENTITY_ID: ENTITY_ID,
        ATTR_COMMAND: "test",
    }
    await opp.services.async_call(DOMAIN, SERVICE_COMMAND, data)
    await opp.async_block_till_done()

    client.request.assert_called_with("test", payload=None)


async def test_command_with_optional_arg.opp, client):
    """Test generic command functionality."""
    await setup_webostv.opp)

    data = {
        ATTR_ENTITY_ID: ENTITY_ID,
        ATTR_COMMAND: "test",
        ATTR_PAYLOAD: {"target": "https://www.google.com"},
    }
    await opp.services.async_call(DOMAIN, SERVICE_COMMAND, data)
    await opp.async_block_till_done()

    client.request.assert_called_with(
        "test", payload={"target": "https://www.google.com"}
    )
