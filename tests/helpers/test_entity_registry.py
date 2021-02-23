"""Tests for the Entity Registry."""
from unittest.mock import patch

import pytest

from openpeerpower.const import EVENT_OPENPEERPOWER_START, STATE_UNAVAILABLE
from openpeerpower.core import CoreState, callback, valid_entity_id
from openpeerpower.helpers import entity_registry

from tests.common import (
    MockConfigEntry,
    flush_store,
    mock_device_registry,
    mock_registry,
)

YAML__OPEN_PATH = "openpeerpower.util.yaml.loader.open"


@pytest.fixture
def registry.opp):
    """Return an empty, loaded, registry."""
    return mock_registry.opp)


@pytest.fixture
def update_events.opp):
    """Capture update events."""
    events = []

    @callback
    def async_capture(event):
        events.append(event.data)

    opp.bus.async_listen(entity_registry.EVENT_ENTITY_REGISTRY_UPDATED, async_capture)

    return events


async def test_get_or_create_returns_same_entry.opp, registry, update_events):
    """Make sure we do not duplicate entries."""
    entry = registry.async_get_or_create("light", "hue", "1234")
    entry2 = registry.async_get_or_create("light", "hue", "1234")

    await opp.async_block_till_done()

    assert len(registry.entities) == 1
    assert entry is entry2
    assert entry.entity_id == "light.hue_1234"
    assert len(update_events) == 1
    assert update_events[0]["action"] == "create"
    assert update_events[0]["entity_id"] == entry.entity_id


def test_get_or_create_suggested_object_id(registry):
    """Test that suggested_object_id works."""
    entry = registry.async_get_or_create(
        "light", "hue", "1234", suggested_object_id="beer"
    )

    assert entry.entity_id == "light.beer"


def test_get_or_create_updates_data(registry):
    """Test that we update data in get_or_create."""
    orig_config_entry = MockConfigEntry(domain="light")

    orig_entry = registry.async_get_or_create(
        "light",
        "hue",
        "5678",
        config_entry=orig_config_entry,
        device_id="mock-dev-id",
        capabilities={"max": 100},
        supported_features=5,
        device_class="mock-device-class",
        disabled_by=entity_registry.DISABLED_OPP,
        unit_of_measurement="initial-unit_of_measurement",
        original_name="initial-original_name",
        original_icon="initial-original_icon",
    )

    assert orig_entry.config_entry_id == orig_config_entry.entry_id
    assert orig_entry.device_id == "mock-dev-id"
    assert orig_entry.capabilities == {"max": 100}
    assert orig_entry.supported_features == 5
    assert orig_entry.device_class == "mock-device-class"
    assert orig_entry.disabled_by == entity_registry.DISABLED_OPP
    assert orig_entry.unit_of_measurement == "initial-unit_of_measurement"
    assert orig_entry.original_name == "initial-original_name"
    assert orig_entry.original_icon == "initial-original_icon"

    new_config_entry = MockConfigEntry(domain="light")

    new_entry = registry.async_get_or_create(
        "light",
        "hue",
        "5678",
        config_entry=new_config_entry,
        device_id="new-mock-dev-id",
        capabilities={"new-max": 100},
        supported_features=10,
        device_class="new-mock-device-class",
        disabled_by=entity_registry.DISABLED_USER,
        unit_of_measurement="updated-unit_of_measurement",
        original_name="updated-original_name",
        original_icon="updated-original_icon",
    )

    assert new_entry.config_entry_id == new_config_entry.entry_id
    assert new_entry.device_id == "new-mock-dev-id"
    assert new_entry.capabilities == {"new-max": 100}
    assert new_entry.supported_features == 10
    assert new_entry.device_class == "new-mock-device-class"
    assert new_entry.unit_of_measurement == "updated-unit_of_measurement"
    assert new_entry.original_name == "updated-original_name"
    assert new_entry.original_icon == "updated-original_icon"
    # Should not be updated
    assert new_entry.disabled_by == entity_registry.DISABLED_OPP


