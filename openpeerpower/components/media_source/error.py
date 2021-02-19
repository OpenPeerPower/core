"""Errors for media source."""
from openpeerpowerr.exceptions import OpenPeerPowerError


class MediaSourceError(OpenPeerPowerError):
    """Base class for media source errors."""


class Unresolvable(MediaSourceError):
    """When media ID is not resolvable."""
