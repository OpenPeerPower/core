"""Errors for the UniFi component."""
from openpeerpower.exceptions import OpenPeerPowerError


class UnifiException(OpenPeerPowerError):
    """Base class for UniFi exceptions."""


class AlreadyConfigured(UnifiException):
    """Controller is already configured."""


class AuthenticationRequired(UnifiException):
    """Unknown error occurred."""


class CannotConnect(UnifiException):
    """Unable to connect to the controller."""


class LoginRequired(UnifiException):
    """Component got logged out."""


class UserLevel(UnifiException):
    """User level too low."""
