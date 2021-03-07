"""Class to manage the entities for a single platform."""
from __future__ import annotations

import asyncio
from contextvars import ContextVar
from datetime import datetime, timedelta
from logging import Logger
from types import ModuleType
from typing import TYPE_CHECKING, Callable, Coroutine, Dict, Iterable, List, Optional

from openpeerpower import config_entries
from openpeerpower.const import ATTR_RESTORED, DEVICE_DEFAULT_NAME
from openpeerpower.core import (
    CALLBACK_TYPE,
    ServiceCall,
    callback,
    split_entity_id,
    valid_entity_id,
)
from openpeerpower.exceptions import OpenPeerPowerError, PlatformNotReady
from openpeerpower.helpers import config_validation as cv, service
from openpeerpower.helpers.typing import OpenPeerPowerType
from openpeerpower.util.async_ import run_callback_threadsafe

from .entity_registry import DISABLED_INTEGRATION
from .event import async_call_later, async_track_time_interval

if TYPE_CHECKING:
    from .entity import Entity


SLOW_SETUP_WARNING = 10
SLOW_SETUP_MAX_WAIT = 60
SLOW_ADD_ENTITY_MAX_WAIT = 15  # Per Entity
SLOW_ADD_MIN_TIMEOUT = 500

PLATFORM_NOT_READY_RETRIES = 10
DATA_ENTITY_PLATFORM = "entity_platform"
PLATFORM_NOT_READY_BASE_WAIT_TIME = 30  # seconds


