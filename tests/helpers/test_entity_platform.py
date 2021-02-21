"""Tests for the EntityPlatform helper."""
import asyncio
from datetime import timedelta
import logging
from unittest.mock import Mock, patch

import pytest

from openpeerpower.const import PERCENTAGE
from openpeerpowerr.core import callback
from openpeerpowerr.exceptions import OpenPeerPowerError, PlatformNotReady
from openpeerpowerr.helpers import entity_platform, entity_registry
from openpeerpowerr.helpers.entity import async_generate_entity_id
from openpeerpowerr.helpers.entity_component import (
    DEFAULT_SCAN_INTERVAL,
    EntityComponent,
)
import openpeerpowerr.util.dt as dt_util

from tests.common import (
    MockConfigEntry,
    MockEntity,
    MockEntityPlatform,
    MockPlatform,
    async_fire_time_changed,
    mock_entity_platform,
    mock_registry,
)

_LOGGER = logging.getLogger(__name__)
DOMAIN = "test_domain"
PLATFORM = "test_platform"


async def test_polling_only_updates_entities_it_should_poll.opp):
    """Test the polling of only updated entities."""
    component = EntityComponent(_LOGGER, DOMAIN,.opp, timedelta(seconds=20))

    no_poll_ent = MockEntity(should_poll=False)
    no_poll_ent.async_update = Mock()
    poll_ent = MockEntity(should_poll=True)
    poll_ent.async_update = Mock()

    await component.async_add_entities([no_poll_ent, poll_ent])

    no_poll_ent.async_update.reset_mock()
    poll_ent.async_update.reset_mock()

    async_fire_time_changed.opp, dt_util.utcnow() + timedelta(seconds=20))
    await opp.async_block_till_done()

    assert not no_poll_ent.async_update.called
    assert poll_ent.async_update.called


async def test_polling_updates_entities_with_exception.opp):
    """Test the updated entities that not break with an exception."""
    component = EntityComponent(_LOGGER, DOMAIN,.opp, timedelta(seconds=20))

    update_ok = []
    update_err = []

    def update_mock():
        """Mock normal update."""
        update_ok.append(None)

    def update_mock_err():
        """Mock error update."""
        update_err.append(None)
        raise AssertionError("Fake error update")

    ent1 = MockEntity(should_poll=True)
    ent1.update = update_mock_err
    ent2 = MockEntity(should_poll=True)
    ent2.update = update_mock
    ent3 = MockEntity(should_poll=True)
    ent3.update = update_mock
    ent4 = MockEntity(should_poll=True)
    ent4.update = update_mock

    await component.async_add_entities([ent1, ent2, ent3, ent4])

    update_ok.clear()
    update_err.clear()

    async_fire_time_changed.opp, dt_util.utcnow() + timedelta(seconds=20))
    await opp.async_block_till_done()

    assert len(update_ok) == 3
    assert len(update_err) == 1


async def test_update_state_adds_entities.opp):
    """Test if updating poll entities cause an entity to be added works."""
    component = EntityComponent(_LOGGER, DOMAIN,.opp)

    ent1 = MockEntity()
    ent2 = MockEntity(should_poll=True)

    await component.async_add_entities([ent2])
    assert len.opp.states.async_entity_ids()) == 1
    ent2.update = lambda *_: component.add_entities([ent1])

    async_fire_time_changed.opp, dt_util.utcnow() + DEFAULT_SCAN_INTERVAL)
    await opp.async_block_till_done()

    assert len.opp.states.async_entity_ids()) == 2


async def test_update_state_adds_entities_with_update_before_add_true.opp):
    """Test if call update before add to state machine."""
    component = EntityComponent(_LOGGER, DOMAIN,.opp)

    ent = MockEntity()
    ent.update = Mock(spec_set=True)

    await component.async_add_entities([ent], True)
    await opp.async_block_till_done()

    assert len.opp.states.async_entity_ids()) == 1
    assert ent.update.called


async def test_update_state_adds_entities_with_update_before_add_false.opp):
    """Test if not call update before add to state machine."""
    component = EntityComponent(_LOGGER, DOMAIN,.opp)

    ent = MockEntity()
    ent.update = Mock(spec_set=True)

    await component.async_add_entities([ent], False)
    await opp.async_block_till_done()

    assert len.opp.states.async_entity_ids()) == 1
    assert not ent.update.called


