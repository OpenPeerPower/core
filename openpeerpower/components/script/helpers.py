"""Helpers for automation integration."""
from openpeerpower.components.blueprint import DomainBlueprints
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.helpers.singleton import singleton

from .const import DOMAIN, LOGGER

DATA_BLUEPRINTS = "script_blueprints"


@singleton(DATA_BLUEPRINTS)
@callback
def async_get_blueprints(opp: OpenPeerPower) -> DomainBlueprints:
    """Get script blueprints."""
    return DomainBlueprints(opp, DOMAIN, LOGGER)
