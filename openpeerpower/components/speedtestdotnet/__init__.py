"""Support for testing internet speed via Speedtest.net."""
from datetime import timedelta
import logging

import speedtest
import voluptuous as vol

from openpeerpower.config_entries import SOURCE_IMPORT
from openpeerpower.const import (
    CONF_MONITORED_CONDITIONS,
    CONF_SCAN_INTERVAL,
    EVENT_OPENPEERPOWER_STARTED,
)
from openpeerpower.core import CoreState, callback
from openpeerpower.exceptions import ConfigEntryNotReady
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_MANUAL,
    CONF_SERVER_ID,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SERVER,
    DOMAIN,
    SENSOR_TYPES,
    SPEED_TEST_SERVICE,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_SERVER_ID): cv.positive_int,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=timedelta(minutes=DEFAULT_SCAN_INTERVAL)
                ): cv.positive_time_period,
                vol.Optional(CONF_MANUAL, default=False): cv.boolean,
                vol.Optional(
                    CONF_MONITORED_CONDITIONS, default=list(SENSOR_TYPES)
                ): vol.All(cv.ensure_list, [vol.In(list(SENSOR_TYPES))]),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def server_id_valid(server_id):
    """Check if server_id is valid."""
    try:
        api = speedtest.Speedtest()
        api.get_servers([int(server_id)])
    except (speedtest.ConfigRetrievalError, speedtest.NoMatchedServers):
        return False

    return True


async def async_setup(opp, config):
    """Import integration from config."""
    if DOMAIN in config:
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=config[DOMAIN]
            )
        )
    return True


async def async_setup_entry(opp, config_entry):
    """Set up the Speedtest.net component."""
    coordinator = SpeedTestDataCoordinator(opp, config_entry)
    await coordinator.async_setup()

    async def _enable_scheduled_speedtests(*_):
        """Activate the data update coordinator."""
        coordinator.update_interval = timedelta(
            minutes=config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
        await coordinator.async_refresh()

    if not config_entry.options[CONF_MANUAL]:
        if opp.state == CoreState.running:
            await _enable_scheduled_speedtests()
            if not coordinator.last_update_success:
                raise ConfigEntryNotReady
        else:
            # Running a speed test during startup can prevent
            # integrations from being able to setup because it
            # can saturate the network interface.
            opp.bus.async_listen_once(
                EVENT_OPENPEERPOWER_STARTED, _enable_scheduled_speedtests
            )

    opp.data[DOMAIN] = coordinator

    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(config_entry, "sensor")
    )

    return True


async def async_unload_entry(opp, config_entry):
    """Unload SpeedTest Entry from config_entry."""
    opp.services.async_remove(DOMAIN, SPEED_TEST_SERVICE)

    opp.data[DOMAIN].async_unload()

    await opp.config_entries.async_forward_entry_unload(config_entry, "sensor")

    opp.data.pop(DOMAIN)

    return True


class SpeedTestDataCoordinator(DataUpdateCoordinator):
    """Get the latest data from speedtest.net."""

    def __init__(self, opp, config_entry):
        """Initialize the data object."""
        self.opp = opp
        self.config_entry = config_entry
        self.api = None
        self.servers = {}
        self._unsub_update_listener = None
        super().__init__(
            self.opp,
            _LOGGER,
            name=DOMAIN,
            update_method=self.async_update,
        )

    def update_servers(self):
        """Update list of test servers."""
        try:
            server_list = self.api.get_servers()
        except speedtest.ConfigRetrievalError:
            _LOGGER.debug("Error retrieving server list")
            return

        self.servers[DEFAULT_SERVER] = {}
        for server in sorted(
            server_list.values(),
            key=lambda server: server[0]["country"] + server[0]["sponsor"],
        ):
            self.servers[
                f"{server[0]['country']} - {server[0]['sponsor']} - {server[0]['name']}"
            ] = server[0]

    def update_data(self):
        """Get the latest data from speedtest.net."""
        self.update_servers()

        self.api.closest.clear()
        if self.config_entry.options.get(CONF_SERVER_ID):
            server_id = self.config_entry.options.get(CONF_SERVER_ID)
            self.api.get_servers(servers=[server_id])

        self.api.get_best_server()
        _LOGGER.debug(
            "Executing speedtest.net speed test with server_id: %s", self.api.best["id"]
        )

        self.api.download()
        self.api.upload()
        return self.api.results.dict()

    async def async_update(self, *_):
        """Update Speedtest data."""
        try:
            return await self.opp.async_add_executor_job(self.update_data)
        except (speedtest.ConfigRetrievalError, speedtest.NoMatchedServers) as err:
            raise UpdateFailed from err

    async def async_set_options(self):
        """Set options for entry."""
        if not self.config_entry.options:
            data = {**self.config_entry.data}
            options = {
                CONF_SCAN_INTERVAL: data.pop(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                CONF_MANUAL: data.pop(CONF_MANUAL, False),
                CONF_SERVER_ID: str(data.pop(CONF_SERVER_ID, "")),
            }
            self.opp.config_entries.async_update_entry(
                self.config_entry, data=data, options=options
            )

    async def async_setup(self):
        """Set up SpeedTest."""
        try:
            self.api = await self.opp.async_add_executor_job(speedtest.Speedtest)
        except speedtest.ConfigRetrievalError as err:
            raise ConfigEntryNotReady from err

        async def request_update(call):
            """Request update."""
            await self.async_request_refresh()

        await self.async_set_options()

        await self.opp.async_add_executor_job(self.update_servers)

        self.opp.services.async_register(DOMAIN, SPEED_TEST_SERVICE, request_update)

        self._unsub_update_listener = self.config_entry.add_update_listener(
            options_updated_listener
        )

    @callback
    def async_unload(self):
        """Unload the coordinator."""
        if not self._unsub_update_listener:
            return
        self._unsub_update_listener()
        self._unsub_update_listener = None


async def options_updated_listener(opp, entry):
    """Handle options update."""
    if entry.options[CONF_MANUAL]:
        opp.data[DOMAIN].update_interval = None
        return

    opp.data[DOMAIN].update_interval = timedelta(
        minutes=entry.options[CONF_SCAN_INTERVAL]
    )
    await opp.data[DOMAIN].async_request_refresh()