@patch("openpeerpowerr.helpers.entity_platform.async_track_time_interval")
async def test_set_scan_interval_via_platform(mock_track,.opp):
    """Test the setting of the scan interval via platform."""

    def platform_setup.opp, config, add_entities, discovery_info=None):
        """Test the platform setup."""
        add_entities([MockEntity(should_poll=True)])

    platform = MockPlatform(platform_setup)
    platform.SCAN_INTERVAL = timedelta(seconds=30)

    mock_entity_platform.opp, "test_domain.platform", platform)

    component = EntityComponent(_LOGGER, DOMAIN,.opp)

    component.setup({DOMAIN: {"platform": "platform"}})

    await opp.async_block_till_done()
    assert mock_track.called
    assert timedelta(seconds=30) == mock_track.call_args[0][2]


async def test_adding_entities_with_generator_and_thread_callback.opp):
    """Test generator in add_entities that calls thread method.

    We should make sure we resolve the generator to a list before passing
    it into an async context.
    """
    component = EntityComponent(_LOGGER, DOMAIN,.opp)

    def create_entity(number):
        """Create entity helper."""
        entity = MockEntity(unique_id=f"unique{number}")
        entity.entity_id = async_generate_entity_id(DOMAIN + ".{}", "Number",.opp.opp)
        return entity

    await component.async_add_entities(create_entity(i) for i in range(2))


async def test_platform_warn_slow_setup.opp):
    """Warn we log when platform setup takes a long time."""
    platform = MockPlatform()

    mock_entity_platform.opp, "test_domain.platform", platform)

    component = EntityComponent(_LOGGER, DOMAIN,.opp)

    with patch.object.opp.loop, "call_later") as mock_call:
        await component.async_setup({DOMAIN: {"platform": "platform"}})
        await opp.async_block_till_done()
        assert mock_call.called

        # mock_calls[0] is the warning message for component setup
        # mock_calls[4] is the warning message for platform setup
        timeout, logger_method = mock_call.mock_calls[4][1][:2]

        assert timeout == entity_platform.SLOW_SETUP_WARNING
        assert logger_method == _LOGGER.warning

        assert mock_call().cancel.called


async def test_platform_error_slow_setup.opp, caplog):
    """Don't block startup more than SLOW_SETUP_MAX_WAIT."""
    with patch.object(entity_platform, "SLOW_SETUP_MAX_WAIT", 0):
        called = []

        async def setup_platform(*args):
            called.append(1)
            await asyncio.sleep(1)

        platform = MockPlatform(async_setup_platform=setup_platform)
        component = EntityComponent(_LOGGER, DOMAIN,.opp)
        mock_entity_platform.opp, "test_domain.test_platform", platform)
        await component.async_setup({DOMAIN: {"platform": "test_platform"}})
        await opp.async_block_till_done()
        assert len(called) == 1
        assert "test_domain.test_platform" not in.opp.config.components
        assert "test_platform is taking longer than 0 seconds" in caplog.text


async def test_updated_state_used_for_entity_id.opp):
    """Test that first update results used for entity ID generation."""
    component = EntityComponent(_LOGGER, DOMAIN,.opp)

    class MockEntityNameFetcher(MockEntity):
        """Mock entity that fetches a friendly name."""

        async def async_update(self):
            """Mock update that assigns a name."""
            self._values["name"] = "Living Room"

    await component.async_add_entities([MockEntityNameFetcher()], True)

    entity_ids = opp.states.async_entity_ids()
    assert len(entity_ids) == 1
    assert entity_ids[0] == "test_domain.living_room"


async def test_parallel_updates_async_platform.opp):
    """Test async platform does not have parallel_updates limit by default."""
    platform = MockPlatform()

    mock_entity_platform.opp, "test_domain.platform", platform)

    component = EntityComponent(_LOGGER, DOMAIN,.opp)
    component._platforms = {}

    await component.async_setup({DOMAIN: {"platform": "platform"}})
    await opp.async_block_till_done()

    handle = list(component._platforms.values())[-1]
    assert handle.parallel_updates is None

    class AsyncEntity(MockEntity):
        """Mock entity that has async_update."""

        async def async_update(self):
            pass

    entity = AsyncEntity()
    await handle.async_add_entities([entity])
    assert entity.parallel_updates is None


