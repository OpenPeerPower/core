"""Test Local Media Source."""
import pytest

from openpeerpower.components import media_source
from openpeerpower.components.media_source import const
from openpeerpower.config import async_process_op_core_config
from openpeerpower.setup import async_setup_component


async def test_async_browse_media(opp):
    """Test browse media."""
    local_media = opp.config.path("media")
    await async_process_op_core_config(
        opp, {"media_dirs": {"local": local_media, "recordings": local_media}}
    )
    await opp.async_block_till_done()

    assert await async_setup_component(opp, const.DOMAIN, {})
    await opp.async_block_till_done()

    # Test path not exists
    with pytest.raises(media_source.BrowseError) as excinfo:
        await media_source.async_browse_media(
            opp, f"{const.URI_SCHEME}{const.DOMAIN}/local/test/not/exist"
        )
    assert str(excinfo.value) == "Path does not exist."

    # Test browse file
    with pytest.raises(media_source.BrowseError) as excinfo:
        await media_source.async_browse_media(
            opp, f"{const.URI_SCHEME}{const.DOMAIN}/local/test.mp3"
        )
    assert str(excinfo.value) == "Path is not a directory."

    # Test invalid base
    with pytest.raises(media_source.BrowseError) as excinfo:
        await media_source.async_browse_media(
            opp, f"{const.URI_SCHEME}{const.DOMAIN}/invalid/base"
        )
    assert str(excinfo.value) == "Unknown source directory."

    # Test directory traversal
    with pytest.raises(media_source.BrowseError) as excinfo:
        await media_source.async_browse_media(
            opp, f"{const.URI_SCHEME}{const.DOMAIN}/local/../configuration.yaml"
        )
    assert str(excinfo.value) == "Invalid path."

    # Test successful listing
    media = await media_source.async_browse_media(
        opp, f"{const.URI_SCHEME}{const.DOMAIN}"
    )
    assert media

    media = await media_source.async_browse_media(
        opp, f"{const.URI_SCHEME}{const.DOMAIN}/local/."
    )
    assert media

    media = await media_source.async_browse_media(
        opp, f"{const.URI_SCHEME}{const.DOMAIN}/recordings/."
    )
    assert media


async def test_media_view(opp, opp_client):
    """Test media view."""
    local_media = opp.config.path("media")
    await async_process_op_core_config(
        opp, {"media_dirs": {"local": local_media, "recordings": local_media}}
    )
    await opp.async_block_till_done()

    assert await async_setup_component(opp, const.DOMAIN, {})
    await opp.async_block_till_done()

    client = await opp_client()

    # Protects against non-existent files
    resp = await client.get("/media/local/invalid.txt")
    assert resp.status == 404

    resp = await client.get("/media/recordings/invalid.txt")
    assert resp.status == 404

    # Protects against non-media files
    resp = await client.get("/media/local/not_media.txt")
    assert resp.status == 404

    # Protects against unknown local media sources
    resp = await client.get("/media/unknown_source/not_media.txt")
    assert resp.status == 404

    # Fetch available media
    resp = await client.get("/media/local/test.mp3")
    assert resp.status == 200

    resp = await client.get("/media/local/Epic Sax Guy 10 Hours.mp4")
    assert resp.status == 200

    resp = await client.get("/media/recordings/test.mp3")
    assert resp.status == 200
