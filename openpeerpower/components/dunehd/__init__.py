"""The Dune HD component."""
from __future__ import annotations

from typing import Final

from pdunehd import DuneHDPlayer

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_HOST
from openpeerpower.core import OpenPeerPower

from .const import DOMAIN

PLATFORMS: Final[list[str]] = ["media_player"]


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    host: str = entry.data[CONF_HOST]

    player = DuneHDPlayer(host)

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = player

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
