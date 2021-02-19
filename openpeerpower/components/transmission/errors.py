"""Errors for the Transmission component."""
from openpeerpower.exceptions import OpenPeerPowerError


class AuthenticationError(OpenPeerPowerError):
    """Wrong Username or Password."""


class CannotConnect(OpenPeerPowerError):
    """Unable to connect to client."""


class UnknownError(OpenPeerPowerError):
    """Unknown Error."""
