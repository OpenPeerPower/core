"""Errors for media source."""
from openpeerpower.exceptions import OpenPeerPowerError


class MediaSourceError(OpenPeerPowerError):
    """Base class for media source errors."""


class Unresolvable(MediaSourceError):
    """When media ID is not resolvable."""
