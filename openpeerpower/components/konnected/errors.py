"""Errors for the Konnected component."""
from openpeerpower.exceptions import OpenPeerPowerError


class KonnectedException(OpenPeerPowerError):
    """Base class for Konnected exceptions."""


class CannotConnect(KonnectedException):
    """Unable to connect to the panel."""
