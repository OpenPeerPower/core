"""Errors for the Plex component."""
from openpeerpower.exceptions import OpenPeerPowerError


class PlexException(OpenPeerPowerError):
    """Base class for Plex exceptions."""


class NoServersFound(PlexException):
    """No servers found on Plex account."""


class ServerNotSpecified(PlexException):
    """Multiple servers linked to account without choice provided."""


class ShouldUpdateConfigEntry(PlexException):
    """Config entry data is out of date and should be updated."""


class MediaNotFound(PlexException):
    """Media lookup failed for a given search query."""
