"""Support for TP-Link LTE modems."""
import asyncio
import logging

import aiohttp
import attr
import tp_connected
import voluptuous as vol

from openpeerpower.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_RECIPIENT,
    EVENT_OPENPEERPOWER_STOP,
)
from openpeerpower.core import callback
from openpeerpower.helpers import config_validation as cv, discovery
from openpeerpower.helpers.aiohttp_client import async_create_clientsession

_LOGGER = logging.getLogger(__name__)

DOMAIN = "tplink_lte"
DATA_KEY = "tplink_lte"

CONF_NOTIFY = "notify"

_NOTIFY_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_RECIPIENT): vol.All(cv.ensure_list, [cv.string]),
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            cv.ensure_list,
            [
                vol.Schema(
                    {
                        vol.Required(CONF_HOST): cv.string,
                        vol.Required(CONF_PASSWORD): cv.string,
                        vol.Optional(CONF_NOTIFY): vol.All(
                            cv.ensure_list, [_NOTIFY_SCHEMA]
                        ),
                    }
                )
            ],
        )
    },
    extra=vol.ALLOW_EXTRA,
)


@attr.s
class ModemData:
    """Class for modem state."""

    host = attr.ib()
    modem = attr.ib()

    connected = attr.ib(init=False, default=True)


@attr.s
class LTEData:
    """Shared state."""

    websession = attr.ib()
    modem_data = attr.ib(init=False, factory=dict)

    def get_modem_data(self, config):
        """Get the requested or the only modem_data value."""
        if CONF_HOST in config:
            return self.modem_data.get(config[CONF_HOST])
        if len(self.modem_data) == 1:
            return next(iter(self.modem_data.values()))

        return None


async def async_setup(opp, config):
    """Set up TP-Link LTE component."""
    if DATA_KEY not in opp.data:
        websession = async_create_clientsession(
            opp, cookie_jar=aiohttp.CookieJar(unsafe=True)
        )
        opp.data[DATA_KEY] = LTEData(websession)

    domain_config = config.get(DOMAIN, [])

    tasks = [_setup_lte(opp, conf) for conf in domain_config]
    if tasks:
        await asyncio.wait(tasks)

    for conf in domain_config:
        for notify_conf in conf.get(CONF_NOTIFY, []):
            opp.async_create_task(
                discovery.async_load_platform(
                    opp, "notify", DOMAIN, notify_conf, config
                )
            )

    return True


async def _setup_lte(opp, lte_config, delay=0):
    """Set up a TP-Link LTE modem."""

    host = lte_config[CONF_HOST]
    password = lte_config[CONF_PASSWORD]

    websession = opp.data[DATA_KEY].websession
    modem = tp_connected.Modem(hostname=host, websession=websession)

    modem_data = ModemData(host, modem)

    try:
        await _login(opp, modem_data, password)
    except tp_connected.Error:
        retry_task = opp.loop.create_task(_retry_login(opp, modem_data, password))

        @callback
        def cleanup_retry(event):
            """Clean up retry task resources."""
            if not retry_task.done():
                retry_task.cancel()

        opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, cleanup_retry)


async def _login(opp, modem_data, password):
    """Log in and complete setup."""
    await modem_data.modem.login(password=password)
    modem_data.connected = True
    opp.data[DATA_KEY].modem_data[modem_data.host] = modem_data

    async def cleanup(event):
        """Clean up resources."""
        await modem_data.modem.logout()

    opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, cleanup)


async def _retry_login(opp, modem_data, password):
    """Sleep and retry setup."""

    _LOGGER.warning("Could not connect to %s. Will keep trying", modem_data.host)

    modem_data.connected = False
    delay = 15

    while not modem_data.connected:
        await asyncio.sleep(delay)

        try:
            await _login(opp, modem_data, password)
            _LOGGER.warning("Connected to %s", modem_data.host)
        except tp_connected.Error:
            delay = min(2 * delay, 300)
