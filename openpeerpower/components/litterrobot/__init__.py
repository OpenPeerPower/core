"""The Litter-Robot integration."""

from pylitterbot.exceptions import LitterRobotException, LitterRobotLoginException

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .hub import LitterRobotHub

PLATFORMS = ["sensor", "switch", "vacuum"]


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up Litter-Robot from a config entry."""
    opp.data.setdefault(DOMAIN, {})
    hub = opp.data[DOMAIN][entry.entry_id] = LitterRobotHub(opp, entry.data)
    try:
        await hub.login(load_robots=True)
    except LitterRobotLoginException:
        return False
    except LitterRobotException as ex:
        raise ConfigEntryNotReady from ex

    if hub.account.robots:
        opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
