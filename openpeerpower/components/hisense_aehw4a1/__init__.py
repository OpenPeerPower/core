"""The Hisense AEH-W4A1 integration."""
import ipaddress
import logging

from pyaehw4a1.aehw4a1 import AehW4a1
import pyaehw4a1.exceptions
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.components.climate import DOMAIN as CLIMATE_DOMAIN
from openpeerpower.const import CONF_IP_ADDRESS
import openpeerpower.helpers.config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def coerce_ip(value):
    """Validate that provided value is a valid IP address."""
    if not value:
        raise vol.Invalid("Must define an IP address")
    try:
        ipaddress.IPv4Network(value)
    except ValueError as err:
        raise vol.Invalid("Not a valid IP address") from err
    return value


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: {
            CLIMATE_DOMAIN: vol.Schema(
                {
                    vol.Optional(CONF_IP_ADDRESS, default=[]): vol.All(
                        cv.ensure_list, [vol.All(cv.string, coerce_ip)]
                    )
                }
            )
        }
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Set up the Hisense AEH-W4A1 integration."""
    conf = config.get(DOMAIN)
    opp.data[DOMAIN] = {}

    if conf is not None:
        devices = conf[CONF_IP_ADDRESS][:]
        for device in devices:
            try:
                await AehW4a1(device).check()
            except pyaehw4a1.exceptions.ConnectionError:
                conf[CONF_IP_ADDRESS].remove(device)
                _LOGGER.warning("Hisense AEH-W4A1 at %s not found", device)
        if conf[CONF_IP_ADDRESS]:
            opp.data[DOMAIN] = conf
            opp.async_create_task(
                opp.config_entries.flow.async_init(
                    DOMAIN,
                    context={"source": config_entries.SOURCE_IMPORT},
                )
            )

    return True


async def async_setup_entry(opp, entry):
    """Set up a config entry for Hisense AEH-W4A1."""
    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(entry, CLIMATE_DOMAIN)
    )

    return True


async def async_unload_entry(opp, entry):
    """Unload a config entry."""
    return await opp.config_entries.async_forward_entry_unload(entry, CLIMATE_DOMAIN)
