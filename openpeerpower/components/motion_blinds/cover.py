"""Support for Motion Blinds using their WLAN API."""

import logging

from motionblinds import BlindType
import voluptuous as vol

from openpeerpower.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    DEVICE_CLASS_AWNING,
    DEVICE_CLASS_BLIND,
    DEVICE_CLASS_CURTAIN,
    DEVICE_CLASS_GATE,
    DEVICE_CLASS_SHADE,
    DEVICE_CLASS_SHUTTER,
    CoverEntity,
)
from openpeerpower.helpers import config_validation as cv, entity_platform
from openpeerpower.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ABSOLUTE_POSITION,
    ATTR_WIDTH,
    DOMAIN,
    KEY_COORDINATOR,
    KEY_GATEWAY,
    MANUFACTURER,
    SERVICE_SET_ABSOLUTE_POSITION,
)

_LOGGER = logging.getLogger(__name__)


POSITION_DEVICE_MAP = {
    BlindType.RollerBlind: DEVICE_CLASS_SHADE,
    BlindType.RomanBlind: DEVICE_CLASS_SHADE,
    BlindType.HoneycombBlind: DEVICE_CLASS_SHADE,
    BlindType.DimmingBlind: DEVICE_CLASS_SHADE,
    BlindType.DayNightBlind: DEVICE_CLASS_SHADE,
    BlindType.RollerShutter: DEVICE_CLASS_SHUTTER,
    BlindType.Switch: DEVICE_CLASS_SHUTTER,
    BlindType.RollerGate: DEVICE_CLASS_GATE,
    BlindType.Awning: DEVICE_CLASS_AWNING,
    BlindType.Curtain: DEVICE_CLASS_CURTAIN,
    BlindType.CurtainLeft: DEVICE_CLASS_CURTAIN,
    BlindType.CurtainRight: DEVICE_CLASS_CURTAIN,
}

TILT_DEVICE_MAP = {
    BlindType.VenetianBlind: DEVICE_CLASS_BLIND,
    BlindType.ShangriLaBlind: DEVICE_CLASS_BLIND,
    BlindType.DoubleRoller: DEVICE_CLASS_SHADE,
}

TDBU_DEVICE_MAP = {
    BlindType.TopDownBottomUp: DEVICE_CLASS_SHADE,
}


SET_ABSOLUTE_POSITION_SCHEMA = {
    vol.Required(ATTR_ABSOLUTE_POSITION): vol.All(cv.positive_int, vol.Range(max=100)),
    vol.Optional(ATTR_WIDTH): vol.All(cv.positive_int, vol.Range(max=100)),
}


async def async_setup_entry.opp, config_entry, async_add_entities):
    """Set up the Motion Blind from a config entry."""
    entities = []
    motion_gateway = opp.data[DOMAIN][config_entry.entry_id][KEY_GATEWAY]
    coordinator = opp.data[DOMAIN][config_entry.entry_id][KEY_COORDINATOR]

    for blind in motion_gateway.device_list.values():
        if blind.type in POSITION_DEVICE_MAP:
            entities.append(
                MotionPositionDevice(
                    coordinator, blind, POSITION_DEVICE_MAP[blind.type], config_entry
                )
            )

        elif blind.type in TILT_DEVICE_MAP:
            entities.append(
                MotionTiltDevice(
                    coordinator, blind, TILT_DEVICE_MAP[blind.type], config_entry
                )
            )

        elif blind.type in TDBU_DEVICE_MAP:
            entities.append(
                MotionTDBUDevice(
                    coordinator, blind, TDBU_DEVICE_MAP[blind.type], config_entry, "Top"
                )
            )
            entities.append(
                MotionTDBUDevice(
                    coordinator,
                    blind,
                    TDBU_DEVICE_MAP[blind.type],
                    config_entry,
                    "Bottom",
                )
            )
            entities.append(
                MotionTDBUDevice(
                    coordinator,
                    blind,
                    TDBU_DEVICE_MAP[blind.type],
                    config_entry,
                    "Combined",
                )
            )

        else:
            _LOGGER.warning("Blind type '%s' not yet supported", blind.blind_type)

    async_add_entities(entities)

    platform = entity_platform.current_platform.get()
    platform.async_register_entity_service(
        SERVICE_SET_ABSOLUTE_POSITION,
        SET_ABSOLUTE_POSITION_SCHEMA,
        SERVICE_SET_ABSOLUTE_POSITION,
    )