def test_get_or_create_suggested_object_id_conflict_register(registry):
    """Test that we don't generate an entity id that is already registered."""
    entry = registry.async_get_or_create(
        "light", "hue", "1234", suggested_object_id="beer"
    )
    entry2 = registry.async_get_or_create(
        "light", "hue", "5678", suggested_object_id="beer"
    )

    assert entry.entity_id == "light.beer"
    assert entry2.entity_id == "light.beer_2"


def test_get_or_create_suggested_object_id_conflict_existing.opp, registry):
    """Test that we don't generate an entity id that currently exists."""
    opp.states.async_set("light.hue_1234", "on")
    entry = registry.async_get_or_create("light", "hue", "1234")
    assert entry.entity_id == "light.hue_1234_2"


def test_create_triggers_save.opp, registry):
    """Test that registering entry triggers a save."""
    with patch.object(registry, "async_schedule_save") as mock_schedule_save:
        registry.async_get_or_create("light", "hue", "1234")

    assert len(mock_schedule_save.mock_calls) == 1


async def test_loading_saving_data.opp, registry):
    """Test that we load/save data correctly."""
    mock_config = MockConfigEntry(domain="light")

    orig_entry1 = registry.async_get_or_create("light", "hue", "1234")
    orig_entry2 = registry.async_get_or_create(
        "light",
        "hue",
        "5678",
        device_id="mock-dev-id",
        area_id="mock-area-id",
        config_entry=mock_config,
        capabilities={"max": 100},
        supported_features=5,
        device_class="mock-device-class",
        disabled_by=entity_registry.DISABLED_OPP,
        original_name="Original Name",
        original_icon= opp:original-icon",
    )
    orig_entry2 = registry.async_update_entity(
        orig_entry2.entity_id, name="User Name", icon= opp:user-icon"
    )

    assert len(registry.entities) == 2

    # Now load written data in new registry
    registry2 = entity_registry.EntityRegistry.opp)
    await flush_store(registry._store)
    await registry2.async_load()

    # Ensure same order
    assert list(registry.entities) == list(registry2.entities)
    new_entry1 = registry.async_get_or_create("light", "hue", "1234")
    new_entry2 = registry.async_get_or_create("light", "hue", "5678")

    assert orig_entry1 == new_entry1
    assert orig_entry2 == new_entry2

    assert new_entry2.device_id == "mock-dev-id"
    assert new_entry2.area_id == "mock-area-id"
    assert new_entry2.disabled_by == entity_registry.DISABLED_OPP
    assert new_entry2.capabilities == {"max": 100}
    assert new_entry2.supported_features == 5
    assert new_entry2.device_class == "mock-device-class"
    assert new_entry2.name == "User Name"
    assert new_entry2.icon == opp:user-icon"
    assert new_entry2.original_name == "Original Name"
    assert new_entry2.original_icon == opp:original-icon"


def test_generate_entity_considers_registered_entities(registry):
    """Test that we don't create entity id that are already registered."""
    entry = registry.async_get_or_create("light", "hue", "1234")
    assert entry.entity_id == "light.hue_1234"
    assert registry.async_generate_entity_id("light", "hue_1234") == "light.hue_1234_2"


def test_generate_entity_considers_existing_entities.opp, registry):
    """Test that we don't create entity id that currently exists."""
    opp.states.async_set("light.kitchen", "on")
    assert registry.async_generate_entity_id("light", "kitchen") == "light.kitchen_2"


def test_is_registered(registry):
    """Test that is_registered works."""
    entry = registry.async_get_or_create("light", "hue", "1234")
    assert registry.async_is_registered(entry.entity_id)
    assert not registry.async_is_registered("light.non_existing")


