"""Errors for the HomematicIP Cloud component."""
from openpeerpower.exceptions import OpenPeerPowerError


class HmipcException(OpenPeerPowerError):
    """Base class for HomematicIP Cloud exceptions."""


class HmipcConnectionError(HmipcException):
    """Unable to connect to the HomematicIP Cloud server."""


class HmipcConnectionWait(HmipcException):
    """Wait for registration to the HomematicIP Cloud server."""


class HmipcRegistrationFailed(HmipcException):
    """Registration on HomematicIP Cloud failed."""


class HmipcPressButton(HmipcException):
    """User needs to press the blue button."""
