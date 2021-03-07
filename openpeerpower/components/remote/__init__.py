"""Support to interface with universal remote control devices."""
from datetime import timedelta
import functools as ft
import logging
from typing import Any, Dict, Iterable, List, Optional, cast

import voluptuous as vol

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import (
    ATTR_COMMAND,
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_ON,
)
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.config_validation import (  # noqa: F401
    PLATFORM_SCHEMA,
    PLATFORM_SCHEMA_BASE,
    make_entity_service_schema,
)
from openpeerpower.helpers.entity import ToggleEntity
from openpeerpower.helpers.entity_component import EntityComponent
from openpeerpower.helpers.typing import ConfigType, OpenPeerPowerType
from openpeerpower.loader import bind_opp

# mypy: allow-untyped-calls, allow-untyped-defs, no-check-untyped-defs

_LOGGER = logging.getLogger(__name__)

ATTR_ACTIVITY = "activity"
ATTR_ACTIVITY_LIST = "activity_list"
ATTR_CURRENT_ACTIVITY = "current_activity"
ATTR_COMMAND_TYPE = "command_type"
ATTR_DEVICE = "device"
ATTR_NUM_REPEATS = "num_repeats"
ATTR_DELAY_SECS = "delay_secs"
ATTR_HOLD_SECS = "hold_secs"
ATTR_ALTERNATIVE = "alternative"
ATTR_TIMEOUT = "timeout"

DOMAIN = "remote"
SCAN_INTERVAL = timedelta(seconds=30)

ENTITY_ID_FORMAT = DOMAIN + ".{}"

MIN_TIME_BETWEEN_SCANS = timedelta(seconds=10)

SERVICE_SEND_COMMAND = "send_command"
SERVICE_LEARN_COMMAND = "learn_command"
SERVICE_DELETE_COMMAND = "delete_command"
SERVICE_SYNC = "sync"

DEFAULT_NUM_REPEATS = 1
DEFAULT_DELAY_SECS = 0.4
DEFAULT_HOLD_SECS = 0

SUPPORT_LEARN_COMMAND = 1
SUPPORT_DELETE_COMMAND = 2
SUPPORT_ACTIVITY = 4

REMOTE_SERVICE_ACTIVITY_SCHEMA = make_entity_service_schema(
    {vol.Optional(ATTR_ACTIVITY): cv.string}
)


@bind_opp
def is_on(opp: OpenPeerPowerType, entity_id: str) -> bool:
    """Return if the remote is on based on the statemachine."""
    return opp.states.is_state(entity_id, STATE_ON)


async def async_setup(opp: OpenPeerPowerType, config: ConfigType) -> bool:
    """Track states and offer events for remotes."""
    component = opp.data[DOMAIN] = EntityComponent(_LOGGER, DOMAIN, opp, SCAN_INTERVAL)
    await component.async_setup(config)

    component.async_register_entity_service(
        SERVICE_TURN_OFF, REMOTE_SERVICE_ACTIVITY_SCHEMA, "async_turn_off"
    )

    component.async_register_entity_service(
        SERVICE_TURN_ON, REMOTE_SERVICE_ACTIVITY_SCHEMA, "async_turn_on"
    )

    component.async_register_entity_service(
        SERVICE_TOGGLE, REMOTE_SERVICE_ACTIVITY_SCHEMA, "async_toggle"
    )

    component.async_register_entity_service(
        SERVICE_SEND_COMMAND,
        {
            vol.Required(ATTR_COMMAND): vol.All(cv.ensure_list, [cv.string]),
            vol.Optional(ATTR_DEVICE): cv.string,
            vol.Optional(
                ATTR_NUM_REPEATS, default=DEFAULT_NUM_REPEATS
            ): cv.positive_int,
            vol.Optional(ATTR_DELAY_SECS): vol.Coerce(float),
            vol.Optional(ATTR_HOLD_SECS, default=DEFAULT_HOLD_SECS): vol.Coerce(float),
        },
        "async_send_command",
    )

    component.async_register_entity_service(
        SERVICE_LEARN_COMMAND,
        {
            vol.Optional(ATTR_DEVICE): cv.string,
            vol.Optional(ATTR_COMMAND): vol.All(cv.ensure_list, [cv.string]),
            vol.Optional(ATTR_COMMAND_TYPE): cv.string,
            vol.Optional(ATTR_ALTERNATIVE): cv.boolean,
            vol.Optional(ATTR_TIMEOUT): cv.positive_int,
        },
        "async_learn_command",
    )

    component.async_register_entity_service(
        SERVICE_DELETE_COMMAND,
        {
            vol.Required(ATTR_COMMAND): vol.All(cv.ensure_list, [cv.string]),
            vol.Optional(ATTR_DEVICE): cv.string,
        },
        "async_delete_command",
    )

    return True


async def async_setup_entry(opp: OpenPeerPowerType, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    return await cast(EntityComponent, opp.data[DOMAIN]).async_setup_entry(entry)


async def async_unload_entry(opp: OpenPeerPowerType, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await cast(EntityComponent, opp.data[DOMAIN]).async_unload_entry(entry)


class RemoteEntity(ToggleEntity):
    """Representation of a remote."""

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return 0

    @property
    def current_activity(self) -> Optional[str]:
        """Active activity."""
        return None

    @property
    def activity_list(self) -> Optional[List[str]]:
        """List of available activities."""
        return None

    @property
    def state_attributes(self) -> Optional[Dict[str, Any]]:
        """Return optional state attributes."""
        if not self.supported_features & SUPPORT_ACTIVITY:
            return None

        return {
            ATTR_ACTIVITY_LIST: self.activity_list,
            ATTR_CURRENT_ACTIVITY: self.current_activity,
        }

    def send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send commands to a device."""
        raise NotImplementedError()

    async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send commands to a device."""
        assert self.opp is not None
        await self.opp.async_add_executor_job(
            ft.partial(self.send_command, command, **kwargs)
        )

    def learn_command(self, **kwargs: Any) -> None:
        """Learn a command from a device."""
        raise NotImplementedError()

    async def async_learn_command(self, **kwargs: Any) -> None:
        """Learn a command from a device."""
        assert self.opp is not None
        await self.opp.async_add_executor_job(ft.partial(self.learn_command, **kwargs))

    def delete_command(self, **kwargs: Any) -> None:
        """Delete commands from the database."""
        raise NotImplementedError()

    async def async_delete_command(self, **kwargs: Any) -> None:
        """Delete commands from the database."""
        assert self.opp is not None
        await self.opp.async_add_executor_job(ft.partial(self.delete_command, **kwargs))


class RemoteDevice(RemoteEntity):
    """Representation of a remote (for backwards compatibility)."""

    def __init_subclass__(cls, **kwargs):
        """Print deprecation warning."""
        super().__init_subclass__(**kwargs)
        _LOGGER.warning(
            "RemoteDevice is deprecated, modify %s to extend RemoteEntity",
            cls.__name__,
        )
