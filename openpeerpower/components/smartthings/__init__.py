"""Support for SmartThings Cloud."""
import asyncio
import importlib
import logging
from typing import Iterable

from aiohttp.client_exceptions import ClientConnectionError, ClientResponseError
from pysmartapp.event import EVENT_TYPE_DEVICE
from pysmartthings import Attribute, Capability, SmartThings

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import (
    CONF_ACCESS_TOKEN,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    HTTP_FORBIDDEN,
    HTTP_UNAUTHORIZED,
)
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from openpeerpower.helpers.entity import Entity
from openpeerpower.helpers.event import async_track_time_interval
from openpeerpower.helpers.typing import ConfigType, OpenPeerPowerType

from .config_flow import SmartThingsFlowHandler  # noqa: F401
from .const import (
    CONF_APP_ID,
    CONF_INSTALLED_APP_ID,
    CONF_LOCATION_ID,
    CONF_REFRESH_TOKEN,
    DATA_BROKERS,
    DATA_MANAGER,
    DOMAIN,
    EVENT_BUTTON,
    SIGNAL_SMARTTHINGS_UPDATE,
    SUPPORTED_PLATFORMS,
    TOKEN_REFRESH_INTERVAL,
)
from .smartapp import (
    format_unique_id,
    setup_smartapp,
    setup_smartapp_endpoint,
    smartapp_sync_subscriptions,
    unload_smartapp_endpoint,
    validate_installed_app,
    validate_webhook_requirements,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_opp: OpenPeerPowerType, config: ConfigType):
    """Initialize the SmartThings platform."""
    await setup_smartapp_endpoint.opp)
    return True


async def async_migrate_entry.opp: OpenPeerPowerType, entry: ConfigEntry):
    """Handle migration of a previous version config entry.

    A config entry created under a previous version must go through the
    integration setup again so we can properly retrieve the needed data
    elements. Force this by removing the entry and triggering a new flow.
    """
    # Remove the entry which will invoke the callback to delete the app.
   .opp.async_create_task.opp.config_entries.async_remove(entry.entry_id))
    # only create new flow if there isn't a pending one for SmartThings.
    flows = opp.config_entries.flow.async_progress()
    if not [flow for flow in flows if flow["handler"] == DOMAIN]:
       .opp.async_create_task(
           .opp.config_entries.flow.async_init(DOMAIN, context={"source": "import"})
        )

    # Return False because it could not be migrated.
    return False


async def async_setup_entry.opp: OpenPeerPowerType, entry: ConfigEntry):
    """Initialize config entry which represents an installed SmartApp."""
    # For backwards compat
    if entry.unique_id is None:
       .opp.config_entries.async_update_entry(
            entry,
            unique_id=format_unique_id(
                entry.data[CONF_APP_ID], entry.data[CONF_LOCATION_ID]
            ),
        )

    if not validate_webhook_requirements.opp):
        _LOGGER.warning(
            "The 'base_url' of the 'http' integration must be configured and start with 'https://'"
        )
        return False

    api = SmartThings(async_get_clientsession.opp), entry.data[CONF_ACCESS_TOKEN])

    remove_entry = False
    try:
        # See if the app is already setup. This occurs when there are
        # installs in multiple SmartThings locations (valid use-case)
        manager = opp.data[DOMAIN][DATA_MANAGER]
        smart_app = manager.smartapps.get(entry.data[CONF_APP_ID])
        if not smart_app:
            # Validate and setup the app.
            app = await api.app(entry.data[CONF_APP_ID])
            smart_app = setup_smartapp.opp, app)

        # Validate and retrieve the installed app.
        installed_app = await validate_installed_app(
            api, entry.data[CONF_INSTALLED_APP_ID]
        )

        # Get scenes
        scenes = await async_get_entry_scenes(entry, api)

        # Get SmartApp token to sync subscriptions
        token = await api.generate_tokens(
            entry.data[CONF_CLIENT_ID],
            entry.data[CONF_CLIENT_SECRET],
            entry.data[CONF_REFRESH_TOKEN],
        )
       .opp.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_REFRESH_TOKEN: token.refresh_token}
        )

        # Get devices and their current status
        devices = await api.devices(location_ids=[installed_app.location_id])

        async def retrieve_device_status(device):
            try:
                await device.status.refresh()
            except ClientResponseError:
                _LOGGER.debug(
                    "Unable to update status for device: %s (%s), the device will be excluded",
                    device.label,
                    device.device_id,
                    exc_info=True,
                )
                devices.remove(device)

        await asyncio.gather(*(retrieve_device_status(d) for d in devices.copy()))

        # Sync device subscriptions
        await smartapp_sync_subscriptions(
           .opp,
            token.access_token,
            installed_app.location_id,
            installed_app.installed_app_id,
            devices,
        )

        # Setup device broker
        broker = DeviceBroker.opp, entry, token, smart_app, devices, scenes)
        broker.connect()
       .opp.data[DOMAIN][DATA_BROKERS][entry.entry_id] = broker

    except ClientResponseError as ex:
        if ex.status in (HTTP_UNAUTHORIZED, HTTP_FORBIDDEN):
            _LOGGER.exception(
                "Unable to setup configuration entry '%s' - please reconfigure the integration",
                entry.title,
            )
            remove_entry = True
        else:
            _LOGGER.debug(ex, exc_info=True)
            raise ConfigEntryNotReady from ex
    except (ClientConnectionError, RuntimeWarning) as ex:
        _LOGGER.debug(ex, exc_info=True)
        raise ConfigEntryNotReady from ex

    if remove_entry:
       .opp.async_create_task.opp.config_entries.async_remove(entry.entry_id))
        # only create new flow if there isn't a pending one for SmartThings.
        flows = opp.config_entries.flow.async_progress()
        if not [flow for flow in flows if flow["handler"] == DOMAIN]:
           .opp.async_create_task(
               .opp.config_entries.flow.async_init(
                    DOMAIN, context={"source": "import"}
                )
            )
        return False

    for component in SUPPORTED_PLATFORMS:
       .opp.async_create_task(
           .opp.config_entries.async_forward_entry_setup(entry, component)
        )
    return True


