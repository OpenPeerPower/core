"""Test the base functions of the media player."""
import base64
from unittest.mock import patch

from openpeerpower.components import media_player
from openpeerpower.components.websocket_api.const import TYPE_RESULT
from openpeerpower.setup import async_setup_component


async def test_get_image(opp, opp_ws_client, caplog):
    """Test get image via WS command."""
    await async_setup_component(
        opp, "media_player", {"media_player": {"platform": "demo"}}
    )
    await opp.async_block_till_done()

    client = await opp_ws_client(opp)

    with patch(
        "openpeerpower.components.media_player.MediaPlayerEntity."
        "async_get_media_image",
        return_value=(b"image", "image/jpeg"),
    ):
        await client.send_json(
            {
                "id": 5,
                "type": "media_player_thumbnail",
                "entity_id": "media_player.bedroom",
            }
        )

        msg = await client.receive_json()

    assert msg["id"] == 5
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]
    assert msg["result"]["content_type"] == "image/jpeg"
    assert msg["result"]["content"] == base64.b64encode(b"image").decode("utf-8")

    assert "media_player_thumbnail is deprecated" in caplog.text


async def test_get_image_http(opp, aiohttp_client):
    """Test get image via http command."""
    await async_setup_component(
        opp, "media_player", {"media_player": {"platform": "demo"}}
    )
    await opp.async_block_till_done()

    state = opp.states.get("media_player.bedroom")
    assert "entity_picture_local" not in state.attributes

    client = await aiohttp_client(opp.http.app)

    with patch(
        "openpeerpower.components.media_player.MediaPlayerEntity."
        "async_get_media_image",
        return_value=(b"image", "image/jpeg"),
    ):
        resp = await client.get(state.attributes["entity_picture"])
        content = await resp.read()

    assert content == b"image"


async def test_get_image_http_remote(opp, aiohttp_client):
    """Test get image url via http command."""
    with patch(
        "openpeerpower.components.media_player.MediaPlayerEntity."
        "media_image_remotely_accessible",
        return_value=True,
    ):
        await async_setup_component(
            opp, "media_player", {"media_player": {"platform": "demo"}}
        )
        await opp.async_block_till_done()

        state = opp.states.get("media_player.bedroom")
        assert "entity_picture_local" in state.attributes

        client = await aiohttp_client(opp.http.app)

        with patch(
            "openpeerpower.components.media_player.MediaPlayerEntity."
            "async_get_media_image",
            return_value=(b"image", "image/jpeg"),
        ):
            resp = await client.get(state.attributes["entity_picture_local"])
            content = await resp.read()

        assert content == b"image"


async def test_get_async_get_browse_image(opp, aiohttp_client, opp_ws_client):
    """Test get browse image."""
    await async_setup_component(
        opp, "media_player", {"media_player": {"platform": "demo"}}
    )
    await opp.async_block_till_done()

    entity_comp = opp.data.get("entity_components", {}).get("media_player")
    assert entity_comp

    player = entity_comp.get_entity("media_player.bedroom")
    assert player

    client = await aiohttp_client(opp.http.app)

    with patch(
        "openpeerpower.components.media_player.MediaPlayerEntity."
        "async_get_browse_image",
        return_value=(b"image", "image/jpeg"),
    ):
        url = player.get_browse_image_url("album", "abcd")
        resp = await client.get(url)
        content = await resp.read()

    assert content == b"image"


def test_deprecated_base_class(caplog):
    """Test deprecated base class."""

    class CustomMediaPlayer(media_player.MediaPlayerDevice):
        pass

    CustomMediaPlayer()
    assert "MediaPlayerDevice is deprecated, modify CustomMediaPlayer" in caplog.text


async def test_media_browse(opp, opp_ws_client):
    """Test browsing media."""
    await async_setup_component(
        opp, "media_player", {"media_player": {"platform": "demo"}}
    )
    await opp.async_block_till_done()

    client = await opp_ws_client(opp)

    with patch(
        "openpeerpower.components.demo.media_player.YOUTUBE_PLAYER_SUPPORT",
        media_player.SUPPORT_BROWSE_MEDIA,
    ), patch(
        "openpeerpower.components.media_player.MediaPlayerEntity." "async_browse_media",
        return_value={"bla": "yo"},
    ) as mock_browse_media:
        await client.send_json(
            {
                "id": 5,
                "type": "media_player/browse_media",
                "entity_id": "media_player.bedroom",
                "media_content_type": "album",
                "media_content_id": "abcd",
            }
        )

        msg = await client.receive_json()

    assert msg["id"] == 5
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]
    assert msg["result"] == {"bla": "yo"}
    assert mock_browse_media.mock_calls[0][1] == ("album", "abcd")

    with patch(
        "openpeerpower.components.demo.media_player.YOUTUBE_PLAYER_SUPPORT",
        media_player.SUPPORT_BROWSE_MEDIA,
    ), patch(
        "openpeerpower.components.media_player.MediaPlayerEntity." "async_browse_media",
        return_value={"bla": "yo"},
    ):
        await client.send_json(
            {
                "id": 6,
                "type": "media_player/browse_media",
                "entity_id": "media_player.bedroom",
            }
        )

        msg = await client.receive_json()

    assert msg["id"] == 6
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]
    assert msg["result"] == {"bla": "yo"}
