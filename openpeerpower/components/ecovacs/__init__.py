"""Support for Ecovacs Deebot vacuums."""
import logging
import random
import string

from sucks import EcoVacsAPI, VacBot
import voluptuous as vol

from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME, EVENT_OPENPEERPOWER_STOP
from openpeerpower.helpers import discovery
import openpeerpower.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ecovacs"

CONF_COUNTRY = "country"
CONF_CONTINENT = "continent"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Required(CONF_COUNTRY): vol.All(vol.Lower, cv.string),
                vol.Required(CONF_CONTINENT): vol.All(vol.Lower, cv.string),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

ECOVACS_DEVICES = "ecovacs_devices"

# Generate a random device ID on each bootup
ECOVACS_API_DEVICEID = "".join(
    random.choice(string.ascii_uppercase + string.digits) for _ in range(8)
)


def setup(opp, config):
    """Set up the Ecovacs component."""
    _LOGGER.debug("Creating new Ecovacs component")

    opp.data[ECOVACS_DEVICES] = []

    ecovacs_api = EcoVacsAPI(
        ECOVACS_API_DEVICEID,
        config[DOMAIN].get(CONF_USERNAME),
        EcoVacsAPI.md5(config[DOMAIN].get(CONF_PASSWORD)),
        config[DOMAIN].get(CONF_COUNTRY),
        config[DOMAIN].get(CONF_CONTINENT),
    )

    devices = ecovacs_api.devices()
    _LOGGER.debug("Ecobot devices: %s", devices)

    for device in devices:
        _LOGGER.info(
            "Discovered Ecovacs device on account: %s with nickname %s",
            device["did"],
            device["nick"],
        )
        vacbot = VacBot(
            ecovacs_api.uid,
            ecovacs_api.REALM,
            ecovacs_api.resource,
            ecovacs_api.user_access_token,
            device,
            config[DOMAIN].get(CONF_CONTINENT).lower(),
            monitor=True,
        )
        opp.data[ECOVACS_DEVICES].append(vacbot)

    def stop(event: object) -> None:
        """Shut down open connections to Ecovacs XMPP server."""
        for device in opp.data[ECOVACS_DEVICES]:
            _LOGGER.info(
                "Shutting down connection to Ecovacs device %s", device.vacuum["did"]
            )
            device.disconnect()

    # Listen for OP stop to disconnect.
    opp.bus.listen_once(EVENT_OPENPEERPOWER_STOP, stop)

    if opp.data[ECOVACS_DEVICES]:
        _LOGGER.debug("Starting vacuum components")
        discovery.load_platform(opp, "vacuum", DOMAIN, {}, config)

    return True
