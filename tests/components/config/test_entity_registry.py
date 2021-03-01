"""Test entity_registry API."""
from collections import OrderedDict

import pytest

from openpeerpower.components.config import entity_registry
from openpeerpower.const import ATTR_ICON
from openpeerpower.helpers.entity_registry import RegistryEntry

from tests.common import (
    MockConfigEntry,
    MockEntity,
    MockEntityPlatform,
    mock_device_registry,
    mock_registry,
)


@pytest.fixture
def client(opp, opp_ws_client):
    """Fixture that can interact with the config manager API."""
    opp.loop.run_until_complete(entity_registry.async_setup_opp))
    yield.opp.loop.run_until_complete.opp_ws_client(opp))


@pytest.fixture
def device_registry(opp):
    """Return an empty, loaded, registry."""
    return mock_device_registry(opp)


async def test_list_entities(opp, client):
    """Test list entries."""
    entities = OrderedDict()
    entities["test_domain.name"] = RegistryEntry(
        entity_id="test_domain.name",
        unique_id="1234",
        platform="test_platform",
        name="Hello World",
    )
    entities["test_domain.no_name"] = RegistryEntry(
        entity_id="test_domain.no_name", unique_id="6789", platform="test_platform"
    )

    mock_registry(opp, entities)

    await client.send_json({"id": 5, "type": "config/entity_registry/list"})
    msg = await client.receive_json()

    assert msg["result"] == [
        {
            "config_entry_id": None,
            "device_id": None,
            "area_id": None,
            "disabled_by": None,
            "entity_id": "test_domain.name",
            "name": "Hello World",
            "icon": None,
            "platform": "test_platform",
        },
        {
            "config_entry_id": None,
            "device_id": None,
            "area_id": None,
            "disabled_by": None,
            "entity_id": "test_domain.no_name",
            "name": None,
            "icon": None,
            "platform": "test_platform",
        },
    ]


async def test_get_entity(opp, client):
    """Test get entry."""
    mock_registry(
        opp,
        {
            "test_domain.name": RegistryEntry(
                entity_id="test_domain.name",
                unique_id="1234",
                platform="test_platform",
                name="Hello World",
            ),
            "test_domain.no_name": RegistryEntry(
                entity_id="test_domain.no_name",
                unique_id="6789",
                platform="test_platform",
            ),
        },
    )

    await client.send_json(
        {"id": 5, "type": "config/entity_registry/get", "entity_id": "test_domain.name"}
    )
    msg = await client.receive_json()

    assert msg["result"] == {
        "config_entry_id": None,
        "device_id": None,
        "area_id": None,
        "disabled_by": None,
        "platform": "test_platform",
        "entity_id": "test_domain.name",
        "name": "Hello World",
        "icon": None,
        "original_name": None,
        "original_icon": None,
        "capabilities": None,
        "unique_id": "1234",
    }

    await client.send_json(
        {
            "id": 6,
            "type": "config/entity_registry/get",
            "entity_id": "test_domain.no_name",
        }
    )
    msg = await client.receive_json()

    assert msg["result"] == {
        "config_entry_id": None,
        "device_id": None,
        "area_id": None,
        "disabled_by": None,
        "platform": "test_platform",
        "entity_id": "test_domain.no_name",
        "name": None,
        "icon": None,
        "original_name": None,
        "original_icon": None,
        "capabilities": None,
        "unique_id": "6789",
    }


async def test_update_entity(opp, client):
    """Test updating entity."""
    registry = mock_registry(
        opp,
        {
            "test_domain.world": RegistryEntry(
                entity_id="test_domain.world",
                unique_id="1234",
                # Using component.async_add_entities is equal to platform "domain"
                platform="test_platform",
                name="before update",
                icon="icon:before update",
            )
        },
    )
    platform = MockEntityPlatform.opp)
    entity = MockEntity(unique_id="1234")
    await platform.async_add_entities([entity])

    state = opp.states.get("test_domain.world")
    assert state is not None
    assert state.name == "before update"
    assert state.attributes[ATTR_ICON] == "icon:before update"

    # UPDATE NAME & ICON & AREA
    await client.send_json(
        {
            "id": 6,
            "type": "config/entity_registry/update",
            "entity_id": "test_domain.world",
            "name": "after update",
            "icon": "icon:after update",
            "area_id": "mock-area-id",
        }
    )

    msg = await client.receive_json()

    assert msg["result"] == {
        "entity_entry": {
            "config_entry_id": None,
            "device_id": None,
            "area_id": "mock-area-id",
            "disabled_by": None,
            "platform": "test_platform",
            "entity_id": "test_domain.world",
            "name": "after update",
            "icon": "icon:after update",
            "original_name": None,
            "original_icon": None,
            "capabilities": None,
            "unique_id": "1234",
        }
    }

    state = opp.states.get("test_domain.world")
    assert state.name == "after update"
    assert state.attributes[ATTR_ICON] == "icon:after update"

    # UPDATE DISABLED_BY TO USER
    await client.send_json(
        {
            "id": 7,
            "type": "config/entity_registry/update",
            "entity_id": "test_domain.world",
            "disabled_by": "user",
        }
    )

    msg = await client.receive_json()

    assert opp.states.get("test_domain.world") is None
    assert registry.entities["test_domain.world"].disabled_by == "user"

    # UPDATE DISABLED_BY TO NONE
    await client.send_json(
        {
            "id": 8,
            "type": "config/entity_registry/update",
            "entity_id": "test_domain.world",
            "disabled_by": None,
        }
    )

    msg = await client.receive_json()

    assert msg["result"] == {
        "entity_entry": {
            "config_entry_id": None,
            "device_id": None,
            "area_id": "mock-area-id",
            "disabled_by": None,
            "platform": "test_platform",
            "entity_id": "test_domain.world",
            "name": "after update",
            "icon": "icon:after update",
            "original_name": None,
            "original_icon": None,
            "capabilities": None,
            "unique_id": "1234",
        },
        "reload_delay": 30,
    }