class EntityPlatform:
    """Manage the entities for a single platform."""

    def __init__(
        self,
        *,
        opp: OpenPeerPowerType,
        logger: Logger,
        domain: str,
        platform_name: str,
        platform: Optional[ModuleType],
        scan_interval: timedelta,
        entity_namespace: Optional[str],
    ):
        """Initialize the entity platform."""
        self.opp = opp
        self.logger = logger
        self.domain = domain
        self.platform_name = platform_name
        self.platform = platform
        self.scan_interval = scan_interval
        self.entity_namespace = entity_namespace
        self.config_entry: Optional[config_entries.ConfigEntry] = None
        self.entities: Dict[str, Entity] = {}
        self._tasks: List[asyncio.Future] = []
        # Stop tracking tasks after setup is completed
        self._setup_complete = False
        # Method to cancel the state change listener
        self._async_unsub_polling: Optional[CALLBACK_TYPE] = None
        # Method to cancel the retry of setup
        self._async_cancel_retry_setup: Optional[CALLBACK_TYPE] = None
        self._process_updates: Optional[asyncio.Lock] = None

        self.parallel_updates: Optional[asyncio.Semaphore] = None

        # Platform is None for the EntityComponent "catch-all" EntityPlatform
        # which powers entity_component.add_entities
        self.parallel_updates_created = platform is None

        opp.data.setdefault(DATA_ENTITY_PLATFORM, {}).setdefault(
            self.platform_name, []
        ).append(self)

    def __repr__(self) -> str:
        """Represent an EntityPlatform."""
        return f"<EntityPlatform domain={self.domain} platform_name={self.platform_name} config_entry={self.config_entry}>"

    @callback
    def _get_parallel_updates_semaphore(
        self, entity_has_async_update: bool
    ) -> Optional[asyncio.Semaphore]:
        """Get or create a semaphore for parallel updates.

        Semaphore will be created on demand because we base it off if update method is async or not.

        If parallel updates is set to 0, we skip the semaphore.
        If parallel updates is set to a number, we initialize the semaphore to that number.
        The default value for parallel requests is decided based on the first entity that is added to Open Peer Power.
        It's 0 if the entity defines the async_update method, else it's 1.
        """
        if self.parallel_updates_created:
            return self.parallel_updates

        self.parallel_updates_created = True

        parallel_updates = getattr(self.platform, "PARALLEL_UPDATES", None)

        if parallel_updates is None and not entity_has_async_update:
            parallel_updates = 1

        if parallel_updates == 0:
            parallel_updates = None

        if parallel_updates is not None:
            self.parallel_updates = asyncio.Semaphore(parallel_updates)

        return self.parallel_updates

    async def async_setup(self, platform_config, discovery_info=None):  # type: ignore[no-untyped-def]
        """Set up the platform from a config file."""
        platform = self.platform
        opp = self.opp

        if not hasattr(platform, "async_setup_platform") and not hasattr(
            platform, "setup_platform"
        ):
            self.logger.error(
                "The %s platform for the %s integration does not support platform setup. Please remove it from your config.",
                self.platform_name,
                self.domain,
            )
            return

        @callback
        def async_create_setup_task() -> Coroutine:
            """Get task to set up platform."""
            if getattr(platform, "async_setup_platform", None):
                return platform.async_setup_platform(  # type: ignore
                    opp,
                    platform_config,
                    self._async_schedule_add_entities,
                    discovery_info,
                )

            # This should not be replaced with opp.async_add_job because
            # we don't want to track this task in case it blocks startup.
            return opp.loop.run_in_executor(  # type: ignore[return-value]
                None,
                platform.setup_platform,  # type: ignore
                opp,
                platform_config,
                self._schedule_add_entities,
                discovery_info,
            )

        await self._async_setup_platform(async_create_setup_task)

    async def async_setup_entry(self, config_entry: config_entries.ConfigEntry) -> bool:
        """Set up the platform from a config entry."""
        # Store it so that we can save config entry ID in entity registry
        self.config_entry = config_entry
        platform = self.platform

        @callback
        def async_create_setup_task():  # type: ignore[no-untyped-def]
            """Get task to set up platform."""
            return platform.async_setup_entry(  # type: ignore
                self.opp, config_entry, self._async_schedule_add_entities
            )

        return await self._async_setup_platform(async_create_setup_task)

    async def _async_setup_platform(
        self, async_create_setup_task: Callable[[], Coroutine], tries: int = 0
    ) -> bool:
        """Set up a platform via config file or config entry.

        async_create_setup_task creates a coroutine that sets up platform.
        """
        current_platform.set(self)
        logger = self.logger
        opp = self.opp
        full_name = f"{self.domain}.{self.platform_name}"

        logger.info("Setting up %s", full_name)
        warn_task = opp.loop.call_later(
            SLOW_SETUP_WARNING,
            logger.warning,
            "Setup of %s platform %s is taking over %s seconds.",
            self.domain,
            self.platform_name,
            SLOW_SETUP_WARNING,
        )

        try:
            task = async_create_setup_task()

            async with opp.timeout.async_timeout(SLOW_SETUP_MAX_WAIT, self.domain):
                await asyncio.shield(task)

            # Block till all entities are done
            while self._tasks:
                pending = [task for task in self._tasks if not task.done()]
                self._tasks.clear()

                if pending:
                    await asyncio.gather(*pending)

            opp.config.components.add(full_name)
            self._setup_complete = True
            return True
        except PlatformNotReady:
            tries += 1
            wait_time = min(tries, 6) * PLATFORM_NOT_READY_BASE_WAIT_TIME
            logger.warning(
                "Platform %s not ready yet. Retrying in %d seconds.",
                self.platform_name,
                wait_time,
            )

            async def setup_again(now):  # type: ignore[no-untyped-def]
                """Run setup again."""
                self._async_cancel_retry_setup = None
                await self._async_setup_platform(async_create_setup_task, tries)

            self._async_cancel_retry_setup = async_call_later(
                opp, wait_time, setup_again
            )
            return False
        except asyncio.TimeoutError:
            logger.error(
                "Setup of platform %s is taking longer than %s seconds."
                " Startup will proceed without waiting any longer.",
                self.platform_name,
                SLOW_SETUP_MAX_WAIT,
            )
            return False
        except Exception:  # pylint: disable=broad-except
            logger.exception(
                "Error while setting up %s platform for %s",
                self.platform_name,
                self.domain,
            )
            return False
        finally:
            warn_task.cancel()

    def _schedule_add_entities(
        self, new_entities: Iterable[Entity], update_before_add: bool = False
    ) -> None:
        """Schedule adding entities for a single platform, synchronously."""
        run_callback_threadsafe(
            self.opp.loop,
            self._async_schedule_add_entities,
            list(new_entities),
            update_before_add,
        ).result()

    @callback
    def _async_schedule_add_entities(
        self, new_entities: Iterable[Entity], update_before_add: bool = False
    ) -> None:
        """Schedule adding entities for a single platform async."""
        task = self.opp.async_create_task(
            self.async_add_entities(new_entities, update_before_add=update_before_add),
        )

        if not self._setup_complete:
            self._tasks.append(task)

    def add_entities(
        self, new_entities: Iterable[Entity], update_before_add: bool = False
    ) -> None:
        """Add entities for a single platform."""
        # That avoid deadlocks
        if update_before_add:
            self.logger.warning(
                "Call 'add_entities' with update_before_add=True "
                "only inside tests or you can run into a deadlock!"
            )

        asyncio.run_coroutine_threadsafe(
            self.async_add_entities(list(new_entities), update_before_add),
            self.opp.loop,
        ).result()

    async def async_add_entities(
        self, new_entities: Iterable[Entity], update_before_add: bool = False
    ) -> None:
        """Add entities for a single platform async.

        This method must be run in the event loop.
        """
        # handle empty list from component/platform
        if not new_entities:
            return

        opp = self.opp

        device_registry = await opp.helpers.device_registry.async_get_registry()
        entity_registry = await opp.helpers.entity_registry.async_get_registry()
        tasks = [
            self._async_add_entity(  # type: ignore
                entity, update_before_add, entity_registry, device_registry
            )
            for entity in new_entities
        ]

        # No entities for processing
        if not tasks:
            return

        timeout = max(SLOW_ADD_ENTITY_MAX_WAIT * len(tasks), SLOW_ADD_MIN_TIMEOUT)
        try:
            async with self.opp.timeout.async_timeout(timeout, self.domain):
                await asyncio.gather(*tasks)
        except asyncio.TimeoutError:
            self.logger.warning(
                "Timed out adding entities for domain %s with platform %s after %ds",
                self.domain,
                self.platform_name,
                timeout,
            )
        except Exception:
            self.logger.exception(
                "Error adding entities for domain %s with platform %s",
                self.domain,
                self.platform_name,
            )
            raise

        if self._async_unsub_polling is not None or not any(
            entity.should_poll for entity in self.entities.values()
        ):
            return

        self._async_unsub_polling = async_track_time_interval(
            self.opp,
            self._update_entity_states,
            self.scan_interval,
        )

    async def _async_add_entity(  # type: ignore[no-untyped-def]
        self, entity, update_before_add, entity_registry, device_registry
    ):
        """Add an entity to the platform."""
        if entity is None:
            raise ValueError("Entity cannot be None")

        entity.add_to_platform_start(
            self.opp,
            self,
            self._get_parallel_updates_semaphore(hasattr(entity, "async_update")),
        )

        # Update properties before we generate the entity_id
        if update_before_add:
            try:
                await entity.async_device_update(warning=False)
            except Exception:  # pylint: disable=broad-except
                self.logger.exception("%s: Error on device update!", self.platform_name)
                entity.add_to_platform_abort()
                return

        requested_entity_id = None
        suggested_object_id: Optional[str] = None

        # Get entity_id from unique ID registration
        if entity.unique_id is not None:
            if entity.entity_id is not None:
                requested_entity_id = entity.entity_id
                suggested_object_id = split_entity_id(entity.entity_id)[1]
            else:
                suggested_object_id = entity.name

            if self.entity_namespace is not None:
                suggested_object_id = f"{self.entity_namespace} {suggested_object_id}"

            if self.config_entry is not None:
                config_entry_id: Optional[str] = self.config_entry.entry_id
            else:
                config_entry_id = None

            device_info = entity.device_info
            device_id = None

            if config_entry_id is not None and device_info is not None:
                processed_dev_info = {"config_entry_id": config_entry_id}
                for key in (
                    "connections",
                    "identifiers",
                    "manufacturer",
                    "model",
                    "name",
                    "default_manufacturer",
                    "default_model",
                    "default_name",
                    "sw_version",
                    "entry_type",
                    "via_device",
                    "suggested_area",
                ):
                    if key in device_info:
                        processed_dev_info[key] = device_info[key]

                device = device_registry.async_get_or_create(**processed_dev_info)
                if device:
                    device_id = device.id

            disabled_by: Optional[str] = None
            if not entity.entity_registry_enabled_default:
                disabled_by = DISABLED_INTEGRATION

            entry = entity_registry.async_get_or_create(
                self.domain,
                self.platform_name,
                entity.unique_id,
                suggested_object_id=suggested_object_id,
                config_entry=self.config_entry,
                device_id=device_id,
                known_object_ids=self.entities.keys(),
                disabled_by=disabled_by,
                capabilities=entity.capability_attributes,
                supported_features=entity.supported_features,
                device_class=entity.device_class,
                unit_of_measurement=entity.unit_of_measurement,
                original_name=entity.name,
                original_icon=entity.icon,
            )

            entity.registry_entry = entry
            entity.entity_id = entry.entity_id

            if entry.disabled:
                self.logger.info(
                    "Not adding entity %s because it's disabled",
                    entry.name
                    or entity.name
                    or f'"{self.platform_name} {entity.unique_id}"',
                )
                entity.add_to_platform_abort()
                return

        # We won't generate an entity ID if the platform has already set one
        # We will however make sure that platform cannot pick a registered ID
        elif entity.entity_id is not None and entity_registry.async_is_registered(
            entity.entity_id
        ):
            # If entity already registered, convert entity id to suggestion
            suggested_object_id = split_entity_id(entity.entity_id)[1]
            entity.entity_id = None

        # Generate entity ID
        if entity.entity_id is None:
            suggested_object_id = (
                suggested_object_id or entity.name or DEVICE_DEFAULT_NAME
            )

            if self.entity_namespace is not None:
                suggested_object_id = f"{self.entity_namespace} {suggested_object_id}"
            entity.entity_id = entity_registry.async_generate_entity_id(
                self.domain, suggested_object_id, self.entities.keys()
            )

        # Make sure it is valid in case an entity set the value themselves
        if not valid_entity_id(entity.entity_id):
            entity.add_to_platform_abort()
            raise OpenPeerPowerError(f"Invalid entity ID: {entity.entity_id}")

        already_exists = entity.entity_id in self.entities
        restored = False

        if not already_exists and not self.opp.states.async_available(entity.entity_id):
            existing = self.opp.states.get(entity.entity_id)
            if existing is not None and ATTR_RESTORED in existing.attributes:
                restored = True
            else:
                already_exists = True

        if already_exists:
            if entity.unique_id is not None:
                msg = f"Platform {self.platform_name} does not generate unique IDs. "
                if requested_entity_id:
                    msg += f"ID {entity.unique_id} is already used by {entity.entity_id} - ignoring {requested_entity_id}"
                else:
                    msg += f"ID {entity.unique_id} already exists - ignoring {entity.entity_id}"
            else:
                msg = f"Entity id already exists - ignoring: {entity.entity_id}"
            self.logger.error(msg)
            entity.add_to_platform_abort()
            return

        entity_id = entity.entity_id
        self.entities[entity_id] = entity

        if not restored:
            # Reserve the state in the state machine
            # because as soon as we return control to the event
            # loop below, another entity could be added
            # with the same id before `entity.add_to_platform_finish()`
            # has a chance to finish.
            self.opp.states.async_reserve(entity.entity_id)

        entity.async_on_remove(lambda: self.entities.pop(entity_id))

        await entity.add_to_platform_finish()

    async def async_reset(self) -> None:
        """Remove all entities and reset data.

        This method must be run in the event loop.
        """
        if self._async_cancel_retry_setup is not None:
            self._async_cancel_retry_setup()
            self._async_cancel_retry_setup = None

        if not self.entities:
            return

        tasks = [entity.async_remove() for entity in self.entities.values()]

        await asyncio.gather(*tasks)

        if self._async_unsub_polling is not None:
            self._async_unsub_polling()
            self._async_unsub_polling = None
        self._setup_complete = False

    async def async_destroy(self) -> None:
        """Destroy an entity platform.

        Call before discarding the object.
        """
        await self.async_reset()
        self.opp.data[DATA_ENTITY_PLATFORM][self.platform_name].remove(self)

    async def async_remove_entity(self, entity_id: str) -> None:
        """Remove entity id from platform."""
        await self.entities[entity_id].async_remove()

        # Clean up polling job if no longer needed
        if self._async_unsub_polling is not None and not any(
            entity.should_poll for entity in self.entities.values()
        ):
            self._async_unsub_polling()
            self._async_unsub_polling = None

    async def async_extract_from_service(
        self, service_call: ServiceCall, expand_group: bool = True
    ) -> List[Entity]:
        """Extract all known and available entities from a service call.

        Will return an empty list if entities specified but unknown.

        This method must be run in the event loop.
        """
        return await service.async_extract_entities(
            self.opp, self.entities.values(), service_call, expand_group
        )

    @callback
    def async_register_entity_service(self, name, schema, func, required_features=None):  # type: ignore[no-untyped-def]
        """Register an entity service.

        Services will automatically be shared by all platforms of the same domain.
        """
        if self.opp.services.has_service(self.platform_name, name):
            return

        if isinstance(schema, dict):
            schema = cv.make_entity_service_schema(schema)

        async def handle_service(call: ServiceCall) -> None:
            """Handle the service."""
            await service.entity_service_call(
                self.opp,
                [
                    plf
                    for plf in self.opp.data[DATA_ENTITY_PLATFORM][self.platform_name]
                    if plf.domain == self.domain
                ],
                func,
                call,
                required_features,
            )

        self.opp.services.async_register(
            self.platform_name, name, handle_service, schema
        )

    async def _update_entity_states(self, now: datetime) -> None:
        """Update the states of all the polling entities.

        To protect from flooding the executor, we will update async entities
        in parallel and other entities sequential.

        This method must be run in the event loop.
        """
        if self._process_updates is None:
            self._process_updates = asyncio.Lock()
        if self._process_updates.locked():
            self.logger.warning(
                "Updating %s %s took longer than the scheduled update interval %s",
                self.platform_name,
                self.domain,
                self.scan_interval,
            )
            return

        async with self._process_updates:
            tasks = []
            for entity in self.entities.values():
                if not entity.should_poll:
                    continue
                tasks.append(entity.async_update_op_state(True))

            if tasks:
                await asyncio.gather(*tasks)


current_platform: ContextVar[Optional[EntityPlatform]] = ContextVar(
    "current_platform", default=None
)


@callback
def async_get_platforms(
    opp: OpenPeerPowerType, integration_name: str
) -> List[EntityPlatform]:
    """Find existing platforms."""
    if (
        DATA_ENTITY_PLATFORM not in opp.data
        or integration_name not in opp.data[DATA_ENTITY_PLATFORM]
    ):
        return []

    platforms: List[EntityPlatform] = opp.data[DATA_ENTITY_PLATFORM][integration_name]

    return platforms
