"""Support for Twente Milieu."""
from __future__ import annotations

import asyncio
from datetime import timedelta

from twentemilieu import TwenteMilieu
import voluptuous as vol

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_ID
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.dispatcher import async_dispatcher_send
from openpeerpower.helpers.event import async_track_time_interval
from openpeerpower.helpers.typing import ConfigType

from .const import (
    CONF_HOUSE_LETTER,
    CONF_HOUSE_NUMBER,
    CONF_POST_CODE,
    DATA_UPDATE,
    DOMAIN,
)

SCAN_INTERVAL = timedelta(seconds=3600)

SERVICE_UPDATE = "update"
SERVICE_SCHEMA = vol.Schema({vol.Optional(CONF_ID): cv.string})

PLATFORMS = ["sensor"]


async def _update_twentemilieu(opp: OpenPeerPower, unique_id: str | None) -> None:
    """Update Twente Milieu."""
    if unique_id is not None:
        twentemilieu = opp.data[DOMAIN].get(unique_id)
        if twentemilieu is not None:
            await twentemilieu.update()
            async_dispatcher_send(opp, DATA_UPDATE, unique_id)
    else:
        await asyncio.wait(
            [twentemilieu.update() for twentemilieu in opp.data[DOMAIN].values()]
        )

        for uid in opp.data[DOMAIN]:
            async_dispatcher_send(opp, DATA_UPDATE, uid)


async def async_setup(opp: OpenPeerPower, config: ConfigType) -> bool:
    """Set up the Twente Milieu components."""

    async def update(call) -> None:
        """Service call to manually update the data."""
        unique_id = call.data.get(CONF_ID)
        await _update_twentemilieu(opp, unique_id)

    opp.services.async_register(DOMAIN, SERVICE_UPDATE, update, schema=SERVICE_SCHEMA)

    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up Twente Milieu from a config entry."""
    session = async_get_clientsession(opp)
    twentemilieu = TwenteMilieu(
        post_code=entry.data[CONF_POST_CODE],
        house_number=entry.data[CONF_HOUSE_NUMBER],
        house_letter=entry.data[CONF_HOUSE_LETTER],
        session=session,
    )

    unique_id = entry.data[CONF_ID]
    opp.data.setdefault(DOMAIN, {})[unique_id] = twentemilieu

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    async def _interval_update(now=None) -> None:
        """Update Twente Milieu data."""
        await _update_twentemilieu(opp, unique_id)

    async_track_time_interval(opp, _interval_update, SCAN_INTERVAL)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload Twente Milieu config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)

    del opp.data[DOMAIN][entry.data[CONF_ID]]

    return unload_ok
