"""StarLine base entity."""
from typing import Callable, Optional

from openpeerpower.helpers.entity import Entity

from .account import StarlineAccount, StarlineDevice


class StarlineEntity(Entity):
    """StarLine base entity class."""

    def __init__(
        self, account: StarlineAccount, device: StarlineDevice, key: str, name: str
    ):
        """Initialize StarLine entity."""
        self._account = account
        self._device = device
        self._key = key
        self._name = name
        self._unsubscribe_api: Optional[Callable] = None

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def available(self):
        """Return True if entity is available."""
        return self._account.api.available

    @property
    def unique_id(self):
        """Return the unique ID of the entity."""
        return f"starline-{self._key}-{self._device.device_id}"

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._device.name} {self._name}"

    @property
    def device_info(self):
        """Return the device info."""
        return self._account.device_info(self._device)

    def update(self):
        """Read new state data."""
        self.schedule_update_op_state()

    async def async_added_to_opp(self):
        """Call when entity about to be added to Open Peer Power."""
        await super().async_added_to_opp()
        self._unsubscribe_api = self._account.api.add_update_listener(self.update)

    async def async_will_remove_from_opp(self):
        """Call when entity is being removed from Open Peer Power."""
        await super().async_will_remove_from_opp()
        if self._unsubscribe_api is not None:
            self._unsubscribe_api()
            self._unsubscribe_api = None
