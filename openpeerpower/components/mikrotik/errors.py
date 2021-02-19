"""Errors for the Mikrotik component."""
from openpeerpower.exceptions import OpenPeerPowerError


class CannotConnect(OpenPeerPowerError):
    """Unable to connect to the hub."""


class LoginError(OpenPeerPowerError):
    """Component got logged out."""
