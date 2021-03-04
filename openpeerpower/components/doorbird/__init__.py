"""Support for DoorBird devices."""
import asyncio
import logging
import urllib
from urllib.error import HTTPError

from aiohttp import web
from doorbirdpy import DoorBird
import voluptuous as vol

from openpeerpower.components.http import OpenPeerPowerView
from openpeerpower.config_entries import SOURCE_IMPORT, ConfigEntry
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    CONF_DEVICES,
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_TOKEN,
    CONF_USERNAME,
    HTTP_OK,
    HTTP_UNAUTHORIZED,
)
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.exceptions import ConfigEntryNotReady
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.network import get_url
from openpeerpower.util import dt as dt_util, slugify

from .const import (
    CONF_EVENTS,
    DOMAIN,
    DOOR_STATION,
    DOOR_STATION_EVENT_ENTITY_IDS,
    DOOR_STATION_INFO,
    PLATFORMS,
    UNDO_UPDATE_LISTENER,
)
from .util import get_doorstation_by_token

_LOGGER = logging.getLogger(__name__)

API_URL = f"/api/{DOMAIN}"

CONF_CUSTOM_URL = "opp_url_override"

RESET_DEVICE_FAVORITES = "doorbird_reset_favorites"

DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_TOKEN): cv.string,
        vol.Optional(CONF_EVENTS, default=[]): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_CUSTOM_URL): cv.string,
        vol.Optional(CONF_NAME): cv.string,
    }
)