async def test_parallel_updates_async_platform_with_constant.opp):
    """Test async platform can set parallel_updates limit."""
    platform = MockPlatform()
    platform.PARALLEL_UPDATES = 2

    mock_entity_platform.opp, "test_domain.platform", platform)

    component = EntityComponent(_LOGGER, DOMAIN,.opp)
    component._platforms = {}

    await component.async_setup({DOMAIN: {"platform": "platform"}})
    await opp.async_block_till_done()

    handle = list(component._platforms.values())[-1]

    class AsyncEntity(MockEntity):
        """Mock entity that has async_update."""

        async def async_update(self):
            pass

    entity = AsyncEntity()
    await handle.async_add_entities([entity])
    assert entity.parallel_updates is not None
    assert entity.parallel_updates._value == 2


async def test_parallel_updates_sync_platform.opp):
    """Test sync platform parallel_updates default set to 1."""
    platform = MockPlatform()

    mock_entity_platform.opp, "test_domain.platform", platform)

    component = EntityComponent(_LOGGER, DOMAIN,.opp)
    component._platforms = {}

    await component.async_setup({DOMAIN: {"platform": "platform"}})
    await opp.async_block_till_done()

    handle = list(component._platforms.values())[-1]

    class SyncEntity(MockEntity):
        """Mock entity that has update."""

        async def update(self):
            pass

    entity = SyncEntity()
    await handle.async_add_entities([entity])
    assert entity.parallel_updates is not None
    assert entity.parallel_updates._value == 1


async def test_parallel_updates_sync_platform_with_constant.opp):
    """Test sync platform can set parallel_updates limit."""
    platform = MockPlatform()
    platform.PARALLEL_UPDATES = 2

    mock_entity_platform.opp, "test_domain.platform", platform)

    component = EntityComponent(_LOGGER, DOMAIN,.opp)
    component._platforms = {}

    await component.async_setup({DOMAIN: {"platform": "platform"}})
    await opp.async_block_till_done()

    handle = list(component._platforms.values())[-1]

    class SyncEntity(MockEntity):
        """Mock entity that has update."""

        async def update(self):
            pass

    entity = SyncEntity()
    await handle.async_add_entities([entity])
    assert entity.parallel_updates is not None
    assert entity.parallel_updates._value == 2


async def test_raise_error_on_update.opp):
    """Test the add entity if they raise an error on update."""
    updates = []
    component = EntityComponent(_LOGGER, DOMAIN,.opp)
    entity1 = MockEntity(name="test_1")
    entity2 = MockEntity(name="test_2")

    def _raise():
        """Raise an exception."""
        raise AssertionError

    entity1.update = _raise
    entity2.update = lambda: updates.append(1)

    await component.async_add_entities([entity1, entity2], True)

    assert len(updates) == 1
    assert 1 in updates

    assert entity1.opp is None
    assert entity1.platform is None
    assert entity2.opp is not None
    assert entity2.platform is not None


async def test_async_remove_with_platform.opp):
    """Remove an entity from a platform."""
    component = EntityComponent(_LOGGER, DOMAIN,.opp)
    entity1 = MockEntity(name="test_1")
    await component.async_add_entities([entity1])
    assert len.opp.states.async_entity_ids()) == 1
    await entity1.async_remove()
    assert len.opp.states.async_entity_ids()) == 0


async def test_not_adding_duplicate_entities_with_unique_id.opp, caplog):
    """Test for not adding duplicate entities."""
    caplog.set_level(logging.ERROR)
    component = EntityComponent(_LOGGER, DOMAIN,.opp)

    await component.async_add_entities(
        [MockEntity(name="test1", unique_id="not_very_unique")]
    )

    assert len.opp.states.async_entity_ids()) == 1
    assert not caplog.text

    ent2 = MockEntity(name="test2", unique_id="not_very_unique")
    await component.async_add_entities([ent2])
    assert "test1" in caplog.text
    assert DOMAIN in caplog.text

    ent3 = MockEntity(
        name="test2", entity_id="test_domain.test3", unique_id="not_very_unique"
    )
    await component.async_add_entities([ent3])
    assert "test1" in caplog.text
    assert "test3" in caplog.text
    assert DOMAIN in caplog.text

    assert ent2.opp is None
    assert ent2.platform is None
    assert len.opp.states.async_entity_ids()) == 1