async def async_get_entry_scenes(entry: ConfigEntry, api):
    """Get the scenes within an integration."""
    try:
        return await api.scenes(location_id=entry.data[CONF_LOCATION_ID])
    except ClientResponseError as ex:
        if ex.status == HTTP_FORBIDDEN:
            _LOGGER.exception(
                "Unable to load scenes for configuration entry '%s' because the access token does not have the required access",
                entry.title,
            )
        else:
            raise
    return []


async def async_unload_entry.opp: OpenPeerPowerType, entry: ConfigEntry):
    """Unload a config entry."""
    broker = opp.data[DOMAIN][DATA_BROKERS].pop(entry.entry_id, None)
    if broker:
        broker.disconnect()

    tasks = [
       .opp.config_entries.async_forward_entry_unload(entry, component)
        for component in SUPPORTED_PLATFORMS
    ]
    return all(await asyncio.gather(*tasks))


async def async_remove_entry.opp: OpenPeerPowerType, entry: ConfigEntry) -> None:
    """Perform clean-up when entry is being removed."""
    api = SmartThings(async_get_clientsession.opp), entry.data[CONF_ACCESS_TOKEN])

    # Remove the installed_app, which if already removed raises a HTTP_FORBIDDEN error.
    installed_app_id = entry.data[CONF_INSTALLED_APP_ID]
    try:
        await api.delete_installed_app(installed_app_id)
    except ClientResponseError as ex:
        if ex.status == HTTP_FORBIDDEN:
            _LOGGER.debug(
                "Installed app %s has already been removed",
                installed_app_id,
                exc_info=True,
            )
        else:
            raise
    _LOGGER.debug("Removed installed app %s", installed_app_id)

    # Remove the app if not referenced by other entries, which if already
    # removed raises a HTTP_FORBIDDEN error.
    all_entries = opp.config_entries.async_entries(DOMAIN)
    app_id = entry.data[CONF_APP_ID]
    app_count = sum(1 for entry in all_entries if entry.data[CONF_APP_ID] == app_id)
    if app_count > 1:
        _LOGGER.debug(
            "App %s was not removed because it is in use by other configuration entries",
            app_id,
        )
        return
    # Remove the app
    try:
        await api.delete_app(app_id)
    except ClientResponseError as ex:
        if ex.status == HTTP_FORBIDDEN:
            _LOGGER.debug("App %s has already been removed", app_id, exc_info=True)
        else:
            raise
    _LOGGER.debug("Removed app %s", app_id)

    if len(all_entries) == 1:
        await unload_smartapp_endpoint.opp)


