"""Custom exceptions for the devolo_home_control integration."""
from openpeerpower.exceptions import OpenPeerPowerError


class CredentialsInvalid(OpenPeerPowerError):
    """Given credentials are invalid."""
