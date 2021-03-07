"""Support for Wireless Sensor Tags."""
import logging

from requests.exceptions import ConnectTimeout, HTTPError
import voluptuous as vol
from wirelesstagpy import NotificationConfig as NC, WirelessTags, WirelessTagsException

from openpeerpower import util
from openpeerpower.const import (
    ATTR_BATTERY_LEVEL,
    ATTR_VOLTAGE,
    CONF_PASSWORD,
    CONF_USERNAME,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    VOLT,
)
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.dispatcher import dispatcher_send
from openpeerpower.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)


# Strength of signal in dBm
ATTR_TAG_SIGNAL_STRENGTH = "signal_strength"
# Indicates if tag is out of range or not
ATTR_TAG_OUT_OF_RANGE = "out_of_range"
# Number in percents from max power of tag receiver
ATTR_TAG_POWER_CONSUMPTION = "power_consumption"


NOTIFICATION_ID = "wirelesstag_notification"
NOTIFICATION_TITLE = "Wireless Sensor Tag Setup"

DOMAIN = "wirelesstag"
DEFAULT_ENTITY_NAMESPACE = "wirelesstag"

# Template for signal - first parameter is tag_id,
# second, tag manager mac address
SIGNAL_TAG_UPDATE = "wirelesstag.tag_info_updated_{}_{}"

# Template for signal - tag_id, sensor type and
# tag manager mac address
SIGNAL_BINARY_EVENT_UPDATE = "wirelesstag.binary_event_updated_{}_{}_{}"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


class WirelessTagPlatform:
    """Principal object to manage all registered in OP tags."""

    def __init__(self, opp, api):
        """Designated initializer for wirelesstags platform."""
        self.opp = opp
        self.api = api
        self.tags = {}
        self._local_base_url = None

    @property
    def tag_manager_macs(self):
        """Return list of tag managers mac addresses in user account."""
        return self.api.mac_addresses

    def load_tags(self):
        """Load tags from remote server."""
        self.tags = self.api.load_tags()
        return self.tags

    def arm(self, switch):
        """Arm entity sensor monitoring."""
        func_name = f"arm_{switch.sensor_type}"
        arm_func = getattr(self.api, func_name)
        if arm_func is not None:
            arm_func(switch.tag_id, switch.tag_manager_mac)

    def disarm(self, switch):
        """Disarm entity sensor monitoring."""
        func_name = f"disarm_{switch.sensor_type}"
        disarm_func = getattr(self.api, func_name)
        if disarm_func is not None:
            disarm_func(switch.tag_id, switch.tag_manager_mac)

    def make_notifications(self, binary_sensors, mac):
        """Create configurations for push notifications."""
        _LOGGER.info("Creating configurations for push notifications")
        configs = []

        bi_url = self.binary_event_callback_url
        for bi_sensor in binary_sensors:
            configs.extend(bi_sensor.event.build_notifications(bi_url, mac))

        update_url = self.update_callback_url

        update_config = NC.make_config_for_update_event(update_url, mac)

        configs.append(update_config)
        return configs

    def install_push_notifications(self, binary_sensors):
        """Register local push notification from tag manager."""
        _LOGGER.info("Registering local push notifications")
        for mac in self.tag_manager_macs:
            configs = self.make_notifications(binary_sensors, mac)
            # install notifications for all tags in tag manager
            # specified by mac
            result = self.api.install_push_notification(0, configs, True, mac)
            if not result:
                self.opp.components.persistent_notification.create(
                    "Error: failed to install local push notifications <br />",
                    title="Wireless Sensor Tag Setup Local Push Notifications",
                    notification_id="wirelesstag_failed_push_notification",
                )
            else:
                _LOGGER.info(
                    "Installed push notifications for all tags in %s",
                    mac,
                )

    @property
    def local_base_url(self):
        """Define base url of opp in local network."""
        if self._local_base_url is None:
            self._local_base_url = f"http://{util.get_local_ip()}"

            port = self.opp.config.api.port
            if port is not None:
                self._local_base_url += f":{port}"
        return self._local_base_url

    @property
    def update_callback_url(self):
        """Return url for local push notifications(update event)."""
        return f"{self.local_base_url}/api/events/wirelesstag_update_tags"

    @property
    def binary_event_callback_url(self):
        """Return url for local push notifications(binary event)."""
        return f"{self.local_base_url}/api/events/wirelesstag_binary_event"

    def handle_update_tags_event(self, event):
        """Handle push event from wireless tag manager."""
        _LOGGER.info("push notification for update arrived: %s", event)
        try:
            tag_id = event.data.get("id")
            mac = event.data.get("mac")
            dispatcher_send(self.opp, SIGNAL_TAG_UPDATE.format(tag_id, mac), event)
        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.error(
                "Unable to handle tag update event:\
                          %s error: %s",
                str(event),
                str(ex),
            )

    def handle_binary_event(self, event):
        """Handle push notifications for binary (on/off) events."""
        _LOGGER.info("Push notification for binary event arrived: %s", event)
        try:
            tag_id = event.data.get("id")
            event_type = event.data.get("type")
            mac = event.data.get("mac")
            dispatcher_send(
                self.opp,
                SIGNAL_BINARY_EVENT_UPDATE.format(tag_id, event_type, mac),
                event,
            )
        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.error(
                "Unable to handle tag binary event:\
                          %s error: %s",
                str(event),
                str(ex),
            )


