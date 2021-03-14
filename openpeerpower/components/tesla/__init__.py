"""Support for Tesla cars."""
import asyncio
from collections import defaultdict
from datetime import timedelta
import logging

import async_timeout
from teslajsonpy import Controller as TeslaAPI
from teslajsonpy.exceptions import IncompleteCredentials, TeslaException
import voluptuous as vol

from openpeerpower.config_entries import SOURCE_IMPORT, ConfigEntry
from openpeerpower.const import (
    ATTR_BATTERY_CHARGING,
    ATTR_BATTERY_LEVEL,
    CONF_ACCESS_TOKEN,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_TOKEN,
    CONF_USERNAME,
    HTTP_UNAUTHORIZED,
)
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import aiohttp_client, config_validation as cv
from openpeerpower.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from openpeerpower.util import slugify

from .config_flow import CannotConnect, InvalidAuth, validate_input
from .const import (
    CONF_WAKE_ON_START,
    DATA_LISTENER,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_WAKE_ON_START,
    DOMAIN,
    ICONS,
    MIN_SCAN_INTERVAL,
    PLATFORMS,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(cv.positive_int, vol.Clamp(min=MIN_SCAN_INTERVAL)),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


@callback
def _async_save_tokens(opp, config_entry, access_token, refresh_token):
    opp.config_entries.async_update_entry(
        config_entry,
        data={
            **config_entry.data,
            CONF_ACCESS_TOKEN: access_token,
            CONF_TOKEN: refresh_token,
        },
    )


@callback
def _async_configured_emails(opp):
    """Return a set of configured Tesla emails."""
    return {
        entry.data[CONF_USERNAME]
        for entry in opp.config_entries.async_entries(DOMAIN)
        if CONF_USERNAME in entry.data
    }


async def async_setup(opp, base_config):
    """Set up of Tesla component."""

    def _update_entry(email, data=None, options=None):
        data = data or {}
        options = options or {
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
            CONF_WAKE_ON_START: DEFAULT_WAKE_ON_START,
        }
        for entry in opp.config_entries.async_entries(DOMAIN):
            if email != entry.title:
                continue
            opp.config_entries.async_update_entry(entry, data=data, options=options)

    config = base_config.get(DOMAIN)
    if not config:
        return True
    email = config[CONF_USERNAME]
    password = config[CONF_PASSWORD]
    scan_interval = config[CONF_SCAN_INTERVAL]
    if email in _async_configured_emails(opp):
        try:
            info = await validate_input(opp, config)
        except (CannotConnect, InvalidAuth):
            return False
        _update_entry(
            email,
            data={
                CONF_USERNAME: email,
                CONF_PASSWORD: password,
                CONF_ACCESS_TOKEN: info[CONF_ACCESS_TOKEN],
                CONF_TOKEN: info[CONF_TOKEN],
            },
            options={CONF_SCAN_INTERVAL: scan_interval},
        )
    else:
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data={CONF_USERNAME: email, CONF_PASSWORD: password},
            )
        )
        opp.data.setdefault(DOMAIN, {})
        opp.data[DOMAIN][email] = {CONF_SCAN_INTERVAL: scan_interval}
    return True


async def async_setup_entry(opp, config_entry):
    """Set up Tesla as config entry."""
    opp.data.setdefault(DOMAIN, {})
    config = config_entry.data
    websession = aiohttp_client.async_get_clientsession(opp)
    email = config_entry.title
    if email in opp.data[DOMAIN] and CONF_SCAN_INTERVAL in opp.data[DOMAIN][email]:
        scan_interval = opp.data[DOMAIN][email][CONF_SCAN_INTERVAL]
        opp.config_entries.async_update_entry(
            config_entry, options={CONF_SCAN_INTERVAL: scan_interval}
        )
        opp.data[DOMAIN].pop(email)
    try:
        controller = TeslaAPI(
            websession,
            email=config.get(CONF_USERNAME),
            password=config.get(CONF_PASSWORD),
            refresh_token=config[CONF_TOKEN],
            access_token=config[CONF_ACCESS_TOKEN],
            update_interval=config_entry.options.get(
                CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
            ),
        )
        (refresh_token, access_token) = await controller.connect(
            wake_if_asleep=config_entry.options.get(
                CONF_WAKE_ON_START, DEFAULT_WAKE_ON_START
            )
        )
    except IncompleteCredentials:
        _async_start_reauth(opp, config_entry)
        return False
    except TeslaException as ex:
        if ex.code == HTTP_UNAUTHORIZED:
            _async_start_reauth(opp, config_entry)
        _LOGGER.error("Unable to communicate with Tesla API: %s", ex.message)
        return False
    _async_save_tokens(opp, config_entry, access_token, refresh_token)
    coordinator = TeslaDataUpdateCoordinator(
        opp, config_entry=config_entry, controller=controller
    )
    # Fetch initial data so we have data when entities subscribe
    entry_data = opp.data[DOMAIN][config_entry.entry_id] = {
        "coordinator": coordinator,
        "devices": defaultdict(list),
        DATA_LISTENER: [config_entry.add_update_listener(update_listener)],
    }
    _LOGGER.debug("Connected to the Tesla API")

    await coordinator.async_refresh()
    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    all_devices = controller.get_homeassistant_components()

    if not all_devices:
        return False

    for device in all_devices:
        entry_data["devices"][device.opp_type].append(device)

    for platform in PLATFORMS:
        _LOGGER.debug("Loading %s", platform)
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(config_entry, platform)
        )
    return True


