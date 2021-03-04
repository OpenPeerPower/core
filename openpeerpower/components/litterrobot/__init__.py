"""The Litter-Robot integration."""
import asyncio

from pylitterbot.exceptions import LitterRobotException, LitterRobotLoginException

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .hub import LitterRobotHub

PLATFORMS = ["sensor", "switch", "vacuum"]


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the Litter-Robot component."""
    opp.data.setdefault(DOMAIN, {})

    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Litter-Robot from a config entry."""
    hub = opp.data[DOMAIN][entry.entry_id] = LitterRobotHub(opp, entry.data)
    try:
        await hub.login(load_robots=True)
    except LitterRobotLoginException:
        return False
    except LitterRobotException as ex:
        raise ConfigEntryNotReady from ex

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
