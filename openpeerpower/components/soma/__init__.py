"""Support for Soma Smartshades."""

from api.soma_api import SomaApi
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_HOST, CONF_PORT
from openpeerpower.core import OpenPeerPower
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.entity import Entity

from .const import API, DOMAIN, HOST, PORT

DEVICES = "devices"

CONFIG_SCHEMA = vol.Schema(
    vol.All(
        cv.deprecated(DOMAIN),
        {
            DOMAIN: vol.Schema(
                {vol.Required(CONF_HOST): cv.string, vol.Required(CONF_PORT): cv.string}
            )
        },
    ),
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = ["cover", "sensor"]


async def async_setup(opp, config):
    """Set up the Soma component."""
    if DOMAIN not in config:
        return True

    opp.async_create_task(
        opp.config_entries.flow.async_init(
            DOMAIN,
            data=config[DOMAIN],
            context={"source": config_entries.SOURCE_IMPORT},
        )
    )

    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Soma from a config entry."""
    opp.data[DOMAIN] = {}
    opp.data[DOMAIN][API] = SomaApi(entry.data[HOST], entry.data[PORT])
    devices = await opp.async_add_executor_job(opp.data[DOMAIN][API].list_devices)
    opp.data[DOMAIN][DEVICES] = devices["shades"]

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    return await opp.config_entries.async_unload_platforms(entry, PLATFORMS)


class SomaEntity(Entity):
    """Representation of a generic Soma device."""

    def __init__(self, device, api):
        """Initialize the Soma device."""
        self.device = device
        self.api = api
        self.current_position = 50
        self.battery_state = 0
        self.is_available = True

    @property
    def available(self):
        """Return true if the last API commands returned successfully."""
        return self.is_available

    @property
    def unique_id(self):
        """Return the unique id base on the id returned by pysoma API."""
        return self.device["mac"]

    @property
    def name(self):
        """Return the name of the device."""
        return self.device["name"]

    @property
    def device_info(self):
        """Return device specific attributes.

        Implemented by platform classes.
        """
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": "Wazombi Labs",
        }
