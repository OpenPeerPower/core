"""Errors for the HLK-SW16 component."""
from openpeerpower.exceptions import OpenPeerPowerError


class SW16Exception(OpenPeerPowerError):
    """Base class for HLK-SW16 exceptions."""


class CannotConnect(SW16Exception):
    """Unable to connect to the HLK-SW16."""
