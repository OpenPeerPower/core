"""Test Media Source initialization."""
from unittest.mock import patch

import pytest

from openpeerpower.components import media_source
from openpeerpower.components.media_player.const import MEDIA_CLASS_DIRECTORY
from openpeerpower.components.media_player.errors import BrowseError
from openpeerpower.components.media_source import const
from openpeerpower.components.media_source.error import Unresolvable
from openpeerpower.setup import async_setup_component


async def test_is_media_source_id():
    """Test media source validation."""
    assert media_source.is_media_source_id(const.URI_SCHEME)
    assert media_source.is_media_source_id(f"{const.URI_SCHEME}domain")
    assert media_source.is_media_source_id(f"{const.URI_SCHEME}domain/identifier")
    assert not media_source.is_media_source_id("test")


async def test_generate_media_source_id():
    """Test identifier generation."""
    tests = [
        (None, None),
        (None, ""),
        ("", ""),
        ("domain", None),
        ("domain", ""),
        ("domain", "identifier"),
    ]

    for domain, identifier in tests:
        assert media_source.is_media_source_id(
            media_source.generate_media_source_id(domain, identifier)
        )


async def test_async_browse_media.opp):
    """Test browse media."""
    assert await async_setup_component.opp, const.DOMAIN, {})
    await opp.async_block_till_done()

    # Test non-media ignored (/media has test.mp3 and not_media.txt)
    media = await media_source.async_browse_media.opp, "")
    assert isinstance(media, media_source.models.BrowseMediaSource)
    assert media.title == "media/"
    assert len(media.children) == 1

    # Test invalid media content
    with pytest.raises(ValueError):
        await media_source.async_browse_media.opp, "invalid")

    # Test base URI returns all domains
    media = await media_source.async_browse_media.opp, const.URI_SCHEME)
    assert isinstance(media, media_source.models.BrowseMediaSource)
    assert len(media.children) == 1
    assert media.children[0].title == "Local Media"


async def test_async_resolve_media.opp):
    """Test browse media."""
    assert await async_setup_component.opp, const.DOMAIN, {})
    await opp.async_block_till_done()

    media = await media_source.async_resolve_media(
       .opp,
        media_source.generate_media_source_id(const.DOMAIN, "local/test.mp3"),
    )
    assert isinstance(media, media_source.models.PlayMedia)


async def test_async_unresolve_media.opp):
    """Test browse media."""
    assert await async_setup_component.opp, const.DOMAIN, {})
    await opp.async_block_till_done()

    # Test no media content
    with pytest.raises(Unresolvable):
        await media_source.async_resolve_media.opp, "")


async def test_websocket_browse_media.opp, opp_ws_client):
    """Test browse media websocket."""
    assert await async_setup_component.opp, const.DOMAIN, {})
    await opp.async_block_till_done()

    client = await opp_ws_client.opp)

    media = media_source.models.BrowseMediaSource(
        domain=const.DOMAIN,
        identifier="/media",
        title="Local Media",
        media_class=MEDIA_CLASS_DIRECTORY,
        media_content_type="listing",
        can_play=False,
        can_expand=True,
    )

    with patch(
        "openpeerpower.components.media_source.async_browse_media",
        return_value=media,
    ):
        await client.send_json(
            {
                "id": 1,
                "type": "media_source/browse_media",
            }
        )

        msg = await client.receive_json()

    assert msg["success"]
    assert msg["id"] == 1
    assert media.as_dict() == msg["result"]

    with patch(
        "openpeerpower.components.media_source.async_browse_media",
        side_effect=BrowseError("test"),
    ):
        await client.send_json(
            {
                "id": 2,
                "type": "media_source/browse_media",
                "media_content_id": "invalid",
            }
        )

        msg = await client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == "browse_media_failed"
    assert msg["error"]["message"] == "test"


async def test_websocket_resolve_media.opp, opp_ws_client):
    """Test browse media websocket."""
    assert await async_setup_component.opp, const.DOMAIN, {})
    await opp.async_block_till_done()

    client = await opp_ws_client.opp)

    media = media_source.models.PlayMedia("/media/local/test.mp3", "audio/mpeg")

    with patch(
        "openpeerpower.components.media_source.async_resolve_media",
        return_value=media,
    ):
        await client.send_json(
            {
                "id": 1,
                "type": "media_source/resolve_media",
                "media_content_id": f"{const.URI_SCHEME}{const.DOMAIN}/local/test.mp3",
            }
        )

        msg = await client.receive_json()

    assert msg["success"]
    assert msg["id"] == 1
    assert msg["result"]["url"].startswith(media.url)
    assert msg["result"]["mime_type"] == media.mime_type

    with patch(
        "openpeerpower.components.media_source.async_resolve_media",
        side_effect=media_source.Unresolvable("test"),
    ):
        await client.send_json(
            {
                "id": 2,
                "type": "media_source/resolve_media",
                "media_content_id": "invalid",
            }
        )

        msg = await client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == "resolve_media_failed"
    assert msg["error"]["message"] == "test"