class DeviceBroker:
    """Manages an individual SmartThings config entry."""

    def __init__(
        self,
        opp: OpenPeerPowerType,
        entry: ConfigEntry,
        token,
        smart_app,
        devices: Iterable,
        scenes: Iterable,
    ):
        """Create a new instance of the DeviceBroker."""
        self.opp = opp
        self._entry = entry
        self._installed_app_id = entry.data[CONF_INSTALLED_APP_ID]
        self._smart_app = smart_app
        self._token = token
        self._event_disconnect = None
        self._regenerate_token_remove = None
        self._assignments = self._assign_capabilities(devices)
        self.devices = {device.device_id: device for device in devices}
        self.scenes = {scene.scene_id: scene for scene in scenes}

    def _assign_capabilities(self, devices: Iterable):
        """Assign platforms to capabilities."""
        assignments = {}
        for device in devices:
            capabilities = device.capabilities.copy()
            slots = {}
            for platform_name in SUPPORTED_PLATFORMS:
                platform = importlib.import_module(f".{platform_name}", self.__module__)
                if not hasattr(platform, "get_capabilities"):
                    continue
                assigned = platform.get_capabilities(capabilities)
                if not assigned:
                    continue
                # Draw-down capabilities and set slot assignment
                for capability in assigned:
                    if capability not in capabilities:
                        continue
                    capabilities.remove(capability)
                    slots[capability] = platform_name
            assignments[device.device_id] = slots
        return assignments

    def connect(self):
        """Connect handlers/listeners for device/lifecycle events."""
        # Setup interval to regenerate the refresh token on a periodic basis.
        # Tokens expire in 30 days and once expired, cannot be recovered.
        async def regenerate_refresh_token(now):
            """Generate a new refresh token and update the config entry."""
            await self._token.refresh(
                self._entry.data[CONF_CLIENT_ID],
                self._entry.data[CONF_CLIENT_SECRET],
            )
            self.opp.config_entries.async_update_entry(
                self._entry,
                data={
                    **self._entry.data,
                    CONF_REFRESH_TOKEN: self._token.refresh_token,
                },
            )
            _LOGGER.debug(
                "Regenerated refresh token for installed app: %s",
                self._installed_app_id,
            )

        self._regenerate_token_remove = async_track_time_interval(
            self.opp, regenerate_refresh_token, TOKEN_REFRESH_INTERVAL
        )

        # Connect handler to incoming device events
        self._event_disconnect = self._smart_app.connect_event(self._event_handler)

    def disconnect(self):
        """Disconnects handlers/listeners for device/lifecycle events."""
        if self._regenerate_token_remove:
            self._regenerate_token_remove()
        if self._event_disconnect:
            self._event_disconnect()

    def get_assigned(self, device_id: str, platform: str):
        """Get the capabilities assigned to the platform."""
        slots = self._assignments.get(device_id, {})
        return [key for key, value in slots.items() if value == platform]

    def any_assigned(self, device_id: str, platform: str):
        """Return True if the platform has any assigned capabilities."""
        slots = self._assignments.get(device_id, {})
        return any(value for value in slots.values() if value == platform)

    async def _event_handler(self, req, resp, app):
        """Broker for incoming events."""
        # Do not process events received from a different installed app
        # under the same parent SmartApp (valid use-scenario)
        if req.installed_app_id != self._installed_app_id:
            return

        updated_devices = set()
        for evt in req.events:
            if evt.event_type != EVENT_TYPE_DEVICE:
                continue
            device = self.devices.get(evt.device_id)
            if not device:
                continue
            device.status.apply_attribute_update(
                evt.component_id,
                evt.capability,
                evt.attribute,
                evt.value,
                data=evt.data,
            )

            # Fire events for buttons
            if (
                evt.capability == Capability.button
                and evt.attribute == Attribute.button
            ):
                data = {
                    "component_id": evt.component_id,
                    "device_id": evt.device_id,
                    "location_id": evt.location_id,
                    "value": evt.value,
                    "name": device.label,
                    "data": evt.data,
                }
                self.opp.bus.async_fire(EVENT_BUTTON, data)
                _LOGGER.debug("Fired button event: %s", data)
            else:
                data = {
                    "location_id": evt.location_id,
                    "device_id": evt.device_id,
                    "component_id": evt.component_id,
                    "capability": evt.capability,
                    "attribute": evt.attribute,
                    "value": evt.value,
                    "data": evt.data,
                }
                _LOGGER.debug("Push update received: %s", data)

            updated_devices.add(device.device_id)

        async_dispatcher_send(self.opp, SIGNAL_SMARTTHINGS_UPDATE, updated_devices)


class SmartThingsEntity(Entity):
    """Defines a SmartThings entity."""

    def __init__(self, device):
        """Initialize the instance."""
        self._device = device
        self._dispatcher_remove = None

    async def async_added_to.opp(self):
        """Device added to.opp."""

        async def async_update_state(devices):
            """Update device state."""
            if self._device.device_id in devices:
                await self.async_update_ha_state(True)

        self._dispatcher_remove = async_dispatcher_connect(
            self.opp, SIGNAL_SMARTTHINGS_UPDATE, async_update_state
        )

    async def async_will_remove_from.opp(self) -> None:
        """Disconnect the device when removed."""
        if self._dispatcher_remove:
            self._dispatcher_remove()

    @property
    def device_info(self):
        """Get attributes about the device."""
        return {
            "identifiers": {(DOMAIN, self._device.device_id)},
            "name": self._device.label,
            "model": self._device.device_type_name,
            "manufacturer": "Unavailable",
        }

    @property
    def name(self) -> str:
        """Return the name of the device."""
        return self._device.label

    @property
    def should_poll(self) -> bool:
        """No polling needed for this device."""
        return False

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._device.device_id
