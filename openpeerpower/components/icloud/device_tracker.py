"""Support for tracking for iCloud devices."""
from typing import Dict

from openpeerpower.components.device_tracker import SOURCE_TYPE_GPS
from openpeerpower.components.device_tracker.config_entry import TrackerEntity
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import callback
from openpeerpower.helpers.dispatcher import async_dispatcher_connect
from openpeerpower.helpers.typing import OpenPeerPowerType

from .account import IcloudAccount, IcloudDevice
from .const import (
    DEVICE_LOCATION_HORIZONTAL_ACCURACY,
    DEVICE_LOCATION_LATITUDE,
    DEVICE_LOCATION_LONGITUDE,
    DOMAIN,
)


async def async_setup_scanner(opp: OpenPeerPowerType, config, see, discovery_info=None):
    """Old way of setting up the iCloud tracker."""


async def async_setup_entry(
    opp: OpenPeerPowerType, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up device tracker for iCloud component."""
    account = opp.data[DOMAIN][entry.unique_id]
    tracked = set()

    @callback
    def update_account():
        """Update the values of the account."""
        add_entities(account, async_add_entities, tracked)

    account.listeners.append(
        async_dispatcher_connect(opp, account.signal_device_new, update_account)
    )

    update_account()


@callback
def add_entities(account, async_add_entities, tracked):
    """Add new tracker entities from the account."""
    new_tracked = []

    for dev_id, device in account.devices.items():
        if dev_id in tracked or device.location is None:
            continue

        new_tracked.append(IcloudTrackerEntity(account, device))
        tracked.add(dev_id)

    if new_tracked:
        async_add_entities(new_tracked, True)


class IcloudTrackerEntity(TrackerEntity):
    """Represent a tracked device."""

    def __init__(self, account: IcloudAccount, device: IcloudDevice):
        """Set up the iCloud tracker entity."""
        self._account = account
        self._device = device
        self._unsub_dispatcher = None

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._device.unique_id

    @property
    def name(self) -> str:
        """Return the name of the device."""
        return self._device.name

    @property
    def location_accuracy(self):
        """Return the location accuracy of the device."""
        return self._device.location[DEVICE_LOCATION_HORIZONTAL_ACCURACY]

    @property
    def latitude(self):
        """Return latitude value of the device."""
        return self._device.location[DEVICE_LOCATION_LATITUDE]

    @property
    def longitude(self):
        """Return longitude value of the device."""
        return self._device.location[DEVICE_LOCATION_LONGITUDE]

    @property
    def battery_level(self) -> int:
        """Return the battery level of the device."""
        return self._device.battery_level

    @property
    def source_type(self) -> str:
        """Return the source type, eg gps or router, of the device."""
        return SOURCE_TYPE_GPS

    @property
    def icon(self) -> str:
        """Return the icon."""
        return icon_for_icloud_device(self._device)

    @property
    def device_state_attributes(self) -> Dict[str, any]:
        """Return the device state attributes."""
        return self._device.state_attributes

    @property
    def device_info(self) -> Dict[str, any]:
        """Return the device information."""
        return {
            "identifiers": {(DOMAIN, self._device.unique_id)},
            "name": self._device.name,
            "manufacturer": "Apple",
            "model": self._device.device_model,
        }

    async def async_added_to_opp(self):
        """Register state update callback."""
        self._unsub_dispatcher = async_dispatcher_connect(
            self.opp, self._account.signal_device_update, self.async_write_op_state
        )

    async def async_will_remove_from_opp(self):
        """Clean up after entity before removal."""
        self._unsub_dispatcher()


def icon_for_icloud_device(icloud_device: IcloudDevice) -> str:
    """Return a battery icon valid identifier."""
    switcher = {
        "iPad": "mdi:tablet-ipad",
        "iPhone": "mdi:cellphone-iphone",
        "iPod": "mdi:ipod",
        "iMac": "mdi:desktop-mac",
        "MacBookPro": "mdi:laptop-mac",
    }

    return switcher.get(icloud_device.device_class, "mdi:cellphone-link")