@pytest.mark.parametrize("load_registries", [False])
async def test_loading_extra_values.opp, opp_storage):
    """Test we load extra data from the registry."""
    opp.storage[entity_registry.STORAGE_KEY] = {
        "version": entity_registry.STORAGE_VERSION,
        "data": {
            "entities": [
                {
                    "entity_id": "test.named",
                    "platform": "super_platform",
                    "unique_id": "with-name",
                    "name": "registry override",
                },
                {
                    "entity_id": "test.no_name",
                    "platform": "super_platform",
                    "unique_id": "without-name",
                },
                {
                    "entity_id": "test.disabled_user",
                    "platform": "super_platform",
                    "unique_id": "disabled-user",
                    "disabled_by": "user",
                },
                {
                    "entity_id": "test.disabled.opp",
                    "platform": "super_platform",
                    "unique_id": "disabled.opp",
                    "disabled_by":  opp.,
                },
                {
                    "entity_id": "test.invalid__entity",
                    "platform": "super_platform",
                    "unique_id": "invalid.opp",
                    "disabled_by":  opp.,
                },
            ]
        },
    }

    await entity_registry.async_load.opp)
    registry = entity_registry.async_get.opp)

    assert len(registry.entities) == 4

    entry_with_name = registry.async_get_or_create(
        "test", "super_platform", "with-name"
    )
    entry_without_name = registry.async_get_or_create(
        "test", "super_platform", "without-name"
    )
    assert entry_with_name.name == "registry override"
    assert entry_without_name.name is None
    assert not entry_with_name.disabled

    entry_disabled opp =registry.async_get_or_create(
        "test", "super_platform", "disabled.opp"
    )
    entry_disabled_user = registry.async_get_or_create(
        "test", "super_platform", "disabled-user"
    )
    assert entry_disabled.opp.disabled
    assert entry_disabled.opp.disabled_by == entity_registry.DISABLED_OPP
    assert entry_disabled_user.disabled
    assert entry_disabled_user.disabled_by == entity_registry.DISABLED_USER


def test_async_get_entity_id(registry):
    """Test that entity_id is returned."""
    entry = registry.async_get_or_create("light", "hue", "1234")
    assert entry.entity_id == "light.hue_1234"
    assert registry.async_get_entity_id("light", "hue", "1234") == "light.hue_1234"
    assert registry.async_get_entity_id("light", "hue", "123") is None


async def test_updating_config_entry_id.opp, registry, update_events):
    """Test that we update config entry id in registry."""
    mock_config_1 = MockConfigEntry(domain="light", entry_id="mock-id-1")
    entry = registry.async_get_or_create(
        "light", "hue", "5678", config_entry=mock_config_1
    )

    mock_config_2 = MockConfigEntry(domain="light", entry_id="mock-id-2")
    entry2 = registry.async_get_or_create(
        "light", "hue", "5678", config_entry=mock_config_2
    )
    assert entry.entity_id == entry2.entity_id
    assert entry2.config_entry_id == "mock-id-2"

    await opp.async_block_till_done()

    assert len(update_events) == 2
    assert update_events[0]["action"] == "create"
    assert update_events[0]["entity_id"] == entry.entity_id
    assert update_events[1]["action"] == "update"
    assert update_events[1]["entity_id"] == entry.entity_id
    assert update_events[1]["changes"] == ["config_entry_id"]


async def test_removing_config_entry_id.opp, registry, update_events):
    """Test that we update config entry id in registry."""
    mock_config = MockConfigEntry(domain="light", entry_id="mock-id-1")

    entry = registry.async_get_or_create(
        "light", "hue", "5678", config_entry=mock_config
    )
    assert entry.config_entry_id == "mock-id-1"
    registry.async_clear_config_entry("mock-id-1")

    assert not registry.entities

    await opp.async_block_till_done()

    assert len(update_events) == 2
    assert update_events[0]["action"] == "create"
    assert update_events[0]["entity_id"] == entry.entity_id
    assert update_events[1]["action"] == "remove"
    assert update_events[1]["entity_id"] == entry.entity_id


async def test_removing_area_id(registry):
    """Make sure we can clear area id."""
    entry = registry.async_get_or_create("light", "hue", "5678")

    entry_w_area = registry.async_update_entity(entry.entity_id, area_id="12345A")

    registry.async_clear_area_id("12345A")
    entry_wo_area = registry.async_get(entry.entity_id)

    assert not entry_wo_area.area_id
    assert entry_w_area != entry_wo_area


