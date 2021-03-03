"""Helpers for automation integration."""
from openpeerpower.components import blueprint
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.helpers.singleton import singleton

from .const import DOMAIN, LOGGER

DATA_BLUEPRINTS = "automation_blueprints"


@singleton(DATA_BLUEPRINTS)
@callback
def async_get_blueprints(opp: OpenPeerPower) -> blueprint.DomainBlueprints:  # type: ignore
    """Get automation blueprints."""
    return blueprint.DomainBlueprints(opp, DOMAIN, LOGGER)  # type: ignore
