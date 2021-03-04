"""The nuki component."""

from datetime import timedelta

import voluptuous as vol

from openpeerpower.components.lock import DOMAIN as LOCK_DOMAIN
from openpeerpower.config_entries import SOURCE_IMPORT
from openpeerpower.const import CONF_HOST, CONF_PORT, CONF_TOKEN
import openpeerpower.helpers.config_validation as cv

from .const import DEFAULT_PORT, DOMAIN

PLATFORMS = ["lock"]
UPDATE_INTERVAL = timedelta(seconds=30)

NUKI_SCHEMA = vol.Schema(
    vol.All(
        {
            vol.Required(CONF_HOST): cv.string,
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
            vol.Required(CONF_TOKEN): cv.string,
        },
    )
)


async def async_setup(opp, config):
    """Set up the Nuki component."""
    opp.data.setdefault(DOMAIN, {})

    for platform in PLATFORMS:
        confs = config.get(platform)
        if confs is None:
            continue

        for conf in confs:
            opp.async_create_task(
                opp.config_entries.flow.async_init(
                    DOMAIN, context={"source": SOURCE_IMPORT}, data=conf
                )
            )

    return True


async def async_setup_entry(opp, entry):
    """Set up the Nuki entry."""
    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(entry, LOCK_DOMAIN)
    )

    return True
