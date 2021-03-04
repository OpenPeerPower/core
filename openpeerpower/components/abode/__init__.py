"""Support for the Abode Security System."""
from asyncio import gather
from copy import deepcopy
from functools import partial

from abodepy import Abode
from abodepy.exceptions import AbodeAuthenticationException, AbodeException
import abodepy.helpers.timeline as TIMELINE
from requests.exceptions import ConnectTimeout, HTTPError
import voluptuous as vol

from openpeerpower.config_entries import SOURCE_IMPORT, SOURCE_REAUTH
from openpeerpower.const import (
    ATTR_ATTRIBUTION,
    ATTR_DATE,
    ATTR_DEVICE_ID,
    ATTR_ENTITY_ID,
    ATTR_TIME,
    CONF_PASSWORD,
    CONF_USERNAME,
    EVENT_OPENPEERPOWER_STOP,
)
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.dispatcher import dispatcher_send
from openpeerpower.helpers.entity import Entity

from .const import ATTRIBUTION, DEFAULT_CACHEDB, DOMAIN, LOGGER

CONF_POLLING = "polling"

SERVICE_SETTINGS = "change_setting"
SERVICE_CAPTURE_IMAGE = "capture_image"
SERVICE_TRIGGER_AUTOMATION = "trigger_automation"

ATTR_DEVICE_NAME = "device_name"
ATTR_DEVICE_TYPE = "device_type"
ATTR_EVENT_CODE = "event_code"
ATTR_EVENT_NAME = "event_name"
ATTR_EVENT_TYPE = "event_type"
ATTR_EVENT_UTC = "event_utc"
ATTR_SETTING = "setting"
ATTR_USER_NAME = "user_name"
ATTR_APP_TYPE = "app_type"
ATTR_EVENT_BY = "event_by"
ATTR_VALUE = "value"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(CONF_POLLING, default=False): cv.boolean,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

CHANGE_SETTING_SCHEMA = vol.Schema(
    {vol.Required(ATTR_SETTING): cv.string, vol.Required(ATTR_VALUE): cv.string}
)

CAPTURE_IMAGE_SCHEMA = vol.Schema({ATTR_ENTITY_ID: cv.entity_ids})

AUTOMATION_SCHEMA = vol.Schema({ATTR_ENTITY_ID: cv.entity_ids})

PLATFORMS = [
    "alarm_control_panel",
    "binary_sensor",
    "lock",
    "switch",
    "cover",
    "camera",
    "light",
    "sensor",
]


class AbodeSystem:
    """Abode System class."""

    def __init__(self, abode, polling):
        """Initialize the system."""
        self.abode = abode
        self.polling = polling
        self.entity_ids = set()
        self.logout_listener = None


async def async_setup(opp, config):
    """Set up Abode integration."""
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]

    opp.async_create_task(
        opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=deepcopy(conf)
        )
    )

    return True


async def async_setup_entry(opp, config_entry):
    """Set up Abode integration from a config entry."""
    username = config_entry.data.get(CONF_USERNAME)
    password = config_entry.data.get(CONF_PASSWORD)
    polling = config_entry.data.get(CONF_POLLING)
    cache = opp.config.path(DEFAULT_CACHEDB)

    # For previous config entries where unique_id is None
    if config_entry.unique_id is None:
        opp.config_entries.async_update_entry(
            config_entry, unique_id=config_entry.data[CONF_USERNAME]
        )

    try:
        abode = await opp.async_add_executor_job(
            Abode, username, password, True, True, True, cache
        )

    except AbodeAuthenticationException as ex:
        LOGGER.error("Invalid credentials: %s", ex)
        await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_REAUTH},
            data=config_entry.data,
        )
        return False

    except (AbodeException, ConnectTimeout, HTTPError) as ex:
        LOGGER.error("Unable to connect to Abode: %s", ex)
        raise ConfigEntryNotReady from ex

    opp.data[DOMAIN] = AbodeSystem(abode, polling)

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    await setup_opp_events(opp)
    await opp.async_add_executor_job(setup_opp_services, opp)
    await opp.async_add_executor_job(setup_abode_events, opp)

    return True


