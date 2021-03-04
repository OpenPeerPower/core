"""Support for ecobee."""
import asyncio
from datetime import timedelta

from pyecobee import ECOBEE_API_KEY, ECOBEE_REFRESH_TOKEN, Ecobee, ExpiredTokenError
import voluptuous as vol

from openpeerpower.config_entries import SOURCE_IMPORT
from openpeerpower.const import CONF_API_KEY
from openpeerpower.helpers import config_validation as cv
from openpeerpower.util import Throttle

from .const import _LOGGER, CONF_REFRESH_TOKEN, DATA_ECOBEE_CONFIG, DOMAIN, PLATFORMS

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=180)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Optional(CONF_API_KEY): cv.string})}, extra=vol.ALLOW_EXTRA
)


async def async_setup(opp, config):
    """
    Ecobee uses config flow for configuration.

    But, an "ecobee:" entry in configuration.yaml will trigger an import flow
    if a config entry doesn't already exist. If ecobee.conf exists, the import
    flow will attempt to import it and create a config entry, to assist users
    migrating from the old ecobee integration. Otherwise, the user will have to
    continue setting up the integration via the config flow.
    """
    opp.data[DATA_ECOBEE_CONFIG] = config.get(DOMAIN, {})

    if not opp.config_entries.async_entries(DOMAIN) and opp.data[DATA_ECOBEE_CONFIG]:
        # No config entry exists and configuration.yaml config exists, trigger the import flow.
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}
            )
        )

    return True


async def async_setup_entry(opp, entry):
    """Set up ecobee via a config entry."""
    api_key = entry.data[CONF_API_KEY]
    refresh_token = entry.data[CONF_REFRESH_TOKEN]

    data = EcobeeData(opp, entry, api_key=api_key, refresh_token=refresh_token)

    if not await data.refresh():
        return False

    await data.update()

    if data.ecobee.thermostats is None:
        _LOGGER.error("No ecobee devices found to set up")
        return False

    opp.data[DOMAIN] = data

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


class EcobeeData:
    """
    Handle getting the latest data from ecobee.com so platforms can use it.

    Also handle refreshing tokens and updating config entry with refreshed tokens.
    """

    def __init__(self, opp, entry, api_key, refresh_token):
        """Initialize the Ecobee data object."""
        self._opp = opp
        self._entry = entry
        self.ecobee = Ecobee(
            config={ECOBEE_API_KEY: api_key, ECOBEE_REFRESH_TOKEN: refresh_token}
        )

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def update(self):
        """Get the latest data from ecobee.com."""
        try:
            await self._opp.async_add_executor_job(self.ecobee.update)
            _LOGGER.debug("Updating ecobee")
        except ExpiredTokenError:
            _LOGGER.debug("Refreshing expired ecobee tokens")
            await self.refresh()

    async def refresh(self) -> bool:
        """Refresh ecobee tokens and update config entry."""
        _LOGGER.debug("Refreshing ecobee tokens and updating config entry")
        if await self._opp.async_add_executor_job(self.ecobee.refresh_tokens):
            self._opp.config_entries.async_update_entry(
                self._entry,
                data={
                    CONF_API_KEY: self.ecobee.config[ECOBEE_API_KEY],
                    CONF_REFRESH_TOKEN: self.ecobee.config[ECOBEE_REFRESH_TOKEN],
                },
            )
            return True
        _LOGGER.error("Error refreshing ecobee tokens")
        return False


async def async_unload_entry(opp, config_entry):
    """Unload the config entry and platforms."""
    opp.data.pop(DOMAIN)

    tasks = []
    for platform in PLATFORMS:
        tasks.append(
            opp.config_entries.async_forward_entry_unload(config_entry, platform)
        )

    return all(await asyncio.gather(*tasks))
