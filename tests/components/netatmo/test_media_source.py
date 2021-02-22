"""Test Local Media Source."""
import ast

import pytest

from openpeerpower.components import media_source
from openpeerpower.components.media_source import const
from openpeerpower.components.media_source.models import PlayMedia
from openpeerpower.components.netatmo import DATA_CAMERAS, DATA_EVENTS, DOMAIN
from openpeerpower.setup import async_setup_component

from tests.common import load_fixture


async def test_async_browse_media.opp):
    """Test browse media."""
    assert await async_setup_component.opp, DOMAIN, {})

    # Prepare cached Netatmo event date
   .opp.data[DOMAIN] = {}
   .opp.data[DOMAIN][DATA_EVENTS] = ast.literal_eval(
        load_fixture("netatmo/events.txt")
    )

   .opp.data[DOMAIN][DATA_CAMERAS] = {
        "12:34:56:78:90:ab": "MyCamera",
        "12:34:56:78:90:ac": "MyOutdoorCamera",
    }

    assert await async_setup_component.opp, const.DOMAIN, {})
    await.opp.async_block_till_done()

    # Test camera not exists
    with pytest.raises(media_source.BrowseError) as excinfo:
        await media_source.async_browse_media(
           .opp, f"{const.URI_SCHEME}{DOMAIN}/events/98:76:54:32:10:ff"
        )
    assert str(excinfo.value) == "Camera does not exist."

    # Test browse event
    with pytest.raises(media_source.BrowseError) as excinfo:
        await media_source.async_browse_media(
           .opp, f"{const.URI_SCHEME}{DOMAIN}/events/12:34:56:78:90:ab/12345"
        )
    assert str(excinfo.value) == "Event does not exist."

    # Test invalid base
    with pytest.raises(media_source.BrowseError) as excinfo:
        await media_source.async_browse_media(
           .opp, f"{const.URI_SCHEME}{DOMAIN}/invalid/base"
        )
    assert str(excinfo.value) == "Unknown source directory."

    # Test successful listing
    media = await media_source.async_browse_media(
       .opp, f"{const.URI_SCHEME}{DOMAIN}/events/"
    )

    # Test successful events listing
    media = await media_source.async_browse_media(
       .opp, f"{const.URI_SCHEME}{DOMAIN}/events/12:34:56:78:90:ab"
    )

    # Test successful event listing
    media = await media_source.async_browse_media(
       .opp, f"{const.URI_SCHEME}{DOMAIN}/events/12:34:56:78:90:ab/1599152672"
    )
    assert media

    # Test successful event resolve
    media = await media_source.async_resolve_media(
       .opp, f"{const.URI_SCHEME}{DOMAIN}/events/12:34:56:78:90:ab/1599152672"
    )
    assert media == PlayMedia(
        url="http:///files/high/index.m3u8", mime_type="application/x-mpegURL"
    )
