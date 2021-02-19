"""Errors for the Media Player component."""
from openpeerpower.exceptions import OpenPeerPowerError


class MediaPlayerException(OpenPeerPowerError):
    """Base class for Media Player exceptions."""


class BrowseError(MediaPlayerException):
    """Error while browsing."""
