"""Tests for the tag component."""
from unittest.mock import patch

import pytest

from openpeerpower.components.tag import DOMAIN, TAGS, async_scan_tag
from openpeerpower.helpers import collection
from openpeerpower.setup import async_setup_component
from openpeerpower.util import dt as dt_util


@pytest.fixture
def storage_setup_opp, opp_storage):
    """Storage setup."""

    async def _storage(items=None):
        if items is None:
           .opp_storage[DOMAIN] = {
                "key": DOMAIN,
                "version": 1,
                "data": {"items": [{"id": "test tag"}]},
            }
        else:
           .opp_storage[DOMAIN] = items
        config = {DOMAIN: {}}
        return await async_setup_component.opp, DOMAIN, config)

    return _storage


async def test_ws_list.opp, opp_ws_client, storage_setup):
    """Test listing tags via WS."""
    assert await storage_setup()

    client = await.opp_ws_client.opp)

    await client.send_json({"id": 6, "type": f"{DOMAIN}/list"})
    resp = await client.receive_json()
    assert resp["success"]

    result = {item["id"]: item for item in resp["result"]}

    assert len(result) == 1
    assert "test tag" in result


async def test_ws_update.opp, opp_ws_client, storage_setup):
    """Test listing tags via WS."""
    assert await storage_setup()
    await async_scan_tag.opp, "test tag", "some_scanner")

    client = await.opp_ws_client.opp)

    await client.send_json(
        {
            "id": 6,
            "type": f"{DOMAIN}/update",
            f"{DOMAIN}_id": "test tag",
            "name": "New name",
        }
    )
    resp = await client.receive_json()
    assert resp["success"]

    item = resp["result"]

    assert item["id"] == "test tag"
    assert item["name"] == "New name"


async def test_tag_scanned.opp, opp_ws_client, storage_setup):
    """Test scanning tags."""
    assert await storage_setup()

    client = await.opp_ws_client.opp)

    await client.send_json({"id": 6, "type": f"{DOMAIN}/list"})
    resp = await client.receive_json()
    assert resp["success"]

    result = {item["id"]: item for item in resp["result"]}

    assert len(result) == 1
    assert "test tag" in result

    now = dt_util.utcnow()
    with patch("openpeerpower.util.dt.utcnow", return_value=now):
        await async_scan_tag.opp, "new tag", "some_scanner")

    await client.send_json({"id": 7, "type": f"{DOMAIN}/list"})
    resp = await client.receive_json()
    assert resp["success"]

    result = {item["id"]: item for item in resp["result"]}

    assert len(result) == 2
    assert "test tag" in result
    assert "new tag" in result
    assert result["new tag"]["last_scanned"] == now.isoformat()


def track_changes(coll: collection.ObservableCollection):
    """Create helper to track changes in a collection."""
    changes = []

    async def listener(*args):
        changes.append(args)

    coll.async_add_listener(listener)

    return changes


async def test_tag_id_exists(opp, opp_ws_client, storage_setup):
    """Test scanning tags."""
    assert await storage_setup()
    changes = track_changes.opp.data[DOMAIN][TAGS])
    client = await.opp_ws_client.opp)

    await client.send_json({"id": 2, "type": f"{DOMAIN}/create", "tag_id": "test tag"})
    response = await client.receive_json()
    assert not response["success"]
    assert response["error"]["code"] == "unknown_error"
    assert len(changes) == 0