async def test_using_prescribed_entity_id.opp):
    """Test for using predefined entity ID."""
    component = EntityComponent(_LOGGER, DOMAIN,.opp)
    await component.async_add_entities(
        [MockEntity(name="bla", entity_id="hello.world")]
    )
    assert "hello.world" in.opp.states.async_entity_ids()


async def test_using_prescribed_entity_id_with_unique_id.opp):
    """Test for amending predefined entity ID because currently exists."""
    component = EntityComponent(_LOGGER, DOMAIN,.opp)

    await component.async_add_entities([MockEntity(entity_id="test_domain.world")])
    await component.async_add_entities(
        [MockEntity(entity_id="test_domain.world", unique_id="bla")]
    )

    assert "test_domain.world_2" in.opp.states.async_entity_ids()


async def test_using_prescribed_entity_id_which_is_registered.opp):
    """Test not allowing predefined entity ID that already registered."""
    component = EntityComponent(_LOGGER, DOMAIN,.opp)
    registry = mock_registry.opp)
    # Register test_domain.world
    registry.async_get_or_create(DOMAIN, "test", "1234", suggested_object_id="world")

    # This entity_id will be rewritten
    await component.async_add_entities([MockEntity(entity_id="test_domain.world")])

    assert "test_domain.world_2" in.opp.states.async_entity_ids()


async def test_name_which_conflict_with_registered.opp):
    """Test not generating conflicting entity ID based on name."""
    component = EntityComponent(_LOGGER, DOMAIN,.opp)
    registry = mock_registry.opp)

    # Register test_domain.world
    registry.async_get_or_create(DOMAIN, "test", "1234", suggested_object_id="world")

    await component.async_add_entities([MockEntity(name="world")])

    assert "test_domain.world_2" in.opp.states.async_entity_ids()


async def test_entity_with_name_and_entity_id_getting_registered.opp):
    """Ensure that entity ID is used for registration."""
    component = EntityComponent(_LOGGER, DOMAIN,.opp)
    await component.async_add_entities(
        [MockEntity(unique_id="1234", name="bla", entity_id="test_domain.world")]
    )
    assert "test_domain.world" in.opp.states.async_entity_ids()


async def test_overriding_name_from_registry.opp):
    """Test that we can override a name via the Entity Registry."""
    component = EntityComponent(_LOGGER, DOMAIN,.opp)
    mock_registry(
       .opp,
        {
            "test_domain.world": entity_registry.RegistryEntry(
                entity_id="test_domain.world",
                unique_id="1234",
                # Using component.async_add_entities is equal to platform "domain"
                platform="test_domain",
                name="Overridden",
            )
        },
    )
    await component.async_add_entities(
        [MockEntity(unique_id="1234", name="Device Name")]
    )

    state = opp.states.get("test_domain.world")
    assert state is not None
    assert state.name == "Overridden"


async def test_registry_respect_entity_namespace.opp):
    """Test that the registry respects entity namespace."""
    mock_registry.opp)
    platform = MockEntityPlatform.opp, entity_namespace="ns")
    entity = MockEntity(unique_id="1234", name="Device Name")
    await platform.async_add_entities([entity])
    assert entity.entity_id == "test_domain.ns_device_name"


async def test_registry_respect_entity_disabled.opp):
    """Test that the registry respects entity disabled."""
    mock_registry(
       .opp,
        {
            "test_domain.world": entity_registry.RegistryEntry(
                entity_id="test_domain.world",
                unique_id="1234",
                # Using component.async_add_entities is equal to platform "domain"
                platform="test_platform",
                disabled_by=entity_registry.DISABLED_USER,
            )
        },
    )
    platform = MockEntityPlatform.opp)
    entity = MockEntity(unique_id="1234")
    await platform.async_add_entities([entity])
    assert entity.entity_id == "test_domain.world"
    assert.opp.states.async_entity_ids() == []


