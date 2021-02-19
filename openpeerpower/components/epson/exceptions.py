"""The errors of Epson integration."""
from openpeerpower import exceptions


class CannotConnect(exceptions.OpenPeerPowerError):
    """Error to indicate we cannot connect."""
