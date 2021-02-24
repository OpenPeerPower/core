"""Support for Mythic Beasts Dynamic DNS service."""
from datetime import timedelta

import mbddns
import voluptuous as vol

from openpeerpower.const import (
    CONF_DOMAIN,
    CONF_HOST,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
)
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.event import async_track_time_interval

DOMAIN = "mythicbeastsdns"

DEFAULT_INTERVAL = timedelta(minutes=10)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_DOMAIN): cv.string,
                vol.Required(CONF_HOST): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_INTERVAL): vol.All(
                    cv.time_period, cv.positive_timedelta
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Initialize the Mythic Beasts component."""
    domain = config[DOMAIN][CONF_DOMAIN]
    password = config[DOMAIN][CONF_PASSWORD]
    host = config[DOMAIN][CONF_HOST]
    update_interval = config[DOMAIN][CONF_SCAN_INTERVAL]

    session = async_get_clientsession(opp)

    result = await mbddns.update(domain, password, host, session=session)

    if not result:
        return False

    async def update_domain_interval(now):
        """Update the DNS entry."""
        await mbddns.update(domain, password, host, session=session)

    async_track_time_interval(opp, update_domain_interval, update_interval)

    return True
