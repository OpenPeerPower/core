"""Support for EnOcean devices."""

import voluptuous as vol

from openpeerpower import config_entries, core
from openpeerpower.config_entries import SOURCE_IMPORT
from openpeerpower.const import CONF_DEVICE
import openpeerpower.helpers.config_validation as cv

from .const import DATA_ENOCEAN, DOMAIN, ENOCEAN_DONGLE
from .dongle import EnOceanDongle

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Required(CONF_DEVICE): cv.string})}, extra=vol.ALLOW_EXTRA
)


async def async_setup(opp, config):
    """Set up the EnOcean component."""
    # support for text-based configuration (legacy)
    if DOMAIN not in config:
        return True

    if opp.config_entries.async_entries(DOMAIN):
        # We can only have one dongle. If there is already one in the config,
        # there is no need to import the yaml based config.
        return True

    opp.async_create_task(
        opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=config[DOMAIN]
        )
    )

    return True


async def async_setup_entry(
    opp: core.OpenPeerPower, config_entry: config_entries.ConfigEntry
):
    """Set up an EnOcean dongle for the given entry."""
    enocean_data = opp.data.setdefault(DATA_ENOCEAN, {})
    usb_dongle = EnOceanDongle(opp, config_entry.data[CONF_DEVICE])
    await usb_dongle.async_setup()
    enocean_data[ENOCEAN_DONGLE] = usb_dongle

    return True


async def async_unload_entry(opp, config_entry):
    """Unload ENOcean config entry."""

    enocean_dongle = opp.data[DATA_ENOCEAN][ENOCEAN_DONGLE]
    enocean_dongle.unload()
    opp.data.pop(DATA_ENOCEAN)

    return True
