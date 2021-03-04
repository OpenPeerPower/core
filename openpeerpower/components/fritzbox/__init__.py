"""Support for AVM Fritz!Box smarthome devices."""
import asyncio
import socket

from pyfritzhome import Fritzhome, LoginError
import voluptuous as vol

from openpeerpower.config_entries import SOURCE_IMPORT, SOURCE_REAUTH
from openpeerpower.const import (
    CONF_DEVICES,
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    EVENT_OPENPEERPOWER_STOP,
)
import openpeerpower.helpers.config_validation as cv

from .const import CONF_CONNECTIONS, DEFAULT_HOST, DEFAULT_USERNAME, DOMAIN, PLATFORMS


def ensure_unique_hosts(value):
    """Validate that all configs have a unique host."""
    vol.Schema(vol.Unique("duplicate host entries found"))(
        [socket.gethostbyname(entry[CONF_HOST]) for entry in value]
    )
    return value


CONFIG_SCHEMA = vol.Schema(
    vol.All(
        cv.deprecated(DOMAIN),
        {
            DOMAIN: vol.Schema(
                {
                    vol.Required(CONF_DEVICES): vol.All(
                        cv.ensure_list,
                        [
                            vol.Schema(
                                {
                                    vol.Required(
                                        CONF_HOST, default=DEFAULT_HOST
                                    ): cv.string,
                                    vol.Required(CONF_PASSWORD): cv.string,
                                    vol.Required(
                                        CONF_USERNAME, default=DEFAULT_USERNAME
                                    ): cv.string,
                                }
                            )
                        ],
                        ensure_unique_hosts,
                    )
                }
            )
        },
    ),
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Set up the AVM Fritz!Box integration."""
    if DOMAIN in config:
        for entry_config in config[DOMAIN][CONF_DEVICES]:
            opp.async_create_task(
                opp.config_entries.flow.async_init(
                    DOMAIN, context={"source": SOURCE_IMPORT}, data=entry_config
                )
            )

    return True


async def async_setup_entry(opp, entry):
    """Set up the AVM Fritz!Box platforms."""
    fritz = Fritzhome(
        host=entry.data[CONF_HOST],
        user=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
    )

    try:
        await opp.async_add_executor_job(fritz.login)
    except LoginError:
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_REAUTH},
                data=entry,
            )
        )
        return False

    opp.data.setdefault(DOMAIN, {CONF_CONNECTIONS: {}, CONF_DEVICES: set()})
    opp.data[DOMAIN][CONF_CONNECTIONS][entry.entry_id] = fritz

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    def logout_fritzbox(event):
        """Close connections to this fritzbox."""
        fritz.logout()

    opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, logout_fritzbox)

    return True


async def async_unload_entry(opp, entry):
    """Unloading the AVM Fritz!Box platforms."""
    fritz = opp.data[DOMAIN][CONF_CONNECTIONS][entry.entry_id]
    await opp.async_add_executor_job(fritz.logout)

    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        opp.data[DOMAIN][CONF_CONNECTIONS].pop(entry.entry_id)

    return unload_ok