@pytest.mark.parametrize("load_registries", [False])
async def test_migration.opp):
    """Test migration from old data to new."""
    mock_config = MockConfigEntry(domain="test-platform", entry_id="test-config-id")

    old_conf = {
        "light.kitchen": {
            "config_entry_id": "test-config-id",
            "unique_id": "test-unique",
            "platform": "test-platform",
            "name": "Test Name",
            "disabled_by":  opp.,
        }
    }
    with patch("os.path.isfile", return_value=True), patch("os.remove"), patch(
        "openpeerpower.helpers.entity_registry.load_yaml", return_value=old_conf
    ):
        await entity_registry.async_load.opp)
        registry = entity_registry.async_get.opp)

    assert registry.async_is_registered("light.kitchen")
    entry = registry.async_get_or_create(
        domain="light",
        platform="test-platform",
        unique_id="test-unique",
        config_entry=mock_config,
    )
    assert entry.name == "Test Name"
    assert entry.disabled_by == opp"
    assert entry.config_entry_id == "test-config-id"


async def test_loading_invalid_entity_id.opp, opp_storage):
    """Test we autofix invalid entity IDs."""
    opp.storage[entity_registry.STORAGE_KEY] = {
        "version": entity_registry.STORAGE_VERSION,
        "data": {
            "entities": [
                {
                    "entity_id": "test.invalid__middle",
                    "platform": "super_platform",
                    "unique_id": "id-invalid-middle",
                    "name": "registry override",
                },
                {
                    "entity_id": "test.invalid_end_",
                    "platform": "super_platform",
                    "unique_id": "id-invalid-end",
                },
                {
                    "entity_id": "test._invalid_start",
                    "platform": "super_platform",
                    "unique_id": "id-invalid-start",
                },
            ]
        },
    }

    registry = await entity_registry.async_get_registry.opp)

    entity_invalid_middle = registry.async_get_or_create(
        "test", "super_platform", "id-invalid-middle"
    )

    assert valid_entity_id(entity_invalid_middle.entity_id)

    entity_invalid_end = registry.async_get_or_create(
        "test", "super_platform", "id-invalid-end"
    )

    assert valid_entity_id(entity_invalid_end.entity_id)

    entity_invalid_start = registry.async_get_or_create(
        "test", "super_platform", "id-invalid-start"
    )

    assert valid_entity_id(entity_invalid_start.entity_id)


async def test_update_entity_unique_id(registry):
    """Test entity's unique_id is updated."""
    mock_config = MockConfigEntry(domain="light", entry_id="mock-id-1")

    entry = registry.async_get_or_create(
        "light", "hue", "5678", config_entry=mock_config
    )
    assert registry.async_get_entity_id("light", "hue", "5678") == entry.entity_id

    new_unique_id = "1234"
    with patch.object(registry, "async_schedule_save") as mock_schedule_save:
        updated_entry = registry.async_update_entity(
            entry.entity_id, new_unique_id=new_unique_id
        )
    assert updated_entry != entry
    assert updated_entry.unique_id == new_unique_id
    assert mock_schedule_save.call_count == 1

    assert registry.async_get_entity_id("light", "hue", "5678") is None
    assert registry.async_get_entity_id("light", "hue", "1234") == entry.entity_id


async def test_update_entity_unique_id_conflict(registry):
    """Test migration raises when unique_id already in use."""
    mock_config = MockConfigEntry(domain="light", entry_id="mock-id-1")
    entry = registry.async_get_or_create(
        "light", "hue", "5678", config_entry=mock_config
    )
    entry2 = registry.async_get_or_create(
        "light", "hue", "1234", config_entry=mock_config
    )
    with patch.object(
        registry, "async_schedule_save"
    ) as mock_schedule_save, pytest.raises(ValueError):
        registry.async_update_entity(entry.entity_id, new_unique_id=entry2.unique_id)
    assert mock_schedule_save.call_count == 0
    assert registry.async_get_entity_id("light", "hue", "5678") == entry.entity_id
    assert registry.async_get_entity_id("light", "hue", "1234") == entry2.entity_id


