"""Integrate with NO-IP Dynamic DNS service."""
import asyncio
import base64
from datetime import timedelta
import logging

import aiohttp
from aiohttp.hdrs import AUTHORIZATION, USER_AGENT
import async_timeout
import voluptuous as vol

from openpeerpower.const import CONF_DOMAIN, CONF_PASSWORD, CONF_TIMEOUT, CONF_USERNAME
from openpeerpower.helpers.aiohttp_client import SERVER_SOFTWARE
import openpeerpower.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "no_ip"

# We should set a dedicated address for the user agent.
EMAIL = "hello@openpeerpower.io"

INTERVAL = timedelta(minutes=5)

DEFAULT_TIMEOUT = 10

NO_IP_ERRORS = {
    "nohost": "Hostname supplied does not exist under specified account",
    "badauth": "Invalid username password combination",
    "badagent": "Client disabled",
    "!donator": "An update request was sent with a feature that is not available",
    "abuse": "Username is blocked due to abuse",
    "911": "A fatal error on NO-IP's side such as a database outage",
}

UPDATE_URL = "https://dynupdate.noip.com/nic/update"
HA_USER_AGENT = f"{SERVER_SOFTWARE} {EMAIL}"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_DOMAIN): cv.string,
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Initialize the NO-IP component."""
    domain = config[DOMAIN].get(CONF_DOMAIN)
    user = config[DOMAIN].get(CONF_USERNAME)
    password = config[DOMAIN].get(CONF_PASSWORD)
    timeout = config[DOMAIN].get(CONF_TIMEOUT)

    auth_str = base64.b64encode(f"{user}:{password}".encode("utf-8"))

    session = opp.helpers.aiohttp_client.async_get_clientsession()

    result = await _update_no_ip(opp, session, domain, auth_str, timeout)

    if not result:
        return False

    async def update_domain_interval(now):
        """Update the NO-IP entry."""
        await _update_no_ip(opp, session, domain, auth_str, timeout)

    opp.helpers.event.async_track_time_interval(update_domain_interval, INTERVAL)

    return True


async def _update_no_ip(opp, session, domain, auth_str, timeout):
    """Update NO-IP."""
    url = UPDATE_URL

    params = {"hostname": domain}

    headers = {
        AUTHORIZATION: f"Basic {auth_str.decode('utf-8')}",
        USER_AGENT: HA_USER_AGENT,
    }

    try:
        with async_timeout.timeout(timeout):
            resp = await session.get(url, params=params, headers=headers)
            body = await resp.text()

            if body.startswith("good") or body.startswith("nochg"):
                return True

            _LOGGER.warning(
                "Updating NO-IP failed: %s => %s", domain, NO_IP_ERRORS[body.strip()]
            )

    except aiohttp.ClientError:
        _LOGGER.warning("Can't connect to NO-IP API")

    except asyncio.TimeoutError:
        _LOGGER.warning("Timeout from NO-IP API for domain: %s", domain)

    return False