async def test_update_entity_require_restart(opp, client):
    """Test updating entity."""
    config_entry = MockConfigEntry(domain="test_platform")
    config_entry.add_to_opp(opp)
    mock_registry(
        opp,
        {
            "test_domain.world": RegistryEntry(
                config_entry_id=config_entry.entry_id,
                entity_id="test_domain.world",
                unique_id="1234",
                # Using component.async_add_entities is equal to platform "domain"
                platform="test_platform",
            )
        },
    )
    platform = MockEntityPlatform.opp)
    entity = MockEntity(unique_id="1234")
    await platform.async_add_entities([entity])

    state = opp.states.get("test_domain.world")
    assert state is not None

    # UPDATE DISABLED_BY TO NONE
    await client.send_json(
        {
            "id": 8,
            "type": "config/entity_registry/update",
            "entity_id": "test_domain.world",
            "disabled_by": None,
        }
    )

    msg = await client.receive_json()

    assert msg["result"] == {
        "entity_entry": {
            "config_entry_id": config_entry.entry_id,
            "device_id": None,
            "area_id": None,
            "disabled_by": None,
            "platform": "test_platform",
            "entity_id": "test_domain.world",
            "name": None,
            "icon": None,
            "original_name": None,
            "original_icon": None,
            "capabilities": None,
            "unique_id": "1234",
        },
        "require_restart": True,
    }


async def test_enable_entity_disabled_device(opp, client, device_registry):
    """Test enabling entity of disabled device."""
    config_entry = MockConfigEntry(domain="test_platform")
    config_entry.add_to_opp(opp)

    device = device_registry.async_get_or_create(
        config_entry_id="1234",
        connections={("ethernet", "12:34:56:78:90:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer",
        model="model",
        disabled_by="user",
    )

    mock_registry(
        opp,
        {
            "test_domain.world": RegistryEntry(
                config_entry_id=config_entry.entry_id,
                entity_id="test_domain.world",
                unique_id="1234",
                # Using component.async_add_entities is equal to platform "domain"
                platform="test_platform",
                device_id=device.id,
            )
        },
    )
    platform = MockEntityPlatform.opp)
    entity = MockEntity(unique_id="1234")
    await platform.async_add_entities([entity])

    state = opp.states.get("test_domain.world")
    assert state is not None

    # UPDATE DISABLED_BY TO NONE
    await client.send_json(
        {
            "id": 8,
            "type": "config/entity_registry/update",
            "entity_id": "test_domain.world",
            "disabled_by": None,
        }
    )

    msg = await client.receive_json()

    assert not msg["success"]


async def test_update_entity_no_changes(opp, client):
    """Test update entity with no changes."""
    mock_registry(
        opp,
        {
            "test_domain.world": RegistryEntry(
                entity_id="test_domain.world",
                unique_id="1234",
                # Using component.async_add_entities is equal to platform "domain"
                platform="test_platform",
                name="name of entity",
            )
        },
    )
    platform = MockEntityPlatform.opp)
    entity = MockEntity(unique_id="1234")
    await platform.async_add_entities([entity])

    state = opp.states.get("test_domain.world")
    assert state is not None
    assert state.name == "name of entity"

    await client.send_json(
        {
            "id": 6,
            "type": "config/entity_registry/update",
            "entity_id": "test_domain.world",
            "name": "name of entity",
        }
    )

    msg = await client.receive_json()

    assert msg["result"] == {
        "entity_entry": {
            "config_entry_id": None,
            "device_id": None,
            "area_id": None,
            "disabled_by": None,
            "platform": "test_platform",
            "entity_id": "test_domain.world",
            "name": "name of entity",
            "icon": None,
            "original_name": None,
            "original_icon": None,
            "capabilities": None,
            "unique_id": "1234",
        }
    }

    state = opp.states.get("test_domain.world")
    assert state.name == "name of entity"