def setup(opp, config):
    """Set up the Wireless Sensor Tag component."""
    conf = config[DOMAIN]
    username = conf.get(CONF_USERNAME)
    password = conf.get(CONF_PASSWORD)

    try:
        wirelesstags = WirelessTags(username=username, password=password)

        platform = WirelessTagPlatform(opp, wirelesstags)
        platform.load_tags()
        opp.data[DOMAIN] = platform
    except (ConnectTimeout, HTTPError, WirelessTagsException) as ex:
        _LOGGER.error("Unable to connect to wirelesstag.net service: %s", str(ex))
        opp.components.persistent_notification.create(
            f"Error: {ex}<br />Please restart opp after fixing this.",
            title=NOTIFICATION_TITLE,
            notification_id=NOTIFICATION_ID,
        )
        return False

    # listen to custom events
    opp.bus.listen("wirelesstag_update_tags", opp.data[DOMAIN].handle_update_tags_event)
    opp.bus.listen("wirelesstag_binary_event", opp.data[DOMAIN].handle_binary_event)

    return True


class WirelessTagBaseSensor(Entity):
    """Base class for OP implementation for Wireless Sensor Tag."""

    def __init__(self, api, tag):
        """Initialize a base sensor for Wireless Sensor Tag platform."""
        self._api = api
        self._tag = tag
        self._uuid = self._tag.uuid
        self.tag_id = self._tag.tag_id
        self.tag_manager_mac = self._tag.tag_manager_mac
        self._name = self._tag.name
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def principal_value(self):
        """Return base value.

        Subclasses need override based on type of sensor.
        """
        return 0

    def updated_state_value(self):
        """Return formatted value.

        The default implementation formats principal value.
        """
        return self.decorate_value(self.principal_value)

    # pylint: disable=no-self-use
    def decorate_value(self, value):
        """Decorate input value to be well presented for end user."""
        return f"{value:.1f}"

    @property
    def available(self):
        """Return True if entity is available."""
        return self._tag.is_alive

    def update(self):
        """Update state."""
        if not self.should_poll:
            return

        updated_tags = self._api.load_tags()
        updated_tag = updated_tags[self._uuid]
        if updated_tag is None:
            _LOGGER.error('Unable to update tag: "%s"', self.name)
            return

        self._tag = updated_tag
        self._state = self.updated_state_value()

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            ATTR_BATTERY_LEVEL: int(self._tag.battery_remaining * 100),
            ATTR_VOLTAGE: f"{self._tag.battery_volts:.2f}{VOLT}",
            ATTR_TAG_SIGNAL_STRENGTH: f"{self._tag.signal_strength}{SIGNAL_STRENGTH_DECIBELS_MILLIWATT}",
            ATTR_TAG_OUT_OF_RANGE: not self._tag.is_in_range,
            ATTR_TAG_POWER_CONSUMPTION: f"{self._tag.power_consumption:.2f}{PERCENTAGE}",
        }
