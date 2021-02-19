"""Errors for the Hue component."""
from openpeerpower.exceptions import OpenPeerPowerError


class HueException(OpenPeerPowerError):
    """Base class for Hue exceptions."""


class CannotConnect(HueException):
    """Unable to connect to the bridge."""


class AuthenticationRequired(HueException):
    """Unknown error occurred."""