async def test_entity_registry_updates_name.opp):
    """Test that updates on the entity registry update platform entities."""
    registry = mock_registry(
       .opp,
        {
            "test_domain.world": entity_registry.RegistryEntry(
                entity_id="test_domain.world",
                unique_id="1234",
                # Using component.async_add_entities is equal to platform "domain"
                platform="test_platform",
                name="before update",
            )
        },
    )
    platform = MockEntityPlatform.opp)
    entity = MockEntity(unique_id="1234")
    await platform.async_add_entities([entity])

    state = opp.states.get("test_domain.world")
    assert state is not None
    assert state.name == "before update"

    registry.async_update_entity("test_domain.world", name="after update")
    await opp.async_block_till_done()
    await opp.async_block_till_done()

    state = opp.states.get("test_domain.world")
    assert state.name == "after update"


async def test_setup_entry.opp):
    """Test we can setup an entry."""
    registry = mock_registry.opp)

    async def async_setup_entry.opp, config_entry, async_add_entities):
        """Mock setup entry method."""
        async_add_entities([MockEntity(name="test1", unique_id="unique")])
        return True

    platform = MockPlatform(async_setup_entry=async_setup_entry)
    config_entry = MockConfigEntry(entry_id="super-mock-id")
    entity_platform = MockEntityPlatform(
       .opp, platform_name=config_entry.domain, platform=platform
    )

    assert await entity_platform.async_setup_entry(config_entry)
    await opp.async_block_till_done()
    full_name = f"{entity_platform.domain}.{config_entry.domain}"
    assert full_name in.opp.config.components
    assert len.opp.states.async_entity_ids()) == 1
    assert len(registry.entities) == 1
    assert registry.entities["test_domain.test1"].config_entry_id == "super-mock-id"


async def test_setup_entry_platform_not_ready.opp, caplog):
    """Test when an entry is not ready yet."""
    async_setup_entry = Mock(side_effect=PlatformNotReady)
    platform = MockPlatform(async_setup_entry=async_setup_entry)
    config_entry = MockConfigEntry()
    ent_platform = MockEntityPlatform(
       .opp, platform_name=config_entry.domain, platform=platform
    )

    with patch.object(entity_platform, "async_call_later") as mock_call_later:
        assert not await ent_platform.async_setup_entry(config_entry)

    full_name = f"{ent_platform.domain}.{config_entry.domain}"
    assert full_name not in.opp.config.components
    assert len(async_setup_entry.mock_calls) == 1
    assert "Platform test not ready yet" in caplog.text
    assert len(mock_call_later.mock_calls) == 1


async def test_reset_cancels_retry_setup.opp):
    """Test that resetting a platform will cancel scheduled a setup retry."""
    async_setup_entry = Mock(side_effect=PlatformNotReady)
    platform = MockPlatform(async_setup_entry=async_setup_entry)
    config_entry = MockConfigEntry()
    ent_platform = MockEntityPlatform(
       .opp, platform_name=config_entry.domain, platform=platform
    )

    with patch.object(entity_platform, "async_call_later") as mock_call_later:
        assert not await ent_platform.async_setup_entry(config_entry)

    assert len(mock_call_later.mock_calls) == 1
    assert len(mock_call_later.return_value.mock_calls) == 0
    assert ent_platform._async_cancel_retry_setup is not None

    await ent_platform.async_reset()

    assert len(mock_call_later.return_value.mock_calls) == 1
    assert ent_platform._async_cancel_retry_setup is None


async def test_not_fails_with_adding_empty_entities_.opp):
    """Test for not fails on empty entities list."""
    component = EntityComponent(_LOGGER, DOMAIN,.opp)

    await component.async_add_entities([])

    assert len.opp.states.async_entity_ids()) == 0