async def async_unload_entry(opp, config_entry):
    """Unload a config entry."""
    opp.services.async_remove(DOMAIN, SERVICE_SETTINGS)
    opp.services.async_remove(DOMAIN, SERVICE_CAPTURE_IMAGE)
    opp.services.async_remove(DOMAIN, SERVICE_TRIGGER_AUTOMATION)

    tasks = []

    for platform in PLATFORMS:
        tasks.append(
            opp.config_entries.async_forward_entry_unload(config_entry, platform)
        )

    await gather(*tasks)

    await opp.async_add_executor_job(opp.data[DOMAIN].abode.events.stop)
    await opp.async_add_executor_job(opp.data[DOMAIN].abode.logout)

    opp.data[DOMAIN].logout_listener()
    opp.data.pop(DOMAIN)

    return True


def setup_opp_services(opp):
    """Open Peer Power services."""

    def change_setting(call):
        """Change an Abode system setting."""
        setting = call.data.get(ATTR_SETTING)
        value = call.data.get(ATTR_VALUE)

        try:
            opp.data[DOMAIN].abode.set_setting(setting, value)
        except AbodeException as ex:
            LOGGER.warning(ex)

    def capture_image(call):
        """Capture a new image."""
        entity_ids = call.data.get(ATTR_ENTITY_ID)

        target_entities = [
            entity_id
            for entity_id in opp.data[DOMAIN].entity_ids
            if entity_id in entity_ids
        ]

        for entity_id in target_entities:
            signal = f"abode_camera_capture_{entity_id}"
            dispatcher_send(opp, signal)

    def trigger_automation(call):
        """Trigger an Abode automation."""
        entity_ids = call.data.get(ATTR_ENTITY_ID)

        target_entities = [
            entity_id
            for entity_id in opp.data[DOMAIN].entity_ids
            if entity_id in entity_ids
        ]

        for entity_id in target_entities:
            signal = f"abode_trigger_automation_{entity_id}"
            dispatcher_send(opp, signal)

    opp.services.register(
        DOMAIN, SERVICE_SETTINGS, change_setting, schema=CHANGE_SETTING_SCHEMA
    )

    opp.services.register(
        DOMAIN, SERVICE_CAPTURE_IMAGE, capture_image, schema=CAPTURE_IMAGE_SCHEMA
    )

    opp.services.register(
        DOMAIN, SERVICE_TRIGGER_AUTOMATION, trigger_automation, schema=AUTOMATION_SCHEMA
    )


async def setup_opp_events(opp):
    """Open Peer Power start and stop callbacks."""

    def logout(event):
        """Logout of Abode."""
        if not opp.data[DOMAIN].polling:
            opp.data[DOMAIN].abode.events.stop()

        opp.data[DOMAIN].abode.logout()
        LOGGER.info("Logged out of Abode")

    if not opp.data[DOMAIN].polling:
        await opp.async_add_executor_job(opp.data[DOMAIN].abode.events.start)

    opp.data[DOMAIN].logout_listener = opp.bus.async_listen_once(
        EVENT_OPENPEERPOWER_STOP, logout
    )