CONFIG_SCHEMA = vol.Schema(
    vol.All(
        cv.deprecated(DOMAIN),
        {
            DOMAIN: vol.Schema(
                {vol.Required(CONF_DEVICES): vol.All(cv.ensure_list, [DEVICE_SCHEMA])}
            )
        },
    ),
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the DoorBird component."""
    opp.data.setdefault(DOMAIN, {})

    # Provide an endpoint for the doorstations to call to trigger events
    opp.http.register_view(DoorBirdRequestView)

    if DOMAIN in config and CONF_DEVICES in config[DOMAIN]:
        for index, doorstation_config in enumerate(config[DOMAIN][CONF_DEVICES]):
            if CONF_NAME not in doorstation_config:
                doorstation_config[CONF_NAME] = f"DoorBird {index + 1}"

            opp.async_create_task(
                opp.config_entries.flow.async_init(
                    DOMAIN, context={"source": SOURCE_IMPORT}, data=doorstation_config
                )
            )

    def _reset_device_favorites_handler(event):
        """Handle clearing favorites on device."""
        token = event.data.get("token")

        if token is None:
            return

        doorstation = get_doorstation_by_token(opp, token)

        if doorstation is None:
            _LOGGER.error("Device not found for provided token")
            return

        # Clear webhooks
        favorites = doorstation.device.favorites()

        for favorite_type in favorites:
            for favorite_id in favorites[favorite_type]:
                doorstation.device.delete_favorite(favorite_type, favorite_id)

    opp.bus.async_listen(RESET_DEVICE_FAVORITES, _reset_device_favorites_handler)

    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up DoorBird from a config entry."""

    _async_import_options_from_data_if_missing(opp, entry)

    doorstation_config = entry.data
    doorstation_options = entry.options
    config_entry_id = entry.entry_id

    device_ip = doorstation_config[CONF_HOST]
    username = doorstation_config[CONF_USERNAME]
    password = doorstation_config[CONF_PASSWORD]

    device = DoorBird(device_ip, username, password)
    try:
        status, info = await opp.async_add_executor_job(_init_doorbird_device, device)
    except urllib.error.HTTPError as err:
        if err.code == HTTP_UNAUTHORIZED:
            _LOGGER.error(
                "Authorization rejected by DoorBird for %s@%s", username, device_ip
            )
            return False
        raise ConfigEntryNotReady from err
    except OSError as oserr:
        _LOGGER.error("Failed to setup doorbird at %s: %s", device_ip, oserr)
        raise ConfigEntryNotReady from oserr

    if not status[0]:
        _LOGGER.error(
            "Could not connect to DoorBird as %s@%s: Error %s",
            username,
            device_ip,
            str(status[1]),
        )
        raise ConfigEntryNotReady

    token = doorstation_config.get(CONF_TOKEN, config_entry_id)
    custom_url = doorstation_config.get(CONF_CUSTOM_URL)
    name = doorstation_config.get(CONF_NAME)
    events = doorstation_options.get(CONF_EVENTS, [])
    doorstation = ConfiguredDoorBird(device, name, custom_url, token)
    doorstation.update_events(events)
    # Subscribe to doorbell or motion events
    if not await _async_register_events(opp, doorstation):
        raise ConfigEntryNotReady

    undo_listener = entry.add_update_listener(_update_listener)

    opp.data[DOMAIN][config_entry_id] = {
        DOOR_STATION: doorstation,
        DOOR_STATION_INFO: info,
        UNDO_UPDATE_LISTENER: undo_listener,
    }

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


def _init_doorbird_device(device):
    return device.ready(), device.info()


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""

    opp.data[DOMAIN][entry.entry_id][UNDO_UPDATE_LISTENER]()

    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def _async_register_events(opp, doorstation):
    try:
        await opp.async_add_executor_job(doorstation.register_events, opp)
    except HTTPError:
        opp.components.persistent_notification.async_create(
            "Doorbird configuration failed.  Please verify that API "
            "Operator permission is enabled for the Doorbird user. "
            "A restart will be required once permissions have been "
            "verified.",
            title="Doorbird Configuration Failure",
            notification_id="doorbird_schedule_error",
        )
        return False

    return True


async def _update_listener(opp: OpenPeerPower, entry: ConfigEntry):
    """Handle options update."""
    config_entry_id = entry.entry_id
    doorstation = opp.data[DOMAIN][config_entry_id][DOOR_STATION]
    doorstation.update_events(entry.options[CONF_EVENTS])
    # Subscribe to doorbell or motion events
    await _async_register_events(opp, doorstation)


@callback
def _async_import_options_from_data_if_missing(opp: OpenPeerPower, entry: ConfigEntry):
    options = dict(entry.options)
    modified = False
    for importable_option in [CONF_EVENTS]:
        if importable_option not in entry.options and importable_option in entry.data:
            options[importable_option] = entry.data[importable_option]
            modified = True

    if modified:
        opp.config_entries.async_update_entry(entry, options=options)


class ConfiguredDoorBird:
    """Attach additional information to pass along with configured device."""

    def __init__(self, device, name, custom_url, token):
        """Initialize configured device."""
        self._name = name
        self._device = device
        self._custom_url = custom_url
        self.events = None
        self.doorstation_events = None
        self._token = token

    def update_events(self, events):
        """Update the doorbird events."""
        self.events = events
        self.doorstation_events = [self._get_event_name(event) for event in self.events]

    @property
    def name(self):
        """Get custom device name."""
        return self._name

    @property
    def device(self):
        """Get the configured device."""
        return self._device

    @property
    def custom_url(self):
        """Get custom url for device."""
        return self._custom_url

    @property
    def token(self):
        """Get token for device."""
        return self._token

    def register_events(self, opp):
        """Register events on device."""
        # Get the URL of this server
        opp_url = get_url(opp)

        # Override url if another is specified in the configuration
        if self.custom_url is not None:
            opp_url = self.custom_url

        for event in self.doorstation_events:
            self._register_event(opp_url, event)

            _LOGGER.info("Successfully registered URL for %s on %s", event, self.name)

    @property
    def slug(self):
        """Get device slug."""
        return slugify(self._name)

    def _get_event_name(self, event):
        return f"{self.slug}_{event}"

    def _register_event(self, opp_url, event):
        """Add a schedule entry in the device for a sensor."""
        url = f"{opp_url}{API_URL}/{event}?token={self._token}"

        # Register OP URL as webhook if not already, then get the ID
        if not self.webhook_is_registered(url):
            self.device.change_favorite("http", f"Open Peer Power ({event})", url)

        fav_id = self.get_webhook_id(url)

        if not fav_id:
            _LOGGER.warning(
                'Could not find favorite for URL "%s". ' 'Skipping sensor "%s"',
                url,
                event,
            )
            return

    def webhook_is_registered(self, url, favs=None) -> bool:
        """Return whether the given URL is registered as a device favorite."""
        return self.get_webhook_id(url, favs) is not None

    def get_webhook_id(self, url, favs=None) -> str or None:
        """
        Return the device favorite ID for the given URL.

        The favorite must exist or there will be problems.
        """
        favs = favs if favs else self.device.favorites()

        if "http" not in favs:
            return None

        for fav_id in favs["http"]:
            if favs["http"][fav_id]["value"] == url:
                return fav_id

        return None

    def get_event_data(self):
        """Get data to pass along with OP event."""
        return {
            "timestamp": dt_util.utcnow().isoformat(),
            "live_video_url": self._device.live_video_url,
            "live_image_url": self._device.live_image_url,
            "rtsp_live_video_url": self._device.rtsp_live_video_url,
            "html5_viewer_url": self._device.html5_viewer_url,
        }


class DoorBirdRequestView(OpenPeerPowerView):
    """Provide a page for the device to call."""

    requires_auth = False
    url = API_URL
    name = API_URL[1:].replace("/", ":")
    extra_urls = [API_URL + "/{event}"]

    async def get(self, request, event):
        """Respond to requests from the device."""
        opp = request.app["opp"]

        token = request.query.get("token")

        device = get_doorstation_by_token(opp, token)

        if device is None:
            return web.Response(
                status=HTTP_UNAUTHORIZED, text="Invalid token provided."
            )

        if device:
            event_data = device.get_event_data()
        else:
            event_data = {}

        if event == "clear":
            opp.bus.async_fire(RESET_DEVICE_FAVORITES, {"token": token})

            message = f"HTTP Favorites cleared for {device.slug}"
            return web.Response(status=HTTP_OK, text=message)

        event_data[ATTR_ENTITY_ID] = opp.data[DOMAIN][
            DOOR_STATION_EVENT_ENTITY_IDS
        ].get(event)

        opp.bus.async_fire(f"{DOMAIN}_{event}", event_data)

        return web.Response(status=HTTP_OK, text="OK")