async def test_entity_registry_updates_entity_id.opp):
    """Test that updates on the entity registry update platform entities."""
    registry = mock_registry(
       .opp,
        {
            "test_domain.world": entity_registry.RegistryEntry(
                entity_id="test_domain.world",
                unique_id="1234",
                # Using component.async_add_entities is equal to platform "domain"
                platform="test_platform",
                name="Some name",
            )
        },
    )
    platform = MockEntityPlatform.opp)
    entity = MockEntity(unique_id="1234")
    await platform.async_add_entities([entity])

    state = opp.states.get("test_domain.world")
    assert state is not None
    assert state.name == "Some name"

    registry.async_update_entity(
        "test_domain.world", new_entity_id="test_domain.planet"
    )
    await opp.async_block_till_done()
    await opp.async_block_till_done()

    assert.opp.states.get("test_domain.world") is None
    assert.opp.states.get("test_domain.planet") is not None


async def test_entity_registry_updates_invalid_entity_id.opp):
    """Test that we can't update to an invalid entity id."""
    registry = mock_registry(
       .opp,
        {
            "test_domain.world": entity_registry.RegistryEntry(
                entity_id="test_domain.world",
                unique_id="1234",
                # Using component.async_add_entities is equal to platform "domain"
                platform="test_platform",
                name="Some name",
            ),
            "test_domain.existing": entity_registry.RegistryEntry(
                entity_id="test_domain.existing",
                unique_id="5678",
                platform="test_platform",
            ),
        },
    )
    platform = MockEntityPlatform.opp)
    entity = MockEntity(unique_id="1234")
    await platform.async_add_entities([entity])

    state = opp.states.get("test_domain.world")
    assert state is not None
    assert state.name == "Some name"

    with pytest.raises(ValueError):
        registry.async_update_entity(
            "test_domain.world", new_entity_id="test_domain.existing"
        )

    with pytest.raises(ValueError):
        registry.async_update_entity(
            "test_domain.world", new_entity_id="invalid_entity_id"
        )

    with pytest.raises(ValueError):
        registry.async_update_entity(
            "test_domain.world", new_entity_id="diff_domain.world"
        )

    await opp.async_block_till_done()
    await opp.async_block_till_done()

    assert.opp.states.get("test_domain.world") is not None
    assert.opp.states.get("invalid_entity_id") is None
    assert.opp.states.get("diff_domain.world") is None


async def test_device_info_called.opp):
    """Test device info is forwarded correctly."""
    registry = await.opp.helpers.device_registry.async_get_registry()
    via = registry.async_get_or_create(
        config_entry_id="123",
        connections=set(),
        identifiers={("hue", "via-id")},
        manufacturer="manufacturer",
        model="via",
    )

    async def async_setup_entry.opp, config_entry, async_add_entities):
        """Mock setup entry method."""
        async_add_entities(
            [
                # Invalid device info
                MockEntity(unique_id="abcd", device_info={}),
                # Valid device info
                MockEntity(
                    unique_id="qwer",
                    device_info={
                        "identifiers": {("hue", "1234")},
                        "connections": {("mac", "abcd")},
                        "manufacturer": "test-manuf",
                        "model": "test-model",
                        "name": "test-name",
                        "sw_version": "test-sw",
                        "entry_type": "service",
                        "via_device": ("hue", "via-id"),
                    },
                ),
            ]
        )
        return True

    platform = MockPlatform(async_setup_entry=async_setup_entry)
    config_entry = MockConfigEntry(entry_id="super-mock-id")
    entity_platform = MockEntityPlatform(
       .opp, platform_name=config_entry.domain, platform=platform
    )

    assert await entity_platform.async_setup_entry(config_entry)
    await opp.async_block_till_done()

    assert len.opp.states.async_entity_ids()) == 2

    device = registry.async_get_device({("hue", "1234")})
    assert device is not None
    assert device.identifiers == {("hue", "1234")}
    assert device.connections == {("mac", "abcd")}
    assert device.manufacturer == "test-manuf"
    assert device.model == "test-model"
    assert device.name == "test-name"
    assert device.sw_version == "test-sw"
    assert device.entry_type == "service"
    assert device.via_device_id == via.id


