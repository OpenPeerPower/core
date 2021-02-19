"""Errors for the cert_expiry integration."""
from openpeerpower.exceptions import OpenPeerPowerError


class CertExpiryException(OpenPeerPowerError):
    """Base class for cert_expiry exceptions."""


class TemporaryFailure(CertExpiryException):
    """Temporary failure has occurred."""


class ValidationFailure(CertExpiryException):
    """Certificate validation failure has occurred."""


class ResolveFailed(TemporaryFailure):
    """Name resolution failed."""


class ConnectionTimeout(TemporaryFailure):
    """Network connection timed out."""


class ConnectionRefused(TemporaryFailure):
    """Network connection refused."""