def setup_abode_events(opp):
    """Event callbacks."""

    def event_callback(event, event_json):
        """Handle an event callback from Abode."""
        data = {
            ATTR_DEVICE_ID: event_json.get(ATTR_DEVICE_ID, ""),
            ATTR_DEVICE_NAME: event_json.get(ATTR_DEVICE_NAME, ""),
            ATTR_DEVICE_TYPE: event_json.get(ATTR_DEVICE_TYPE, ""),
            ATTR_EVENT_CODE: event_json.get(ATTR_EVENT_CODE, ""),
            ATTR_EVENT_NAME: event_json.get(ATTR_EVENT_NAME, ""),
            ATTR_EVENT_TYPE: event_json.get(ATTR_EVENT_TYPE, ""),
            ATTR_EVENT_UTC: event_json.get(ATTR_EVENT_UTC, ""),
            ATTR_USER_NAME: event_json.get(ATTR_USER_NAME, ""),
            ATTR_APP_TYPE: event_json.get(ATTR_APP_TYPE, ""),
            ATTR_EVENT_BY: event_json.get(ATTR_EVENT_BY, ""),
            ATTR_DATE: event_json.get(ATTR_DATE, ""),
            ATTR_TIME: event_json.get(ATTR_TIME, ""),
        }

        opp.bus.fire(event, data)

    events = [
        TIMELINE.ALARM_GROUP,
        TIMELINE.ALARM_END_GROUP,
        TIMELINE.PANEL_FAULT_GROUP,
        TIMELINE.PANEL_RESTORE_GROUP,
        TIMELINE.AUTOMATION_GROUP,
        TIMELINE.DISARM_GROUP,
        TIMELINE.ARM_GROUP,
        TIMELINE.ARM_FAULT_GROUP,
        TIMELINE.TEST_GROUP,
        TIMELINE.CAPTURE_GROUP,
        TIMELINE.DEVICE_GROUP,
    ]

    for event in events:
        opp.data[DOMAIN].abode.events.add_event_callback(
            event, partial(event_callback, event)
        )


class AbodeEntity(Entity):
    """Representation of an Abode entity."""

    def __init__(self, data):
        """Initialize Abode entity."""
        self._data = data
        self._available = True

    @property
    def available(self):
        """Return the available state."""
        return self._available

    @property
    def should_poll(self):
        """Return the polling state."""
        return self._data.polling

    async def async_added_to_opp(self):
        """Subscribe to Abode connection status updates."""
        await self.opp.async_add_executor_job(
            self._data.abode.events.add_connection_status_callback,
            self.unique_id,
            self._update_connection_status,
        )

        self.opp.data[DOMAIN].entity_ids.add(self.entity_id)

    async def async_will_remove_from_opp(self):
        """Unsubscribe from Abode connection status updates."""
        await self.opp.async_add_executor_job(
            self._data.abode.events.remove_connection_status_callback, self.unique_id
        )

    def _update_connection_status(self):
        """Update the entity available property."""
        self._available = self._data.abode.events.connected
        self.schedule_update_op_state()


class AbodeDevice(AbodeEntity):
    """Representation of an Abode device."""

    def __init__(self, data, device):
        """Initialize Abode device."""
        super().__init__(data)
        self._device = device

    async def async_added_to_opp(self):
        """Subscribe to device events."""
        await super().async_added_to_opp()
        await self.opp.async_add_executor_job(
            self._data.abode.events.add_device_callback,
            self._device.device_id,
            self._update_callback,
        )

    async def async_will_remove_from_opp(self):
        """Unsubscribe from device events."""
        await super().async_will_remove_from_opp()
        await self.opp.async_add_executor_job(
            self._data.abode.events.remove_all_device_callbacks, self._device.device_id
        )

    def update(self):
        """Update device state."""
        self._device.refresh()

    @property
    def name(self):
        """Return the name of the device."""
        return self._device.name

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            "device_id": self._device.device_id,
            "battery_low": self._device.battery_low,
            "no_response": self._device.no_response,
            "device_type": self._device.type,
        }

    @property
    def unique_id(self):
        """Return a unique ID to use for this device."""
        return self._device.device_uuid

    @property
    def device_info(self):
        """Return device registry information for this entity."""
        return {
            "identifiers": {(DOMAIN, self._device.device_id)},
            "manufacturer": "Abode",
            "name": self._device.name,
            "device_type": self._device.type,
        }

    def _update_callback(self, device):
        """Update the device state."""
        self.schedule_update_op_state()


class AbodeAutomation(AbodeEntity):
    """Representation of an Abode automation."""

    def __init__(self, data, automation):
        """Initialize for Abode automation."""
        super().__init__(data)
        self._automation = automation

    def update(self):
        """Update automation state."""
        self._automation.refresh()

    @property
    def name(self):
        """Return the name of the automation."""
        return self._automation.name

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {ATTR_ATTRIBUTION: ATTRIBUTION, "type": "CUE automation"}

    @property
    def unique_id(self):
        """Return a unique ID to use for this automation."""
        return self._automation.automation_id
