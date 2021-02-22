"""Basic checks for entity map storage."""
from aiohomekit.model.characteristics import CharacteristicsTypes
from aiohomekit.model.services import ServicesTypes

from openpeerpower import config_entries
from openpeerpower.components.homekit_controller import async_remove_entry
from openpeerpower.components.homekit_controller.const import ENTITY_MAP

from tests.common import flush_store
from tests.components.homekit_controller.common import (
    setup_platform,
    setup_test_component,
)


async def test_load_from_storage.opp,.opp_storage):
    """Test that entity map can be correctly loaded from cache."""
    hkid = "00:00:00:00:00:00"

   .opp_storage["homekit_controller-entity-map"] = {
        "version": 1,
        "data": {"pairings": {hkid: {"c#": 1, "accessories": []}}},
    }

    await setup_platform.opp)
    assert hkid in.opp.data[ENTITY_MAP].storage_data


async def test_storage_is_removed.opp,.opp_storage):
    """Test entity map storage removal is idempotent."""
    await setup_platform.opp)

    entity_map =.opp.data[ENTITY_MAP]
    hkid = "00:00:00:00:00:01"

    entity_map.async_create_or_update_map(hkid, 1, [])
    assert hkid in entity_map.storage_data
    await flush_store(entity_map.store)
    assert hkid in.opp_storage[ENTITY_MAP]["data"]["pairings"]

    entity_map.async_delete_map(hkid)
    assert hkid not in.opp.data[ENTITY_MAP].storage_data
    await flush_store(entity_map.store)

    assert.opp_storage[ENTITY_MAP]["data"]["pairings"] == {}


async def test_storage_is_removed_idempotent.opp):
    """Test entity map storage removal is idempotent."""
    await setup_platform.opp)

    entity_map =.opp.data[ENTITY_MAP]
    hkid = "00:00:00:00:00:01"

    assert hkid not in entity_map.storage_data

    entity_map.async_delete_map(hkid)

    assert hkid not in entity_map.storage_data


def create_lightbulb_service(accessory):
    """Define lightbulb characteristics."""
    service = accessory.add_service(ServicesTypes.LIGHTBULB)
    on_char = service.add_char(CharacteristicsTypes.ON)
    on_char.value = 0


async def test_storage_is_updated_on_add.opp,.opp_storage, utcnow):
    """Test entity map storage is cleaned up on adding an accessory."""
    await setup_test_component.opp, create_lightbulb_service)

    entity_map =.opp.data[ENTITY_MAP]
    hkid = "00:00:00:00:00:00"

    # Is in memory store updated?
    assert hkid in entity_map.storage_data

    # Is saved out to store?
    await flush_store(entity_map.store)
    assert hkid in.opp_storage[ENTITY_MAP]["data"]["pairings"]


async def test_storage_is_removed_on_config_entry_removal.opp, utcnow):
    """Test entity map storage is cleaned up on config entry removal."""
    await setup_test_component.opp, create_lightbulb_service)

    hkid = "00:00:00:00:00:00"

    pairing_data = {"AccessoryPairingID": hkid}

    entry = config_entries.ConfigEntry(
        1,
        "homekit_controller",
        "TestData",
        pairing_data,
        "test",
        config_entries.CONN_CLASS_LOCAL_PUSH,
        system_options={},
    )

    assert hkid in.opp.data[ENTITY_MAP].storage_data

    await async_remove_entry.opp, entry)

    assert hkid not in.opp.data[ENTITY_MAP].storage_data
