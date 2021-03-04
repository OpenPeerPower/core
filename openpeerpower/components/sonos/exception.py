"""Sonos specific exceptions."""
from openpeerpower.components.media_player.errors import BrowseError


class UnknownMediaType(BrowseError):
    """Unknown media type."""
