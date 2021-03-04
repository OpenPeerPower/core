"""The media_source integration."""
from datetime import timedelta
from typing import Optional

import voluptuous as vol

from openpeerpower.components import websocket_api
from openpeerpower.components.http.auth import async_sign_path
from openpeerpower.components.media_player.const import ATTR_MEDIA_CONTENT_ID
from openpeerpower.components.media_player.errors import BrowseError
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.helpers.integration_platform import (
    async_process_integration_platforms,
)
from openpeerpower.loader import bind_opp

from . import local_source, models
from .const import DOMAIN, URI_SCHEME, URI_SCHEME_REGEX
from .error import Unresolvable


def is_media_source_id(media_content_id: str):
    """Test if identifier is a media source."""
    return URI_SCHEME_REGEX.match(media_content_id) is not None


def generate_media_source_id(domain: str, identifier: str) -> str:
    """Generate a media source ID."""
    uri = f"{URI_SCHEME}{domain or ''}"
    if identifier:
        uri += f"/{identifier}"
    return uri


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the media_source component."""
    opp.data[DOMAIN] = {}
    opp.components.websocket_api.async_register_command(websocket_browse_media)
    opp.components.websocket_api.async_register_command(websocket_resolve_media)
    opp.components.frontend.async_register_built_in_panel(
        "media-browser", "media_browser", "opp:play-box-multiple"
    )
    local_source.async_setup(opp)
    await async_process_integration_platforms(
        opp, DOMAIN, _process_media_source_platform
    )
    return True


async def _process_media_source_platform(opp, domain, platform):
    """Process a media source platform."""
    opp.data[DOMAIN][domain] = await platform.async_get_media_source(opp)


@callback
def _get_media_item(
    opp: OpenPeerPower, media_content_id: Optional[str]
) -> models.MediaSourceItem:
    """Return media item."""
    if media_content_id:
        return models.MediaSourceItem.from_uri(opp, media_content_id)

    # We default to our own domain if its only one registered
    domain = None if len(opp.data[DOMAIN]) > 1 else DOMAIN
    return models.MediaSourceItem(opp, domain, "")


@bind_opp
async def async_browse_media(
    opp: OpenPeerPower, media_content_id: str
) -> models.BrowseMediaSource:
    """Return media player browse media results."""
    return await _get_media_item(opp, media_content_id).async_browse()


@bind_opp
async def async_resolve_media(
    opp: OpenPeerPower, media_content_id: str
) -> models.PlayMedia:
    """Get info to play media."""
    return await _get_media_item(opp, media_content_id).async_resolve()


@websocket_api.websocket_command(
    {
        vol.Required("type"): "media_source/browse_media",
        vol.Optional(ATTR_MEDIA_CONTENT_ID, default=""): str,
    }
)
@websocket_api.async_response
async def websocket_browse_media(opp, connection, msg):
    """Browse available media."""
    try:
        media = await async_browse_media(opp, msg.get("media_content_id"))
        connection.send_result(
            msg["id"],
            media.as_dict(),
        )
    except BrowseError as err:
        connection.send_error(msg["id"], "browse_media_failed", str(err))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "media_source/resolve_media",
        vol.Required(ATTR_MEDIA_CONTENT_ID): str,
        vol.Optional("expires", default=30): int,
    }
)
@websocket_api.async_response
async def websocket_resolve_media(opp, connection, msg):
    """Resolve media."""
    try:
        media = await async_resolve_media(opp, msg["media_content_id"])
        url = media.url
    except Unresolvable as err:
        connection.send_error(msg["id"], "resolve_media_failed", str(err))
    else:
        if url[0] == "/":
            url = async_sign_path(
                opp,
                connection.refresh_token_id,
                url,
                timedelta(seconds=msg["expires"]),
            )

        connection.send_result(msg["id"], {"url": url, "mime_type": media.mime_type})
