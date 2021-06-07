"""The errors of Epson integration."""
from openpeerpower import exceptions


class CannotConnect(exceptions.OpenPeerPowerError):
    """Error to indicate we cannot connect."""


class PoweredOff(exceptions.OpenPeerPowerError):
    """Error to indicate projector is off."""
