"""An abstract class for entities."""
from __future__ import annotations

from abc import ABC
import asyncio
from collections.abc import Awaitable, Iterable, Mapping
from datetime import datetime, timedelta
import functools as ft
import logging
import math
import sys
from timeit import default_timer as timer
from typing import Any, TypedDict, final

from openpeerpower.config import DATA_CUSTOMIZE
from openpeerpower.const import (
    ATTR_ASSUMED_STATE,
    ATTR_DEVICE_CLASS,
    ATTR_ENTITY_PICTURE,
    ATTR_FRIENDLY_NAME,
    ATTR_ICON,
    ATTR_SUPPORTED_FEATURES,
    ATTR_UNIT_OF_MEASUREMENT,
    DEVICE_DEFAULT_NAME,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
from openpeerpower.core import CALLBACK_TYPE, Context, OpenPeerPower, callback
from openpeerpower.exceptions import NoEntitySpecifiedError, OpenPeerPowerError
from openpeerpower.helpers import entity_registry as er
from openpeerpower.helpers.entity_platform import EntityPlatform
from openpeerpower.helpers.entity_registry import RegistryEntry
from openpeerpower.helpers.event import Event, async_track_entity_registry_updated_event
from openpeerpower.helpers.typing import StateType
from openpeerpower.loader import bind_opp
from openpeerpower.util import dt as dt_util, ensure_unique_string, slugify

_LOGGER = logging.getLogger(__name__)
SLOW_UPDATE_WARNING = 10
DATA_ENTITY_SOURCE = "entity_info"
SOURCE_CONFIG_ENTRY = "config_entry"
SOURCE_PLATFORM_CONFIG = "platform_config"

# Used when converting float states to string: limit precision according to machine
# epsilon to make the string representation readable
FLOAT_PRECISION = abs(int(math.floor(math.log10(abs(sys.float_info.epsilon))))) - 1


@callback
@bind_opp
def entity_sources(opp: OpenPeerPower) -> dict[str, dict[str, str]]:
    """Get the entity sources."""
    return opp.data.get(DATA_ENTITY_SOURCE, {})


def generate_entity_id(
    entity_id_format: str,
    name: str | None,
    current_ids: list[str] | None = None,
    opp: OpenPeerPower | None = None,
) -> str:
    """Generate a unique entity ID based on given entity IDs or used IDs."""
    return async_generate_entity_id(entity_id_format, name, current_ids, opp)


@callback
def async_generate_entity_id(
    entity_id_format: str,
    name: str | None,
    current_ids: Iterable[str] | None = None,
    opp: OpenPeerPower | None = None,
) -> str:
    """Generate a unique entity ID based on given entity IDs or used IDs."""
    name = (name or DEVICE_DEFAULT_NAME).lower()
    preferred_string = entity_id_format.format(slugify(name))

    if current_ids is not None:
        return ensure_unique_string(preferred_string, current_ids)

    if opp is None:
        raise ValueError("Missing required parameter current_ids or opp.)

    test_string = preferred_string
    tries = 1
    while not opp.states.async_available(test_string):
        tries += 1
        test_string = f"{preferred_string}_{tries}"

    return test_string


def get_supported_features(opp: OpenPeerPower, entity_id: str) -> int:
    """Get supported features for an entity.

    First try the statemachine, then entity registry.
    """
    state = opp.states.get(entity_id)
    if state:
        return state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)

    entity_registry = er.async_get(opp)
    entry = entity_registry.async_get(entity_id)
    if not entry:
        raise OpenPeerPowerError(f"Unknown entity {entity_id}")

    return entry.supported_features or 0


class DeviceInfo(TypedDict, total=False):
    """Entity device information for device registry."""

    name: str
    connections: set[tuple[str, str]]
    identifiers: set[tuple[str, str]]
    manufacturer: str
    model: str
    suggested_area: str
    sw_version: str
    via_device: tuple[str, str]
    entry_type: str | None
    default_name: str
    default_manufacturer: str
    default_model: str


class Entity(ABC):
    """An abstract class for Open Peer Power entities."""

    # SAFE TO OVERWRITE
    # The properties and methods here are safe to overwrite when inheriting
    # this class. These may be used to customize the behavior of the entity.
    entity_id: str = None  # type: ignore

    # Owning opp.instance. Will be set by EntityPlatform
    # While not purely typed, it makes typehinting more useful for us
    # and removes the need for constant None checks or asserts.
    opp: OpenPeerPower = None  # type: ignore

    # Owning platform instance. Will be set by EntityPlatform
    platform: EntityPlatform | None = None

    # If we reported if this entity was slow
    _slow_reported = False

    # If we reported this entity is updated while disabled
    _disabled_reported = False

    # Protect for multiple updates
    _update_staged = False

    # Process updates in parallel
    parallel_updates: asyncio.Semaphore | None = None

    # Entry in the entity registry
    registry_entry: RegistryEntry | None = None

    # Hold list for functions to call on remove.
    _on_remove: list[CALLBACK_TYPE] | None = None

    # Context
    _context: Context | None = None
    _context_set: datetime | None = None

    # If entity is added to an entity platform
    _added = False

    # Entity Properties
    _attr_assumed_state: bool = False
    _attr_available: bool = True
    _attr_context_recent_time: timedelta = timedelta(seconds=5)
    _attr_device_class: str | None = None
    _attr_device_info: DeviceInfo | None = None
    _attr_entity_picture: str | None = None
    _attr_entity_registry_enabled_default: bool = True
    _attr_extra_state_attributes: Mapping[str, Any] | None = None
    _attr_force_update: bool = False
    _attr_icon: str | None = None
    _attr_name: str | None = None
    _attr_should_poll: bool = True
    _attr_state: StateType = STATE_UNKNOWN
    _attr_supported_features: int | None = None
    _attr_unique_id: str | None = None
    _attr_unit_of_measurement: str | None = None

    @property
    def should_poll(self) -> bool:
        """Return True if entity has to be polled for state.

        False if entity pushes its state to HA.
        """
        return self._attr_should_poll

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return self._attr_unique_id

    @property
    def name(self) -> str | None:
        """Return the name of the entity."""
        return self._attr_name

    @property
    def state(self) -> StateType:
        """Return the state of the entity."""
        return self._attr_state

    @property
    def capability_attributes(self) -> Mapping[str, Any] | None:
        """Return the capability attributes.

        Attributes that explain the capabilities of an entity.

        Implemented by component base class. Convention for attribute names
        is lowercase snake_case.
        """
        return None

    @property
    def state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes.

        Implemented by component base class, should not be extended by integrations.
        Convention for attribute names is lowercase snake_case.
        """
        return None

    @property
    def device_state_attributes(self) -> Mapping[str, Any] | None:
        """Return entity specific state attributes.

        This method is deprecated, platform classes should implement
        extra_state_attributes instead.
        """
        return None

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return entity specific state attributes.

        Implemented by platform classes. Convention for attribute names
        is lowercase snake_case.
        """
        return self._attr_extra_state_attributes

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return device specific attributes.

        Implemented by platform classes.
        """
        return self._attr_device_info

    @property
    def device_class(self) -> str | None:
        """Return the class of this device, from component DEVICE_CLASSES."""
        return self._attr_device_class

    @property
    def unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of this entity, if any."""
        return self._attr_unit_of_measurement

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend, if any."""
        return self._attr_icon

    @property
    def entity_picture(self) -> str | None:
        """Return the entity picture to use in the frontend, if any."""
        return self._attr_entity_picture

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._attr_available

    @property
    def assumed_state(self) -> bool:
        """Return True if unable to access real state of the entity."""
        return self._attr_assumed_state

    @property
    def force_update(self) -> bool:
        """Return True if state updates should be forced.

        If True, a state change will be triggered anytime the state property is
        updated, not just when the value changes.
        """
        return self._attr_force_update

    @property
    def supported_features(self) -> int | None:
        """Flag supported features."""
        return self._attr_supported_features

    @property
    def context_recent_time(self) -> timedelta:
        """Time that a context is considered recent."""
        return self._attr_context_recent_time

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return self._attr_entity_registry_enabled_default

    # DO NOT OVERWRITE
    # These properties and methods are either managed by Open Peer Power or they
    # are used to perform a very specific function. Overwriting these may
    # produce undesirable effects in the entity's operation.

    @property
    def enabled(self) -> bool:
        """Return if the entity is enabled in the entity registry.

        If an entity is not part of the registry, it cannot be disabled
        and will therefore always be enabled.
        """
        return self.registry_entry is None or not self.registry_entry.disabled

    @callback
    def async_set_context(self, context: Context) -> None:
        """Set the context the entity currently operates under."""
        self._context = context
        self._context_set = dt_util.utcnow()

    async def async_update_op_state(self, force_refresh: bool = False) -> None:
        """Update Open Peer Power with current state of entity.

        If force_refresh == True will update entity before setting state.

        This method must be run in the event loop.
        """
        if self.opp is None:
            raise RuntimeError(f"Attribute opp is None for {self}")

        if self.entity_id is None:
            raise NoEntitySpecifiedError(
                f"No entity id specified for entity {self.name}"
            )

        # update entity data
        if force_refresh:
            try:
                await self.async_device_update()
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Update for %s fails", self.entity_id)
                return

        self._async_write_op_state()

    @callback
    def async_write_op_state(self) -> None:
        """Write the state to the state machine."""
        if self.opp is None:
            raise RuntimeError(f"Attribute opp is None for {self}")

        if self.entity_id is None:
            raise NoEntitySpecifiedError(
                f"No entity id specified for entity {self.name}"
            )

        self._async_write_op_state()

    def _stringify_state(self) -> str:
        """Convert state to string."""
        if not self.available:
            return STATE_UNAVAILABLE
        state = self.state
        if state is None:
            return STATE_UNKNOWN
        if isinstance(state, float):
            # If the entity's state is a float, limit precision according to machine
            # epsilon to make the string representation readable
            return f"{state:.{FLOAT_PRECISION}}"
        return str(state)

    @callback
    def _async_write_op_state(self) -> None:
        """Write the state to the state machine."""
        if self.registry_entry and self.registry_entry.disabled_by:
            if not self._disabled_reported:
                self._disabled_reported = True
                assert self.platform is not None
                _LOGGER.warning(
                    "Entity %s is incorrectly being triggered for updates while it is disabled. This is a bug in the %s integration",
                    self.entity_id,
                    self.platform.platform_name,
                )
            return

        start = timer()

        attr = self.capability_attributes
        attr = dict(attr) if attr else {}

        state = self._stringify_state()
        if self.available:
            attr.update(self.state_attributes or {})
            extra_state_attributes = self.extra_state_attributes
            # Backwards compatibility for "device_state_attributes" deprecated in 2021.4
            # Add warning in 2021.6, remove in 2021.10
            if extra_state_attributes is None:
                extra_state_attributes = self.device_state_attributes
            attr.update(extra_state_attributes or {})

        unit_of_measurement = self.unit_of_measurement
        if unit_of_measurement is not None:
            attr[ATTR_UNIT_OF_MEASUREMENT] = unit_of_measurement

        entry = self.registry_entry
        # pylint: disable=consider-using-ternary
        name = (entry and entry.name) or self.name
        if name is not None:
            attr[ATTR_FRIENDLY_NAME] = name

        icon = (entry and entry.icon) or self.icon
        if icon is not None:
            attr[ATTR_ICON] = icon

        entity_picture = self.entity_picture
        if entity_picture is not None:
            attr[ATTR_ENTITY_PICTURE] = entity_picture

        assumed_state = self.assumed_state
        if assumed_state:
            attr[ATTR_ASSUMED_STATE] = assumed_state

        supported_features = self.supported_features
        if supported_features is not None:
            attr[ATTR_SUPPORTED_FEATURES] = supported_features

        device_class = self.device_class
        if device_class is not None:
            attr[ATTR_DEVICE_CLASS] = str(device_class)

        end = timer()

        if end - start > 0.4 and not self._slow_reported:
            self._slow_reported = True
            extra = ""
            if "custom_components" in type(self).__module__:
                extra = "Please report it to the custom component author."
            else:
                extra = (
                    "Please create a bug report at "
                    "https://github.com/openpeerpower/core/issues?q=is%3Aopen+is%3Aissue"
                )
                if self.platform:
                    extra += (
                        f"+label%3A%22integration%3A+{self.platform.platform_name}%22"
                    )

            _LOGGER.warning(
                "Updating state for %s (%s) took %.3f seconds. %s",
                self.entity_id,
                type(self),
                end - start,
                extra,
            )

        # Overwrite properties that have been set in the config file.
        if DATA_CUSTOMIZE in self.opp.data:
            attr.update(self.opp.data[DATA_CUSTOMIZE].get(self.entity_id))

        # Convert temperature if we detect one
        try:
            unit_of_measure = attr.get(ATTR_UNIT_OF_MEASUREMENT)
            units = self.opp.config.units
            if (
                unit_of_measure in (TEMP_CELSIUS, TEMP_FAHRENHEIT)
                and unit_of_measure != units.temperature_unit
            ):
                prec = len(state) - state.index(".") - 1 if "." in state else 0
                temp = units.temperature(float(state), unit_of_measure)
                state = str(round(temp) if prec == 0 else round(temp, prec))
                attr[ATTR_UNIT_OF_MEASUREMENT] = units.temperature_unit
        except ValueError:
            # Could not convert state to float
            pass

        if (
            self._context_set is not None
            and dt_util.utcnow() - self._context_set > self.context_recent_time
        ):
            self._context = None
            self._context_set = None

        self.opp.states.async_set(
            self.entity_id, state, attr, self.force_update, self._context
        )

    def schedule_update_op_state(self, force_refresh: bool = False) -> None:
        """Schedule an update ha state change task.

        Scheduling the update avoids executor deadlocks.

        Entity state and attributes are read when the update ha state change
        task is executed.
        If state is changed more than once before the ha state change task has
        been executed, the intermediate state transitions will be missed.
        """
        self.opp.add_job(self.async_update_op_state(force_refresh))  # type: ignore

    @callback
    def async_schedule_update_op_state(self, force_refresh: bool = False) -> None:
        """Schedule an update ha state change task.

        This method must be run in the event loop.
        Scheduling the update avoids executor deadlocks.

        Entity state and attributes are read when the update ha state change
        task is executed.
        If state is changed more than once before the ha state change task has
        been executed, the intermediate state transitions will be missed.
        """
        if force_refresh:
            self.opp.async_create_task(self.async_update_op_state(force_refresh))
        else:
            self.async_write_op_state()

    async def async_device_update(self, warning: bool = True) -> None:
        """Process 'update' or 'async_update' from entity.

        This method is a coroutine.
        """
        if self._update_staged:
            return
        self._update_staged = True

        # Process update sequential
        if self.parallel_updates:
            await self.parallel_updates.acquire()

        try:
            # pylint: disable=no-member
            if hasattr(self, "async_update"):
                task = self.opp.async_create_task(self.async_update())  # type: ignore
            elif hasattr(self, "update"):
                task = self.opp.async_add_executor_job(self.update)  # type: ignore
            else:
                return

            if not warning:
                await task
                return

            finished, _ = await asyncio.wait([task], timeout=SLOW_UPDATE_WARNING)

            for done in finished:
                exc = done.exception()
                if exc:
                    raise exc
                return

            _LOGGER.warning(
                "Update of %s is taking over %s seconds",
                self.entity_id,
                SLOW_UPDATE_WARNING,
            )
            await task
        finally:
            self._update_staged = False
            if self.parallel_updates:
                self.parallel_updates.release()

    @callback
    def async_on_remove(self, func: CALLBACK_TYPE) -> None:
        """Add a function to call when entity removed."""
        if self._on_remove is None:
            self._on_remove = []
        self._on_remove.append(func)

    async def async_removed_from_registry(self) -> None:
        """Run when entity has been removed from entity registry.

        To be extended by integrations.
        """

    @callback
    def add_to_platform_start(
        self,
        opp: OpenPeerPower,
        platform: EntityPlatform,
        parallel_updates: asyncio.Semaphore | None,
    ) -> None:
        """Start adding an entity to a platform."""
        if self._added:
            raise OpenPeerPowerError(
                f"Entity {self.entity_id} cannot be added a second time to an entity platform"
            )

        self.opp = opp
        self.platform = platform
        self.parallel_updates = parallel_updates
        self._added = True

    @callback
    def add_to_platform_abort(self) -> None:
        """Abort adding an entity to a platform."""
        self.opp = None  # type: ignore
        self.platform = None
        self.parallel_updates = None
        self._added = False

    async def add_to_platform_finish(self) -> None:
        """Finish adding an entity to a platform."""
        await self.async_internal_added_to_opp()
        await self.async_added_to_opp()
        self.async_write_op_state()

    async def async_remove(self, *, force_remove: bool = False) -> None:
        """Remove entity from Open Peer Power.

        If the entity has a non disabled entry in the entity registry,
        the entity's state will be set to unavailable, in the same way
        as when the entity registry is loaded.

        If the entity doesn't have a non disabled entry in the entity registry,
        or if force_remove=True, its state will be removed.
        """
        if self.platform and not self._added:
            raise OpenPeerPowerError(
                f"Entity {self.entity_id} async_remove called twice"
            )

        self._added = False

        if self._on_remove is not None:
            while self._on_remove:
                self._on_remove.pop()()

        await self.async_internal_will_remove_from_opp()
        await self.async_will_remove_from_opp()

        # Check if entry still exists in entity registry (e.g. unloading config entry)
        if (
            not force_remove
            and self.registry_entry
            and not self.registry_entry.disabled
        ):
            # Set the entity's state will to unavailable + ATTR_RESTORED: True
            self.registry_entry.write_unavailable_state(self.opp)
        else:
            self.opp.states.async_remove(self.entity_id, context=self._context)

    async def async_added_to_opp(self) -> None:
        """Run when entity about to be added to opp.

        To be extended by integrations.
        """

    async def async_will_remove_from_opp(self) -> None:
        """Run when entity will be removed from opp.

        To be extended by integrations.
        """

    async def async_internal_added_to_opp(self) -> None:
        """Run when entity about to be added to opp.

        Not to be extended by integrations.
        """
        if self.platform:
            info = {"domain": self.platform.platform_name}

            if self.platform.config_entry:
                info["source"] = SOURCE_CONFIG_ENTRY
                info["config_entry"] = self.platform.config_entry.entry_id
            else:
                info["source"] = SOURCE_PLATFORM_CONFIG

            self.opp.data.setdefault(DATA_ENTITY_SOURCE, {})[self.entity_id] = info

        if self.registry_entry is not None:
            # This is an assert as it should never happen, but helps in tests
            assert (
                not self.registry_entry.disabled_by
            ), f"Entity {self.entity_id} is being added while it's disabled"

            self.async_on_remove(
                async_track_entity_registry_updated_event(
                    self.opp, self.entity_id, self._async_registry_updated
                )
            )

    async def async_internal_will_remove_from_opp(self) -> None:
        """Run when entity will be removed from opp.

        Not to be extended by integrations.
        """
        if self.platform:
            self.opp.data[DATA_ENTITY_SOURCE].pop(self.entity_id)

    async def _async_registry_updated(self, event: Event) -> None:
        """Handle entity registry update."""
        data = event.data
        if data["action"] == "remove":
            await self.async_removed_from_registry()
            self.registry_entry = None
            await self.async_remove()

        if data["action"] != "update":
            return

        ent_reg = await self.opp.helpers.entity_registry.async_get_registry()
        old = self.registry_entry
        self.registry_entry = ent_reg.async_get(data["entity_id"])
        assert self.registry_entry is not None

        if self.registry_entry.disabled:
            await self.async_remove()
            return

        assert old is not None
        if self.registry_entry.entity_id == old.entity_id:
            self.async_write_op_state()
            return

        await self.async_remove(force_remove=True)

        assert self.platform is not None
        self.entity_id = self.registry_entry.entity_id
        await self.platform.async_add_entities([self])

    def __eq__(self, other: Any) -> bool:
        """Return the comparison."""
        if not isinstance(other, self.__class__):
            return False

        # Can only decide equality if both have a unique id
        if self.unique_id is None or other.unique_id is None:
            return False

        # Ensure they belong to the same platform
        if self.platform is not None or other.platform is not None:
            if self.platform is None or other.platform is None:
                return False

            if self.platform.platform != other.platform.platform:
                return False

        return self.unique_id == other.unique_id

    def __repr__(self) -> str:
        """Return the representation."""
        return f"<Entity {self.name}: {self.state}>"

    async def async_request_call(self, coro: Awaitable) -> None:
        """Process request batched."""
        if self.parallel_updates:
            await self.parallel_updates.acquire()

        try:
            await coro
        finally:
            if self.parallel_updates:
                self.parallel_updates.release()


class ToggleEntity(Entity):
    """An abstract class for entities that can be turned on and off."""

    _attr_is_on: bool
    _attr_state: None = None

    @property
    @final
    def state(self) -> str | None:
        """Return the state."""
        return STATE_ON if self.is_on else STATE_OFF

    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        return self._attr_is_on

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        raise NotImplementedError()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self.opp.async_add_executor_job(ft.partial(self.turn_on, **kwargs))

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        raise NotImplementedError()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self.opp.async_add_executor_job(ft.partial(self.turn_off, **kwargs))

    def toggle(self, **kwargs: Any) -> None:
        """Toggle the entity."""
        if self.is_on:
            self.turn_off(**kwargs)
        else:
            self.turn_on(**kwargs)

    async def async_toggle(self, **kwargs: Any) -> None:
        """Toggle the entity."""
        if self.is_on:
            await self.async_turn_off(**kwargs)
        else:
            await self.async_turn_on(**kwargs)
