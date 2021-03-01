"""The Remote Python Debugger integration."""
from asyncio import Event
import logging
from threading import Thread
from typing import Optional

import debugpy
import voluptuous as vol

from openpeerpower.const import CONF_HOST, CONF_PORT
from openpeerpower.core import OpenPeerPower, ServiceCall
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.service import async_register_admin_service
from openpeerpower.helpers.typing import ConfigType

DOMAIN = "debugpy"
CONF_WAIT = "wait"
CONF_START = "start"
SERVICE_START = "start"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_HOST, default="0.0.0.0"): cv.string,
                vol.Optional(CONF_PORT, default=5678): cv.port,
                vol.Optional(CONF_START, default=True): cv.boolean,
                vol.Optional(CONF_WAIT, default=False): cv.boolean,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup(opp: OpenPeerPower, config: ConfigType) -> bool:
    """Set up the Remote Python Debugger component."""
    conf = config[DOMAIN]

    async def debug_start(
        call: Optional[ServiceCall] = None, *, wait: bool = True
    ) -> None:
        """Start the debugger."""
        debugpy.listen((conf[CONF_HOST], conf[CONF_PORT]))

        wait = conf[CONF_WAIT]
        if wait:
            _LOGGER.warning(
                "Waiting for remote debug connection on %s:%s",
                conf[CONF_HOST],
                conf[CONF_PORT],
            )
            ready = Event()

            def waitfor():
                debugpy.wait_for_client()
                opp.loop.call_soon_threadsafe(ready.set)

            Thread(target=waitfor).start()

            await ready.wait()
        else:
            _LOGGER.warning(
                "Listening for remote debug connection on %s:%s",
                conf[CONF_HOST],
                conf[CONF_PORT],
            )

    async_register_admin_service(
        opp, DOMAIN, SERVICE_START, debug_start, schema=vol.Schema({})
    )

    # If set to start the debugger on startup, do so
    if conf[CONF_START]:
        await debug_start(wait=conf[CONF_WAIT])

    return True
