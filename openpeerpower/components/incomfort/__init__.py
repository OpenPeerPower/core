"""Support for an Intergas boiler via an InComfort/Intouch Lan2RF gateway."""
import logging
from typing import Optional

from aiohttp import ClientResponseError
from incomfortclient import Gateway as InComfortGateway
import voluptuous as vol

from openpeerpower.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from openpeerpower.core import callback
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.discovery import async_load_platform
from openpeerpower.helpers.dispatcher import async_dispatcher_connect
from openpeerpower.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

DOMAIN = "incomfort"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Inclusive(CONF_USERNAME, "credentials"): cv.string,
                vol.Inclusive(CONF_PASSWORD, "credentials"): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, opp_config):
    """Create an Intergas InComfort/Intouch system."""
    incomfort_data = opp.data[DOMAIN] = {}

    credentials = dict(opp_config[DOMAIN])
    hostname = credentials.pop(CONF_HOST)

    client = incomfort_data["client"] = InComfortGateway(
        hostname, **credentials, session=async_get_clientsession(opp)
    )

    try:
        heaters = incomfort_data["heaters"] = list(await client.heaters)
    except ClientResponseError as err:
        _LOGGER.warning("Setup failed, check your configuration, message is: %s", err)
        return False

    for heater in heaters:
        await heater.update()

    for platform in ["water_heater", "binary_sensor", "sensor", "climate"]:
        opp.async_create_task(
            async_load_platform(opp, platform, DOMAIN, {}, opp_config)
        )

    return True


class IncomfortEntity(Entity):
    """Base class for all InComfort entities."""

    def __init__(self) -> None:
        """Initialize the class."""
        self._unique_id = self._name = None

    @property
    def unique_id(self) -> Optional[str]:
        """Return a unique ID."""
        return self._unique_id

    @property
    def name(self) -> Optional[str]:
        """Return the name of the sensor."""
        return self._name


class IncomfortChild(IncomfortEntity):
    """Base class for all InComfort entities (excluding the boiler)."""

    async def async_added_to_opp(self) -> None:
        """Set up a listener when this entity is added to HA."""
        self.async_on_remove(async_dispatcher_connect(self.opp, DOMAIN, self._refresh))

    @callback
    def _refresh(self) -> None:
        self.async_schedule_update_op_state(force_refresh=True)

    @property
    def should_poll(self) -> bool:
        """Return False as this device should never be polled."""
        return False