async def test_update_entity(registry):
    """Test updating entity."""
    mock_config = MockConfigEntry(domain="light", entry_id="mock-id-1")
    entry = registry.async_get_or_create(
        "light", "hue", "5678", config_entry=mock_config
    )

    for attr_name, new_value in (
        ("name", "new name"),
        ("icon", "new icon"),
        ("disabled_by", entity_registry.DISABLED_USER),
    ):
        changes = {attr_name: new_value}
        updated_entry = registry.async_update_entity(entry.entity_id, **changes)

        assert updated_entry != entry
        assert getattr(updated_entry, attr_name) == new_value
        assert getattr(updated_entry, attr_name) != getattr(entry, attr_name)

        assert (
            registry.async_get_entity_id("light", "hue", "5678")
            == updated_entry.entity_id
        )
        entry = updated_entry


async def test_disabled_by(registry):
    """Test that we can disable an entry when we create it."""
    entry = registry.async_get_or_create("light", "hue", "5678", disabled_by= opp")
    assert entry.disabled_by == opp"

    entry = registry.async_get_or_create(
        "light", "hue", "5678", disabled_by="integration"
    )
    assert entry.disabled_by == opp"

    entry2 = registry.async_get_or_create("light", "hue", "1234")
    assert entry2.disabled_by is None


async def test_disabled_by_system_options(registry):
    """Test system options setting disabled_by."""
    mock_config = MockConfigEntry(
        domain="light",
        entry_id="mock-id-1",
        system_options={"disable_new_entities": True},
    )
    entry = registry.async_get_or_create(
        "light", "hue", "AAAA", config_entry=mock_config
    )
    assert entry.disabled_by == "integration"

    entry2 = registry.async_get_or_create(
        "light", "hue", "BBBB", config_entry=mock_config, disabled_by="user"
    )
    assert entry2.disabled_by == "user"


async def test_restore_states.opp):
    """Test restoring states."""
    opp.state = CoreState.not_running

    registry = await entity_registry.async_get_registry.opp)

    registry.async_get_or_create(
        "light",
        "hue",
        "1234",
        suggested_object_id="simple",
    )
    # Should not be created
    registry.async_get_or_create(
        "light",
        "hue",
        "5678",
        suggested_object_id="disabled",
        disabled_by=entity_registry.DISABLED_OPP,
    )
    registry.async_get_or_create(
        "light",
        "hue",
        "9012",
        suggested_object_id="all_info_set",
        capabilities={"max": 100},
        supported_features=5,
        device_class="mock-device-class",
        original_name="Mock Original Name",
        original_icon= opp:original-icon",
    )

    opp.bus.async_fire(EVENT_OPENPEERPOWER_START, {})
    await opp.async_block_till_done()

    simple = opp.states.get("light.simple")
    assert simple is not None
    assert simple.state == STATE_UNAVAILABLE
    assert simple.attributes == {"restored": True, "supported_features": 0}

    disabled = opp.states.get("light.disabled")
    assert disabled is None

    all_info_set = opp.states.get("light.all_info_set")
    assert all_info_set is not None
    assert all_info_set.state == STATE_UNAVAILABLE
    assert all_info_set.attributes == {
        "max": 100,
        "supported_features": 5,
        "device_class": "mock-device-class",
        "restored": True,
        "friendly_name": "Mock Original Name",
        "icon":  opp.original-icon",
    }

    registry.async_remove("light.disabled")
    registry.async_remove("light.simple")
    registry.async_remove("light.all_info_set")

    await opp.async_block_till_done()

    assert.opp.states.get("light.simple") is None
    assert.opp.states.get("light.disabled") is None
    assert.opp.states.get("light.all_info_set") is None


