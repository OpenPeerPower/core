"""Netatmo Media Source Implementation."""
from __future__ import annotations

import datetime as dt
import logging
import re

from openpeerpower.components.media_player.const import (
    MEDIA_CLASS_DIRECTORY,
    MEDIA_CLASS_VIDEO,
    MEDIA_TYPE_VIDEO,
)
from openpeerpower.components.media_player.errors import BrowseError
from openpeerpower.components.media_source.const import MEDIA_MIME_TYPES
from openpeerpower.components.media_source.error import MediaSourceError, Unresolvable
from openpeerpower.components.media_source.models import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
)
from openpeerpower.core import OpenPeerPower, callback

from .const import DATA_CAMERAS, DATA_EVENTS, DOMAIN, MANUFACTURER

_LOGGER = logging.getLogger(__name__)
MIME_TYPE = "application/x-mpegURL"


class IncompatibleMediaSource(MediaSourceError):
    """Incompatible media source attributes."""


async def async_get_media_source(opp: OpenPeerPower):
    """Set up Netatmo media source."""
    return NetatmoSource(opp)


class NetatmoSource(MediaSource):
    """Provide Netatmo camera recordings as media sources."""

    name: str = MANUFACTURER

    def __init__(self, opp: OpenPeerPower) -> None:
        """Initialize Netatmo source."""
        super().__init__(DOMAIN)
        self.opp = opp
        self.events = self.opp.data[DOMAIN][DATA_EVENTS]

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Resolve media to a url."""
        _, camera_id, event_id = async_parse_identifier(item)
        url = self.events[camera_id][event_id]["media_url"]
        return PlayMedia(url, MIME_TYPE)

    async def async_browse_media(
        self, item: MediaSourceItem, media_types: tuple[str] = MEDIA_MIME_TYPES
    ) -> BrowseMediaSource:
        """Return media."""
        try:
            source, camera_id, event_id = async_parse_identifier(item)
        except Unresolvable as err:
            raise BrowseError(str(err)) from err

        return self._browse_media(source, camera_id, event_id)

    def _browse_media(
        self, source: str, camera_id: str, event_id: int
    ) -> BrowseMediaSource:
        """Browse media."""
        if camera_id and camera_id not in self.events:
            raise BrowseError("Camera does not exist.")

        if event_id and event_id not in self.events[camera_id]:
            raise BrowseError("Event does not exist.")

        return self._build_item_response(source, camera_id, event_id)

    def _build_item_response(
        self, source: str, camera_id: str, event_id: int = None
    ) -> BrowseMediaSource:
        if event_id and event_id in self.events[camera_id]:
            created = dt.datetime.fromtimestamp(event_id)
            if self.events[camera_id][event_id]["type"] == "outdoor":
                thumbnail = (
                    self.events[camera_id][event_id]["event_list"][0]
                    .get("snapshot", {})
                    .get("url")
                )
                message = remove_html_tags(
                    self.events[camera_id][event_id]["event_list"][0]["message"]
                )
            else:
                thumbnail = (
                    self.events[camera_id][event_id].get("snapshot", {}).get("url")
                )
                message = remove_html_tags(self.events[camera_id][event_id]["message"])
            title = f"{created} - {message}"
        else:
            title = self.opp.data[DOMAIN][DATA_CAMERAS].get(camera_id, MANUFACTURER)
            thumbnail = None

        if event_id:
            path = f"{source}/{camera_id}/{event_id}"
        else:
            path = f"{source}/{camera_id}"

        media_class = MEDIA_CLASS_DIRECTORY if event_id is None else MEDIA_CLASS_VIDEO

        media = BrowseMediaSource(
            domain=DOMAIN,
            identifier=path,
            media_class=media_class,
            media_content_type=MEDIA_TYPE_VIDEO,
            title=title,
            can_play=bool(
                event_id and self.events[camera_id][event_id].get("media_url")
            ),
            can_expand=event_id is None,
            thumbnail=thumbnail,
        )

        if not media.can_play and not media.can_expand:
            _LOGGER.debug(
                "Camera %s with event %s without media url found", camera_id, event_id
            )
            raise IncompatibleMediaSource

        if not media.can_expand:
            return media

        media.children = []
        # Append first level children
        if not camera_id:
            for cid in self.events:
                child = self._build_item_response(source, cid)
                if child:
                    media.children.append(child)
        else:
            for eid in self.events[camera_id]:
                try:
                    child = self._build_item_response(source, camera_id, eid)
                except IncompatibleMediaSource:
                    continue
                if child:
                    media.children.append(child)

        return media


def remove_html_tags(text):
    """Remove html tags from string."""
    clean = re.compile("<.*?>")
    return re.sub(clean, "", text)


@callback
def async_parse_identifier(
    item: MediaSourceItem,
) -> tuple[str, str, int | None]:
    """Parse identifier."""
    if not item.identifier or "/" not in item.identifier:
        return "events", "", None

    source, path = item.identifier.lstrip("/").split("/", 1)

    if source != "events":
        raise Unresolvable("Unknown source directory.")

    if "/" in path:
        camera_id, event_id = path.split("/", 1)
        return source, camera_id, int(event_id)

    return source, path, None