async def test_device_info_not_overrides.opp):
    """Test device info is forwarded correctly."""
    registry = await.opp.helpers.device_registry.async_get_registry()
    device = registry.async_get_or_create(
        config_entry_id="bla",
        connections={("mac", "abcd")},
        manufacturer="test-manufacturer",
        model="test-model",
    )

    assert device.manufacturer == "test-manufacturer"
    assert device.model == "test-model"

    async def async_setup_entry.opp, config_entry, async_add_entities):
        """Mock setup entry method."""
        async_add_entities(
            [
                MockEntity(
                    unique_id="qwer",
                    device_info={
                        "connections": {("mac", "abcd")},
                        "default_name": "default name 1",
                        "default_model": "default model 1",
                        "default_manufacturer": "default manufacturer 1",
                    },
                )
            ]
        )
        return True

    platform = MockPlatform(async_setup_entry=async_setup_entry)
    config_entry = MockConfigEntry(entry_id="super-mock-id")
    entity_platform = MockEntityPlatform(
       .opp, platform_name=config_entry.domain, platform=platform
    )

    assert await entity_platform.async_setup_entry(config_entry)
    await opp.async_block_till_done()

    device2 = registry.async_get_device(set(), {("mac", "abcd")})
    assert device2 is not None
    assert device.id == device2.id
    assert device2.manufacturer == "test-manufacturer"
    assert device2.model == "test-model"


async def test_entity_disabled_by_integration.opp):
    """Test entity disabled by integration."""
    component = EntityComponent(_LOGGER, DOMAIN,.opp, timedelta(seconds=20))

    entity_default = MockEntity(unique_id="default")
    entity_disabled = MockEntity(
        unique_id="disabled", entity_registry_enabled_default=False
    )

    await component.async_add_entities([entity_default, entity_disabled])

    assert entity_default.opp is not None
    assert entity_default.platform is not None
    assert entity_disabled.opp is None
    assert entity_disabled.platform is None

    registry = await.opp.helpers.entity_registry.async_get_registry()

    entry_default = registry.async_get_or_create(DOMAIN, DOMAIN, "default")
    assert entry_default.disabled_by is None
    entry_disabled = registry.async_get_or_create(DOMAIN, DOMAIN, "disabled")
    assert entry_disabled.disabled_by == "integration"


async def test_entity_info_added_to_entity_registry.opp):
    """Test entity info is written to entity registry."""
    component = EntityComponent(_LOGGER, DOMAIN,.opp, timedelta(seconds=20))

    entity_default = MockEntity(
        unique_id="default",
        capability_attributes={"max": 100},
        supported_features=5,
        device_class="mock-device-class",
        unit_of_measurement=PERCENTAGE,
    )

    await component.async_add_entities([entity_default])

    registry = await.opp.helpers.entity_registry.async_get_registry()

    entry_default = registry.async_get_or_create(DOMAIN, DOMAIN, "default")
    print(entry_default)
    assert entry_default.capabilities == {"max": 100}
    assert entry_default.supported_features == 5
    assert entry_default.device_class == "mock-device-class"
    assert entry_default.unit_of_measurement == PERCENTAGE


async def test_override_restored_entities.opp):
    """Test that we allow overriding restored entities."""
    registry = mock_registry.opp)
    registry.async_get_or_create(
        "test_domain", "test_domain", "1234", suggested_object_id="world"
    )

   .opp.states.async_set("test_domain.world", "unavailable", {"restored": True})

    component = EntityComponent(_LOGGER, DOMAIN,.opp)

    await component.async_add_entities(
        [MockEntity(unique_id="1234", state="on", entity_id="test_domain.world")], True
    )

    state = opp.states.get("test_domain.world")
    assert state.state == "on"


async def test_platform_with_no_setup.opp, caplog):
    """Test setting up a platform that does not support setup."""
    entity_platform = MockEntityPlatform(
       .opp, domain="mock-integration", platform_name="mock-platform", platform=None
    )

    await entity_platform.async_setup(None)

    assert (
        "The mock-platform platform for the mock-integration integration does not support platform setup."
        in caplog.text
    )