async def test_async_get_device_class_lookup.opp):
    """Test registry device class lookup."""
    opp.state = CoreState.not_running

    ent_reg = await entity_registry.async_get_registry.opp)

    ent_reg.async_get_or_create(
        "binary_sensor",
        "light",
        "battery_charging",
        device_id="light_device_entry_id",
        device_class="battery_charging",
    )
    ent_reg.async_get_or_create(
        "sensor",
        "light",
        "battery",
        device_id="light_device_entry_id",
        device_class="battery",
    )
    ent_reg.async_get_or_create(
        "light", "light", "demo", device_id="light_device_entry_id"
    )
    ent_reg.async_get_or_create(
        "binary_sensor",
        "vacuum",
        "battery_charging",
        device_id="vacuum_device_entry_id",
        device_class="battery_charging",
    )
    ent_reg.async_get_or_create(
        "sensor",
        "vacuum",
        "battery",
        device_id="vacuum_device_entry_id",
        device_class="battery",
    )
    ent_reg.async_get_or_create(
        "vacuum", "vacuum", "demo", device_id="vacuum_device_entry_id"
    )
    ent_reg.async_get_or_create(
        "binary_sensor",
        "remote",
        "battery_charging",
        device_id="remote_device_entry_id",
        device_class="battery_charging",
    )
    ent_reg.async_get_or_create(
        "remote", "remote", "demo", device_id="remote_device_entry_id"
    )

    device_lookup = ent_reg.async_get_device_class_lookup(
        {("binary_sensor", "battery_charging"), ("sensor", "battery")}
    )

    assert device_lookup == {
        "remote_device_entry_id": {
            (
                "binary_sensor",
                "battery_charging",
            ): "binary_sensor.remote_battery_charging"
        },
        "light_device_entry_id": {
            (
                "binary_sensor",
                "battery_charging",
            ): "binary_sensor.light_battery_charging",
            ("sensor", "battery"): "sensor.light_battery",
        },
        "vacuum_device_entry_id": {
            (
                "binary_sensor",
                "battery_charging",
            ): "binary_sensor.vacuum_battery_charging",
            ("sensor", "battery"): "sensor.vacuum_battery",
        },
    }


async def test_remove_device_removes_entities.opp, registry):
    """Test that we remove entities tied to a device."""
    device_registry = mock_device_registry.opp)
    config_entry = MockConfigEntry(domain="light")

    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={("mac", "12:34:56:AB:CD:EF")},
    )

    entry = registry.async_get_or_create(
        "light",
        "hue",
        "5678",
        config_entry=config_entry,
        device_id=device_entry.id,
    )

    assert registry.async_is_registered(entry.entity_id)

    device_registry.async_remove_device(device_entry.id)
    await opp.async_block_till_done()

    assert not registry.async_is_registered(entry.entity_id)


async def test_update_device_race.opp, registry):
    """Test race when a device is created, updated and removed."""
    device_registry = mock_device_registry.opp)
    config_entry = MockConfigEntry(domain="light")

    # Create device
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={("mac", "12:34:56:AB:CD:EF")},
    )
    # Update it
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={("bridgeid", "0123")},
        connections={("mac", "12:34:56:AB:CD:EF")},
    )
    # Add entity to the device
    entry = registry.async_get_or_create(
        "light",
        "hue",
        "5678",
        config_entry=config_entry,
        device_id=device_entry.id,
    )

    assert registry.async_is_registered(entry.entity_id)

    device_registry.async_remove_device(device_entry.id)
    await opp.async_block_till_done()

    assert not registry.async_is_registered(entry.entity_id)