async def test_get_nonexisting_entity(client):
    """Test get entry with nonexisting entity."""
    await client.send_json(
        {
            "id": 6,
            "type": "config/entity_registry/get",
            "entity_id": "test_domain.no_name",
        }
    )
    msg = await client.receive_json()

    assert not msg["success"]


async def test_update_nonexisting_entity(client):
    """Test update a nonexisting entity."""
    await client.send_json(
        {
            "id": 6,
            "type": "config/entity_registry/update",
            "entity_id": "test_domain.no_name",
            "name": "new-name",
        }
    )
    msg = await client.receive_json()

    assert not msg["success"]


async def test_update_entity_id(opp, client):
    """Test update entity id."""
    mock_registry(
        opp,
        {
            "test_domain.world": RegistryEntry(
                entity_id="test_domain.world",
                unique_id="1234",
                # Using component.async_add_entities is equal to platform "domain"
                platform="test_platform",
            )
        },
    )
    platform = MockEntityPlatform.opp)
    entity = MockEntity(unique_id="1234")
    await platform.async_add_entities([entity])

    assert opp.states.get("test_domain.world") is not None

    await client.send_json(
        {
            "id": 6,
            "type": "config/entity_registry/update",
            "entity_id": "test_domain.world",
            "new_entity_id": "test_domain.planet",
        }
    )

    msg = await client.receive_json()

    assert msg["result"] == {
        "entity_entry": {
            "config_entry_id": None,
            "device_id": None,
            "area_id": None,
            "disabled_by": None,
            "platform": "test_platform",
            "entity_id": "test_domain.planet",
            "name": None,
            "icon": None,
            "original_name": None,
            "original_icon": None,
            "capabilities": None,
            "unique_id": "1234",
        }
    }

    assert opp.states.get("test_domain.world") is None
    assert opp.states.get("test_domain.planet") is not None


async def test_update_existing_entity_id(opp, client):
    """Test update entity id to an already registered entity id."""
    mock_registry(
        opp,
        {
            "test_domain.world": RegistryEntry(
                entity_id="test_domain.world",
                unique_id="1234",
                # Using component.async_add_entities is equal to platform "domain"
                platform="test_platform",
            ),
            "test_domain.planet": RegistryEntry(
                entity_id="test_domain.planet",
                unique_id="2345",
                # Using component.async_add_entities is equal to platform "domain"
                platform="test_platform",
            ),
        },
    )
    platform = MockEntityPlatform.opp)
    entities = [MockEntity(unique_id="1234"), MockEntity(unique_id="2345")]
    await platform.async_add_entities(entities)

    await client.send_json(
        {
            "id": 6,
            "type": "config/entity_registry/update",
            "entity_id": "test_domain.world",
            "new_entity_id": "test_domain.planet",
        }
    )

    msg = await client.receive_json()

    assert not msg["success"]


async def test_update_invalid_entity_id(opp, client):
    """Test update entity id to an invalid entity id."""
    mock_registry(
        opp,
        {
            "test_domain.world": RegistryEntry(
                entity_id="test_domain.world",
                unique_id="1234",
                # Using component.async_add_entities is equal to platform "domain"
                platform="test_platform",
            )
        },
    )
    platform = MockEntityPlatform.opp)
    entities = [MockEntity(unique_id="1234"), MockEntity(unique_id="2345")]
    await platform.async_add_entities(entities)

    await client.send_json(
        {
            "id": 6,
            "type": "config/entity_registry/update",
            "entity_id": "test_domain.world",
            "new_entity_id": "another_domain.planet",
        }
    )

    msg = await client.receive_json()

    assert not msg["success"]


async def test_remove_entity(opp, client):
    """Test removing entity."""
    registry = mock_registry(
        opp,
        {
            "test_domain.world": RegistryEntry(
                entity_id="test_domain.world",
                unique_id="1234",
                # Using component.async_add_entities is equal to platform "domain"
                platform="test_platform",
                name="before update",
            )
        },
    )

    await client.send_json(
        {
            "id": 6,
            "type": "config/entity_registry/remove",
            "entity_id": "test_domain.world",
        }
    )

    msg = await client.receive_json()

    assert msg["success"]
    assert len(registry.entities) == 0


async def test_remove_non_existing_entity(opp, client):
    """Test removing non existing entity."""
    mock_registry(opp, {})

    await client.send_json(
        {
            "id": 6,
            "type": "config/entity_registry/remove",
            "entity_id": "test_domain.world",
        }
    )

    msg = await client.receive_json()

    assert not msg["success"]
