"""Errors for the Acmeda Pulse component."""
from openpeerpower.exceptions import OpenPeerPowerError


class PulseException(OpenPeerPowerError):
    """Base class for Acmeda Pulse exceptions."""


class CannotConnect(PulseException):
    """Unable to connect to the bridge."""
