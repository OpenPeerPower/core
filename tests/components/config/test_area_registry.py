"""Test area_registry API."""
import pytest

from openpeerpower.components.config import area_registry

from tests.common import mock_area_registry


@pytest.fixture
def client.opp, opp_ws_client):
    """Fixture that can interact with the config manager API."""
   .opp.loop.run_until_complete(area_registry.async_setup_opp))
    yield.opp.loop.run_until_complete.opp_ws_client.opp))


@pytest.fixture
def registry.opp):
    """Return an empty, loaded, registry."""
    return mock_area_registry.opp)


async def test_list_areas.opp, client, registry):
    """Test list entries."""
    registry.async_create("mock 1")
    registry.async_create("mock 2")

    await client.send_json({"id": 1, "type": "config/area_registry/list"})

    msg = await client.receive_json()

    assert len(msg["result"]) == len(registry.areas)


async def test_create_area.opp, client, registry):
    """Test create entry."""
    await client.send_json(
        {"id": 1, "name": "mock", "type": "config/area_registry/create"}
    )

    msg = await client.receive_json()

    assert "mock" in msg["result"]["name"]
    assert len(registry.areas) == 1


async def test_create_area_with_name_already_in_use.opp, client, registry):
    """Test create entry that should fail."""
    registry.async_create("mock")

    await client.send_json(
        {"id": 1, "name": "mock", "type": "config/area_registry/create"}
    )

    msg = await client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == "invalid_info"
    assert msg["error"]["message"] == "The name mock (mock) is already in use"
    assert len(registry.areas) == 1


async def test_delete_area.opp, client, registry):
    """Test delete entry."""
    area = registry.async_create("mock")

    await client.send_json(
        {"id": 1, "area_id": area.id, "type": "config/area_registry/delete"}
    )

    msg = await client.receive_json()

    assert msg["success"]
    assert not registry.areas


async def test_delete_non_existing_area.opp, client, registry):
    """Test delete entry that should fail."""
    registry.async_create("mock")

    await client.send_json(
        {"id": 1, "area_id": "", "type": "config/area_registry/delete"}
    )

    msg = await client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == "invalid_info"
    assert msg["error"]["message"] == "Area ID doesn't exist"
    assert len(registry.areas) == 1


async def test_update_area.opp, client, registry):
    """Test update entry."""
    area = registry.async_create("mock 1")

    await client.send_json(
        {
            "id": 1,
            "area_id": area.id,
            "name": "mock 2",
            "type": "config/area_registry/update",
        }
    )

    msg = await client.receive_json()

    assert msg["result"]["area_id"] == area.id
    assert msg["result"]["name"] == "mock 2"
    assert len(registry.areas) == 1


async def test_update_area_with_same_name.opp, client, registry):
    """Test update entry."""
    area = registry.async_create("mock 1")

    await client.send_json(
        {
            "id": 1,
            "area_id": area.id,
            "name": "mock 1",
            "type": "config/area_registry/update",
        }
    )

    msg = await client.receive_json()

    assert msg["result"]["area_id"] == area.id
    assert msg["result"]["name"] == "mock 1"
    assert len(registry.areas) == 1


async def test_update_area_with_name_already_in_use.opp, client, registry):
    """Test update entry."""
    area = registry.async_create("mock 1")
    registry.async_create("mock 2")

    await client.send_json(
        {
            "id": 1,
            "area_id": area.id,
            "name": "mock 2",
            "type": "config/area_registry/update",
        }
    )

    msg = await client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == "invalid_info"
    assert msg["error"]["message"] == "The name mock 2 (mock2) is already in use"
    assert len(registry.areas) == 2
