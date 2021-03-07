"""The SRP Energy integration."""
import logging

from srpenergy.client import SrpEnergyClient

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_ID, CONF_PASSWORD, CONF_USERNAME
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady

from .const import SRP_ENERGY_DOMAIN

_LOGGER = logging.getLogger(__name__)


PLATFORMS = ["sensor"]


async def async_setup(opp, config):
    """Old way of setting up the srp_energy component."""
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up the SRP Energy component from a config entry."""
    # Store an SrpEnergyClient object for your srp_energy to access
    try:
        srp_energy_client = SrpEnergyClient(
            entry.data.get(CONF_ID),
            entry.data.get(CONF_USERNAME),
            entry.data.get(CONF_PASSWORD),
        )
        opp.data[SRP_ENERGY_DOMAIN] = srp_energy_client
    except (Exception) as ex:
        _LOGGER.error("Unable to connect to Srp Energy: %s", str(ex))
        raise ConfigEntryNotReady from ex

    opp.async_create_task(opp.config_entries.async_forward_entry_setup(entry, "sensor"))

    return True


async def async_unload_entry(opp: OpenPeerPower, config_entry: ConfigEntry):
    """Unload a config entry."""
    # unload srp client
    opp.data[SRP_ENERGY_DOMAIN] = None
    # Remove config entry
    await opp.config_entries.async_forward_entry_unload(config_entry, "sensor")

    return True