async def test_platforms_sharing_services.opp):
    """Test platforms share services."""
    entity_platform1 = MockEntityPlatform(
       .opp, domain="mock_integration", platform_name="mock_platform", platform=None
    )
    entity1 = MockEntity(entity_id="mock_integration.entity_1")
    await entity_platform1.async_add_entities([entity1])

    entity_platform2 = MockEntityPlatform(
       .opp, domain="mock_integration", platform_name="mock_platform", platform=None
    )
    entity2 = MockEntity(entity_id="mock_integration.entity_2")
    await entity_platform2.async_add_entities([entity2])

    entity_platform3 = MockEntityPlatform(
       .opp,
        domain="different_integration",
        platform_name="mock_platform",
        platform=None,
    )
    entity3 = MockEntity(entity_id="different_integration.entity_3")
    await entity_platform3.async_add_entities([entity3])

    entities = []

    @callback
    def handle_service(entity, data):
        entities.append(entity)

    entity_platform1.async_register_entity_service("hello", {}, handle_service)
    entity_platform2.async_register_entity_service(
        "hello", {}, Mock(side_effect=AssertionError("Should not be called"))
    )

    await.opp.services.async_call(
        "mock_platform", "hello", {"entity_id": "all"}, blocking=True
    )

    assert len(entities) == 2
    assert entity1 in entities
    assert entity2 in entities


async def test_invalid_entity_id.opp):
    """Test specifying an invalid entity id."""
    platform = MockEntityPlatform.opp)
    entity = MockEntity(entity_id="invalid_entity_id")
    with pytest.raises(OpenPeerPowerError):
        await platform.async_add_entities([entity])
    assert entity.opp is None
    assert entity.platform is None


class MockBlockingEntity(MockEntity):
    """Class to mock an entity that will block adding entities."""

    async def async_added_to_opp(self):
        """Block for a long time."""
        await asyncio.sleep(1000)


async def test_setup_entry_with_entities_that_block_forever.opp, caplog):
    """Test we cancel adding entities when we reach the timeout."""
    registry = mock_registry.opp)

    async def async_setup_entry.opp, config_entry, async_add_entities):
        """Mock setup entry method."""
        async_add_entities([MockBlockingEntity(name="test1", unique_id="unique")])
        return True

    platform = MockPlatform(async_setup_entry=async_setup_entry)
    config_entry = MockConfigEntry(entry_id="super-mock-id")
    mock_entity_platform = MockEntityPlatform(
       .opp, platform_name=config_entry.domain, platform=platform
    )

    with patch.object(entity_platform, "SLOW_ADD_ENTITY_MAX_WAIT", 0.01), patch.object(
        entity_platform, "SLOW_ADD_MIN_TIMEOUT", 0.01
    ):
        assert await mock_entity_platform.async_setup_entry(config_entry)
        await opp.async_block_till_done()
    full_name = f"{mock_entity_platform.domain}.{config_entry.domain}"
    assert full_name in.opp.config.components
    assert len.opp.states.async_entity_ids()) == 0
    assert len(registry.entities) == 1
    assert "Timed out adding entities" in caplog.text
    assert "test_domain.test1" in caplog.text
    assert "test_domain" in caplog.text
    assert "test" in caplog.text


async def test_two_platforms_add_same_entity.opp):
    """Test two platforms in the same domain adding an entity with the same name."""
    entity_platform1 = MockEntityPlatform(
       .opp, domain="mock_integration", platform_name="mock_platform", platform=None
    )
    entity1 = SlowEntity(name="entity_1")

    entity_platform2 = MockEntityPlatform(
       .opp, domain="mock_integration", platform_name="mock_platform", platform=None
    )
    entity2 = SlowEntity(name="entity_1")

    await asyncio.gather(
        entity_platform1.async_add_entities([entity1]),
        entity_platform2.async_add_entities([entity2]),
    )

    entities = []

    @callback
    def handle_service(entity, *_):
        entities.append(entity)

    entity_platform1.async_register_entity_service("hello", {}, handle_service)
    await.opp.services.async_call(
        "mock_platform", "hello", {"entity_id": "all"}, blocking=True
    )

    assert len(entities) == 2
    assert {entity1.entity_id, entity2.entity_id} == {
        "mock_integration.entity_1",
        "mock_integration.entity_1_2",
    }
    assert entity1 in entities
    assert entity2 in entities


class SlowEntity(MockEntity):
    """An entity that will sleep during add."""

    async def async_added_to_opp(self):
        """Make sure control is returned to the event loop on add."""
        await asyncio.sleep(0.1)
        await super().async_added_to_opp()