class MotionPositionDevice(CoordinatorEntity, CoverEntity):
    """Representation of a Motion Blind Device."""

    def __init__(self, coordinator, blind, device_class, config_entry):
        """Initialize the blind."""
        super().__init__(coordinator)

        self._blind = blind
        self._device_class = device_class
        self._config_entry = config_entry

    @property
    def unique_id(self):
        """Return the unique id of the blind."""
        return self._blind.mac

    @property
    def device_info(self):
        """Return the device info of the blind."""
        device_info = {
            "identifiers": {(DOMAIN, self._blind.mac)},
            "manufacturer": MANUFACTURER,
            "name": f"{self._blind.blind_type}-{self._blind.mac[12:]}",
            "model": self._blind.blind_type,
            "via_device": (DOMAIN, self._config_entry.unique_id),
        }

        return device_info

    @property
    def name(self):
        """Return the name of the blind."""
        return f"{self._blind.blind_type}-{self._blind.mac[12:]}"

    @property
    def available(self):
        """Return True if entity is available."""
        return self._blind.available

    @property
    def current_cover_position(self):
        """
        Return current position of cover.

        None is unknown, 0 is open, 100 is closed.
        """
        if self._blind.position is None:
            return None
        return 100 - self._blind.position

    @property
    def device_class(self):
        """Return the device class."""
        return self._device_class

    @property
    def is_closed(self):
        """Return if the cover is closed or not."""
        return self._blind.position == 100

    async def async_added_to_opp(self):
        """Subscribe to multicast pushes and register signal handler."""
        self._blind.Register_callback(self.unique_id, self.schedule_update_op_state)
        await super().async_added_to_opp()

    async def async_will_remove_from.opp(self):
        """Unsubscribe when removed."""
        self._blind.Remove_callback(self.unique_id)
        await super().async_will_remove_from.opp()

    def open_cover(self, **kwargs):
        """Open the cover."""
        self._blind.Open()

    def close_cover(self, **kwargs):
        """Close cover."""
        self._blind.Close()

    def set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        position = kwargs[ATTR_POSITION]
        self._blind.Set_position(100 - position)

    def set_absolute_position(self, **kwargs):
        """Move the cover to a specific absolute position (see TDBU)."""
        position = kwargs[ATTR_ABSOLUTE_POSITION]
        self._blind.Set_position(100 - position)

    def stop_cover(self, **kwargs):
        """Stop the cover."""
        self._blind.Stop()


class MotionTiltDevice(MotionPositionDevice):
    """Representation of a Motion Blind Device."""

    @property
    def current_cover_tilt_position(self):
        """
        Return current angle of cover.

        None is unknown, 0 is closed/minimum tilt, 100 is fully open/maximum tilt.
        """
        if self._blind.angle is None:
            return None
        return self._blind.angle * 100 / 180

    def open_cover_tilt(self, **kwargs):
        """Open the cover tilt."""
        self._blind.Set_angle(180)

    def close_cover_tilt(self, **kwargs):
        """Close the cover tilt."""
        self._blind.Set_angle(0)

    def set_cover_tilt_position(self, **kwargs):
        """Move the cover tilt to a specific position."""
        angle = kwargs[ATTR_TILT_POSITION] * 180 / 100
        self._blind.Set_angle(angle)

    def stop_cover_tilt(self, **kwargs):
        """Stop the cover."""
        self._blind.Stop()


class MotionTDBUDevice(MotionPositionDevice):
    """Representation of a Motion Top Down Bottom Up blind Device."""

    def __init__(self, coordinator, blind, device_class, config_entry, motor):
        """Initialize the blind."""
        super().__init__(coordinator, blind, device_class, config_entry)
        self._motor = motor
        self._motor_key = motor[0]

        if self._motor not in ["Bottom", "Top", "Combined"]:
            _LOGGER.error("Unknown motor '%s'", self._motor)

    @property
    def unique_id(self):
        """Return the unique id of the blind."""
        return f"{self._blind.mac}-{self._motor}"

    @property
    def name(self):
        """Return the name of the blind."""
        return f"{self._blind.blind_type}-{self._motor}-{self._blind.mac[12:]}"

    @property
    def current_cover_position(self):
        """
        Return current position of cover.

        None is unknown, 0 is open, 100 is closed.
        """
        if self._blind.scaled_position is None:
            return None

        return 100 - self._blind.scaled_position[self._motor_key]

    @property
    def is_closed(self):
        """Return if the cover is closed or not."""
        if self._blind.position is None:
            return None

        if self._motor == "Combined":
            return self._blind.width == 100

        return self._blind.position[self._motor_key] == 100

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        attributes = {}
        if self._blind.position is not None:
            attributes[ATTR_ABSOLUTE_POSITION] = (
                100 - self._blind.position[self._motor_key]
            )
        if self._blind.width is not None:
            attributes[ATTR_WIDTH] = self._blind.width
        return attributes

    def open_cover(self, **kwargs):
        """Open the cover."""
        self._blind.Open(motor=self._motor_key)

    def close_cover(self, **kwargs):
        """Close cover."""
        self._blind.Close(motor=self._motor_key)

    def set_cover_position(self, **kwargs):
        """Move the cover to a specific scaled position."""
        position = kwargs[ATTR_POSITION]
        self._blind.Set_scaled_position(100 - position, motor=self._motor_key)

    def set_absolute_position(self, **kwargs):
        """Move the cover to a specific absolute position."""
        position = kwargs[ATTR_ABSOLUTE_POSITION]
        target_width = kwargs.get(ATTR_WIDTH, None)

        self._blind.Set_position(
            100 - position, motor=self._motor_key, width=target_width
        )

    def stop_cover(self, **kwargs):
        """Stop the cover."""
        self._blind.Stop(motor=self._motor_key)
