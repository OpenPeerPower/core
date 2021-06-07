"""Automation manager for boards manufactured by ProgettiHWSW Italy."""

from ProgettiHWSW.ProgettiHWSWAPI import ProgettiHWSWAPI
from ProgettiHWSW.input import Input
from ProgettiHWSW.relay import Relay

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower

from .const import DOMAIN

PLATFORMS = ["switch", "binary_sensor"]


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up ProgettiHWSW Automation from a config entry."""
    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = ProgettiHWSWAPI(
        f'{entry.data["host"]}:{entry.data["port"]}'
    )

    # Check board validation again to load new values to API.
    await opp.data[DOMAIN][entry.entry_id].check_board()

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


def setup_input(api: ProgettiHWSWAPI, input_number: int) -> Input:
    """Initialize the input pin."""
    return api.get_input(input_number)


def setup_switch(api: ProgettiHWSWAPI, switch_number: int, mode: str) -> Relay:
    """Initialize the output pin."""
    return api.get_relay(switch_number, mode)