async def test_disable_device_disables_entities.opp, registry):
    """Test that we disable entities tied to a device."""
    device_registry = mock_device_registry.opp)
    config_entry = MockConfigEntry(domain="light")
    config_entry.add_to.opp.opp)

    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={("mac", "12:34:56:AB:CD:EF")},
    )

    entry1 = registry.async_get_or_create(
        "light",
        "hue",
        "5678",
        config_entry=config_entry,
        device_id=device_entry.id,
    )
    entry2 = registry.async_get_or_create(
        "light",
        "hue",
        "ABCD",
        config_entry=config_entry,
        device_id=device_entry.id,
        disabled_by="user",
    )
    entry3 = registry.async_get_or_create(
        "light",
        "hue",
        "EFGH",
        config_entry=config_entry,
        device_id=device_entry.id,
        disabled_by="config_entry",
    )

    assert not entry1.disabled
    assert entry2.disabled
    assert entry3.disabled

    device_registry.async_update_device(device_entry.id, disabled_by="user")
    await opp.async_block_till_done()

    entry1 = registry.async_get(entry1.entity_id)
    assert entry1.disabled
    assert entry1.disabled_by == "device"
    entry2 = registry.async_get(entry2.entity_id)
    assert entry2.disabled
    assert entry2.disabled_by == "user"
    entry3 = registry.async_get(entry3.entity_id)
    assert entry3.disabled
    assert entry3.disabled_by == "config_entry"

    device_registry.async_update_device(device_entry.id, disabled_by=None)
    await opp.async_block_till_done()

    entry1 = registry.async_get(entry1.entity_id)
    assert not entry1.disabled
    entry2 = registry.async_get(entry2.entity_id)
    assert entry2.disabled
    assert entry2.disabled_by == "user"
    entry3 = registry.async_get(entry3.entity_id)
    assert entry3.disabled
    assert entry3.disabled_by == "config_entry"


async def test_disable_config_entry_disables_entities.opp, registry):
    """Test that we disable entities tied to a config entry."""
    device_registry = mock_device_registry.opp)
    config_entry = MockConfigEntry(domain="light")
    config_entry.add_to.opp.opp)

    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={("mac", "12:34:56:AB:CD:EF")},
    )

    entry1 = registry.async_get_or_create(
        "light",
        "hue",
        "5678",
        config_entry=config_entry,
        device_id=device_entry.id,
    )
    entry2 = registry.async_get_or_create(
        "light",
        "hue",
        "ABCD",
        config_entry=config_entry,
        device_id=device_entry.id,
        disabled_by="user",
    )
    entry3 = registry.async_get_or_create(
        "light",
        "hue",
        "EFGH",
        config_entry=config_entry,
        device_id=device_entry.id,
        disabled_by="device",
    )

    assert not entry1.disabled
    assert entry2.disabled
    assert entry3.disabled

    await opp.config_entries.async_set_disabled_by(config_entry.entry_id, "user")
    await opp.async_block_till_done()

    entry1 = registry.async_get(entry1.entity_id)
    assert entry1.disabled
    assert entry1.disabled_by == "config_entry"
    entry2 = registry.async_get(entry2.entity_id)
    assert entry2.disabled
    assert entry2.disabled_by == "user"
    entry3 = registry.async_get(entry3.entity_id)
    assert entry3.disabled
    assert entry3.disabled_by == "device"

    await opp.config_entries.async_set_disabled_by(config_entry.entry_id, None)
    await opp.async_block_till_done()

    entry1 = registry.async_get(entry1.entity_id)
    assert not entry1.disabled
    entry2 = registry.async_get(entry2.entity_id)
    assert entry2.disabled
    assert entry2.disabled_by == "user"
    # The device was re-enabled, so entity disabled by the device will be re-enabled too
    entry3 = registry.async_get(entry3.entity_id)
    assert not entry3.disabled_by


async def test_disabled_entities_excluded_from_entity_list.opp, registry):
    """Test that disabled entities are excluded from async_entries_for_device."""
    device_registry = mock_device_registry.opp)
    config_entry = MockConfigEntry(domain="light")

    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={("mac", "12:34:56:AB:CD:EF")},
    )

    entry1 = registry.async_get_or_create(
        "light",
        "hue",
        "5678",
        config_entry=config_entry,
        device_id=device_entry.id,
    )

    entry2 = registry.async_get_or_create(
        "light",
        "hue",
        "ABCD",
        config_entry=config_entry,
        device_id=device_entry.id,
        disabled_by="user",
    )

    entries = entity_registry.async_entries_for_device(registry, device_entry.id)
    assert entries == [entry1]

    entries = entity_registry.async_entries_for_device(
        registry, device_entry.id, include_disabled_entities=True
    )
    assert entries == [entry1, entry2]