async def async_unload_entry(opp, config_entry) -> bool:
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(config_entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    for listener in opp.data[DOMAIN][config_entry.entry_id][DATA_LISTENER]:
        listener()
    username = config_entry.title
    if unload_ok:
        opp.data[DOMAIN].pop(config_entry.entry_id)
        _LOGGER.debug("Unloaded entry for %s", username)
        return True
    return False


def _async_start_reauth(opp: OpenPeerPower, entry: ConfigEntry):
    opp.async_create_task(
        opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "reauth"},
            data=entry.data,
        )
    )
    _LOGGER.error("Credentials are no longer valid. Please reauthenticate")


async def update_listener(opp, config_entry):
    """Update when config_entry options update."""
    controller = opp.data[DOMAIN][config_entry.entry_id]["coordinator"].controller
    old_update_interval = controller.update_interval
    controller.update_interval = config_entry.options.get(CONF_SCAN_INTERVAL)
    if old_update_interval != controller.update_interval:
        _LOGGER.debug(
            "Changing scan_interval from %s to %s",
            old_update_interval,
            controller.update_interval,
        )


class TeslaDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Tesla data."""

    def __init__(self, opp, *, config_entry, controller):
        """Initialize global Tesla data updater."""
        self.controller = controller
        self.config_entry = config_entry

        update_interval = timedelta(seconds=MIN_SCAN_INTERVAL)

        super().__init__(
            opp,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        if self.controller.is_token_refreshed():
            (refresh_token, access_token) = self.controller.get_tokens()
            _async_save_tokens(self.opp, self.config_entry, access_token, refresh_token)
            _LOGGER.debug("Saving new tokens in config_entry")

        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(30):
                return await self.controller.update()
        except TeslaException as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err


class TeslaDevice(CoordinatorEntity):
    """Representation of a Tesla device."""

    def __init__(self, tesla_device, coordinator):
        """Initialise the Tesla device."""
        super().__init__(coordinator)
        self.tesla_device = tesla_device
        self._name = self.tesla_device.name
        self._unique_id = slugify(self.tesla_device.uniq_name)
        self._attributes = self.tesla_device.attrs.copy()

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id

    @property
    def icon(self):
        """Return the icon of the sensor."""
        if self.device_class:
            return None

        return ICONS.get(self.tesla_device.type)

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        attr = self._attributes
        if self.tesla_device.has_battery():
            attr[ATTR_BATTERY_LEVEL] = self.tesla_device.battery_level()
            attr[ATTR_BATTERY_CHARGING] = self.tesla_device.battery_charging()
        return attr

    @property
    def device_info(self):
        """Return the device_info of the device."""
        return {
            "identifiers": {(DOMAIN, self.tesla_device.id())},
            "name": self.tesla_device.car_name(),
            "manufacturer": "Tesla",
            "model": self.tesla_device.car_type,
            "sw_version": self.tesla_device.car_version,
        }

    async def async_added_to_opp(self):
        """Register state update callback."""
        self.async_on_remove(self.coordinator.async_add_listener(self.refresh))

    @callback
    def refresh(self) -> None:
        """Refresh the state of the device.

        This assumes the coordinator has updated the controller.
        """
        self.tesla_device.refresh()
        self._attributes = self.tesla_device.attrs.copy()
        self.async_write_op_state()
