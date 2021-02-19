"""Shared exceptions for the august integration."""

from openpeerpower import exceptions


class RequireValidation(exceptions.OpenPeerPowerError):
    """Error to indicate we require validation (2fa)."""


class CannotConnect(exceptions.OpenPeerPowerError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.OpenPeerPowerError):
    """Error to indicate there is invalid auth."""
