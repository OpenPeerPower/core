"""Switch platform for FireServiceRota integration."""
import logging

from openpeerpower.components.switch import SwitchEntity
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.helpers.dispatcher import async_dispatcher_connect

from .const import DATA_CLIENT, DATA_COORDINATOR, DOMAIN as FIRESERVICEROTA_DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    opp: OpenPeerPower, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up FireServiceRota switch based on a config entry."""
    client = opp.data[FIRESERVICEROTA_DOMAIN][entry.entry_id][DATA_CLIENT]

    coordinator = opp.data[FIRESERVICEROTA_DOMAIN][entry.entry_id][DATA_COORDINATOR]

    async_add_entities([ResponseSwitch(coordinator, client, entry)])


class ResponseSwitch(SwitchEntity):
    """Representation of an FireServiceRota switch."""

    def __init__(self, coordinator, client, entry):
        """Initialize."""
        self._coordinator = coordinator
        self._client = client
        self._unique_id = f"{entry.unique_id}_Response"
        self._entry_id = entry.entry_id

        self._state = None
        self._state_attributes = {}
        self._state_icon = None

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return "Incident Response"

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        if self._state_icon == "acknowledged":
            return "mdi:run-fast"
        if self._state_icon == "rejected":
            return "mdi:account-off-outline"

        return "mdi:forum"

    @property
    def is_on(self) -> bool:
        """Get the assumed state of the switch."""
        return self._state

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this switch."""
        return self._unique_id

    @property
    def should_poll(self) -> bool:
        """No polling needed."""
        return False

    @property
    def available(self):
        """Return if switch is available."""
        return self._client.on_duty

    @property
    def extra_state_attributes(self) -> object:
        """Return available attributes for switch."""
        attr = {}
        if not self._state_attributes:
            return attr

        data = self._state_attributes
        attr = {
            key: data[key]
            for key in (
                "user_name",
                "assigned_skill_ids",
                "responded_at",
                "start_time",
                "status",
                "reported_status",
                "arrived_at_station",
                "available_at_incident_creation",
                "active_duty_function_ids",
            )
            if key in data
        }

        return attr

    async def async_turn_on(self, **kwargs) -> None:
        """Send Acknowlegde response status."""
        await self.async_set_response(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Send Reject response status."""
        await self.async_set_response(False)

    async def async_set_response(self, value) -> None:
        """Send response status."""
        if not self._client.on_duty:
            _LOGGER.debug(
                "Cannot send incident response when not on duty",
            )
            return

        await self._client.async_set_response(value)
        self.client_update()

    async def async_added_to_opp(self) -> None:
        """Register update callback."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.opp,
                f"{FIRESERVICEROTA_DOMAIN}_{self._entry_id}_update",
                self.client_update,
            )
        )
        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_op_state)
        )

    @callback
    def client_update(self) -> None:
        """Handle updated incident data from the client."""
        self.async_schedule_update_op_state(True)

    async def async_update(self) -> bool:
        """Update FireServiceRota response data."""
        data = await self._client.async_response_update()

        if not data or "status" not in data:
            return

        self._state = data["status"] == "acknowledged"
        self._state_attributes = data
        self._state_icon = data["status"]

        _LOGGER.debug("Set state of entity 'Response Switch' to '%s'", self._state)
