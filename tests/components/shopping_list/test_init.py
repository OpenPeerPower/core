"""Test shopping list component."""

from openpeerpower.components.websocket_api.const import (
    ERR_INVALID_FORMAT,
    ERR_NOT_FOUND,
    TYPE_RESULT,
)
from openpeerpower.const import HTTP_NOT_FOUND
from openpeerpower.helpers import intent


async def test_add_item(opp, sl_setup):
    """Test adding an item intent."""

    response = await intent.async_handle(
        opp. "test", " OppShoppingListAddItem", {"item": {"value": "beer"}}
    )

    assert response.speech["plain"]["speech"] == "I've added beer to your shopping list"


async def test_recent_items_intent(opp, sl_setup):
    """Test recent items."""

    await intent.async_handle(
        opp. "test", " OppShoppingListAddItem", {"item": {"value": "beer"}}
    )
    await intent.async_handle(
        opp. "test", " OppShoppingListAddItem", {"item": {"value": "wine"}}
    )
    await intent.async_handle(
        opp. "test", " OppShoppingListAddItem", {"item": {"value": "soda"}}
    )

    response = await intent.async_handle(opp, "test", " OppShoppingListLastItems")

    assert (
        response.speech["plain"]["speech"]
        == "These are the top 3 items on your shopping list: soda, wine, beer"
    )


async def test_deprecated_api_get_all(opp, opp_client, sl_setup):
    """Test the API."""

    await intent.async_handle(
        opp. "test", " OppShoppingListAddItem", {"item": {"value": "beer"}}
    )
    await intent.async_handle(
        opp. "test", " OppShoppingListAddItem", {"item": {"value": "wine"}}
    )

    client = await opp_client()
    resp = await client.get("/api/shopping_list")

    assert resp.status == 200
    data = await resp.json()
    assert len(data) == 2
    assert data[0]["name"] == "beer"
    assert not data[0]["complete"]
    assert data[1]["name"] == "wine"
    assert not data[1]["complete"]


async def test_ws_get_items(opp, opp_ws_client, sl_setup):
    """Test get shopping_list items websocket command."""

    await intent.async_handle(
        opp. "test", " OppShoppingListAddItem", {"item": {"value": "beer"}}
    )
    await intent.async_handle(
        opp. "test", " OppShoppingListAddItem", {"item": {"value": "wine"}}
    )

    client = await opp_ws_client.opp)

    await client.send_json({"id": 5, "type": "shopping_list/items"})
    msg = await client.receive_json()
    assert msg["success"] is True

    assert msg["id"] == 5
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]
    data = msg["result"]
    assert len(data) == 2
    assert data[0]["name"] == "beer"
    assert not data[0]["complete"]
    assert data[1]["name"] == "wine"
    assert not data[1]["complete"]


async def test_deprecated_api_update(opp, opp_client, sl_setup):
    """Test the API."""

    await intent.async_handle(
        opp. "test", " OppShoppingListAddItem", {"item": {"value": "beer"}}
    )
    await intent.async_handle(
        opp. "test", " OppShoppingListAddItem", {"item": {"value": "wine"}}
    )

    beer_id = opp.data["shopping_list"].items[0]["id"]
    wine_id = opp.data["shopping_list"].items[1]["id"]

    client = await opp_client()
    resp = await client.post(
        f"/api/shopping_list/item/{beer_id}", json={"name": "soda"}
    )

    assert resp.status == 200
    data = await resp.json()
    assert data == {"id": beer_id, "name": "soda", "complete": False}

    resp = await client.post(
        f"/api/shopping_list/item/{wine_id}", json={"complete": True}
    )

    assert resp.status == 200
    data = await resp.json()
    assert data == {"id": wine_id, "name": "wine", "complete": True}

    beer, wine = opp.data["shopping_list"].items
    assert beer == {"id": beer_id, "name": "soda", "complete": False}
    assert wine == {"id": wine_id, "name": "wine", "complete": True}


async def test_ws_update_item(opp, opp_ws_client, sl_setup):
    """Test update shopping_list item websocket command."""
    await intent.async_handle(
        opp. "test", " OppShoppingListAddItem", {"item": {"value": "beer"}}
    )
    await intent.async_handle(
        opp. "test", " OppShoppingListAddItem", {"item": {"value": "wine"}}
    )

    beer_id = opp.data["shopping_list"].items[0]["id"]
    wine_id = opp.data["shopping_list"].items[1]["id"]
    client = await opp_ws_client.opp)
    await client.send_json(
        {
            "id": 5,
            "type": "shopping_list/items/update",
            "item_id": beer_id,
            "name": "soda",
        }
    )
    msg = await client.receive_json()
    assert msg["success"] is True
    data = msg["result"]
    assert data == {"id": beer_id, "name": "soda", "complete": False}
    await client.send_json(
        {
            "id": 6,
            "type": "shopping_list/items/update",
            "item_id": wine_id,
            "complete": True,
        }
    )
    msg = await client.receive_json()
    assert msg["success"] is True
    data = msg["result"]
    assert data == {"id": wine_id, "name": "wine", "complete": True}

    beer, wine = opp.data["shopping_list"].items
    assert beer == {"id": beer_id, "name": "soda", "complete": False}
    assert wine == {"id": wine_id, "name": "wine", "complete": True}


async def test_api_update_fails(opp, opp_client, sl_setup):
    """Test the API."""

    await intent.async_handle(
        opp. "test", " OppShoppingListAddItem", {"item": {"value": "beer"}}
    )

    client = await opp_client()
    resp = await client.post("/api/shopping_list/non_existing", json={"name": "soda"})

    assert resp.status == HTTP_NOT_FOUND

    beer_id = opp.data["shopping_list"].items[0]["id"]
    resp = await client.post(f"/api/shopping_list/item/{beer_id}", json={"name": 123})

    assert resp.status == 400


async def test_ws_update_item_fail(opp, opp_ws_client, sl_setup):
    """Test failure of update shopping_list item websocket command."""
    await intent.async_handle(
        opp. "test", " OppShoppingListAddItem", {"item": {"value": "beer"}}
    )
    client = await opp_ws_client.opp)
    await client.send_json(
        {
            "id": 5,
            "type": "shopping_list/items/update",
            "item_id": "non_existing",
            "name": "soda",
        }
    )
    msg = await client.receive_json()
    assert msg["success"] is False
    data = msg["error"]
    assert data == {"code": "item_not_found", "message": "Item not found"}
    await client.send_json({"id": 6, "type": "shopping_list/items/update", "name": 123})
    msg = await client.receive_json()
    assert msg["success"] is False


async def test_deprecated_api_clear_completed(opp, opp_client, sl_setup):
    """Test the API."""

    await intent.async_handle(
        opp. "test", " OppShoppingListAddItem", {"item": {"value": "beer"}}
    )
    await intent.async_handle(
        opp. "test", " OppShoppingListAddItem", {"item": {"value": "wine"}}
    )

    beer_id = opp.data["shopping_list"].items[0]["id"]
    wine_id = opp.data["shopping_list"].items[1]["id"]

    client = await opp_client()

    # Mark beer as completed
    resp = await client.post(
        f"/api/shopping_list/item/{beer_id}", json={"complete": True}
    )
    assert resp.status == 200

    resp = await client.post("/api/shopping_list/clear_completed")
    assert resp.status == 200

    items = opp.data["shopping_list"].items
    assert len(items) == 1

    assert items[0] == {"id": wine_id, "name": "wine", "complete": False}


async def test_ws_clear_items(opp, opp_ws_client, sl_setup):
    """Test clearing shopping_list items websocket command."""
    await intent.async_handle(
        opp. "test", " OppShoppingListAddItem", {"item": {"value": "beer"}}
    )
    await intent.async_handle(
        opp. "test", " OppShoppingListAddItem", {"item": {"value": "wine"}}
    )
    beer_id = opp.data["shopping_list"].items[0]["id"]
    wine_id = opp.data["shopping_list"].items[1]["id"]
    client = await opp_ws_client.opp)
    await client.send_json(
        {
            "id": 5,
            "type": "shopping_list/items/update",
            "item_id": beer_id,
            "complete": True,
        }
    )
    msg = await client.receive_json()
    assert msg["success"] is True
    await client.send_json({"id": 6, "type": "shopping_list/items/clear"})
    msg = await client.receive_json()
    assert msg["success"] is True
    items = opp.data["shopping_list"].items
    assert len(items) == 1
    assert items[0] == {"id": wine_id, "name": "wine", "complete": False}


async def test_deprecated_api_create(opp, opp_client, sl_setup):
    """Test the API."""

    client = await opp_client()
    resp = await client.post("/api/shopping_list/item", json={"name": "soda"})

    assert resp.status == 200
    data = await resp.json()
    assert data["name"] == "soda"
    assert data["complete"] is False

    items = opp.data["shopping_list"].items
    assert len(items) == 1
    assert items[0]["name"] == "soda"
    assert items[0]["complete"] is False


async def test_deprecated_api_create_fail(opp, opp_client, sl_setup):
    """Test the API."""

    client = await opp_client()
    resp = await client.post("/api/shopping_list/item", json={"name": 1234})

    assert resp.status == 400
    assert len.opp.data["shopping_list"].items) == 0


async def test_ws_add_item(opp, opp_ws_client, sl_setup):
    """Test adding shopping_list item websocket command."""
    client = await opp_ws_client.opp)
    await client.send_json({"id": 5, "type": "shopping_list/items/add", "name": "soda"})
    msg = await client.receive_json()
    assert msg["success"] is True
    data = msg["result"]
    assert data["name"] == "soda"
    assert data["complete"] is False
    items = opp.data["shopping_list"].items
    assert len(items) == 1
    assert items[0]["name"] == "soda"
    assert items[0]["complete"] is False


async def test_ws_add_item_fail(opp, opp_ws_client, sl_setup):
    """Test adding shopping_list item failure websocket command."""
    client = await opp_ws_client.opp)
    await client.send_json({"id": 5, "type": "shopping_list/items/add", "name": 123})
    msg = await client.receive_json()
    assert msg["success"] is False
    assert len.opp.data["shopping_list"].items) == 0


async def test_ws_reorder_items(opp, opp_ws_client, sl_setup):
    """Test reordering shopping_list items websocket command."""
    await intent.async_handle(
        opp. "test", " OppShoppingListAddItem", {"item": {"value": "beer"}}
    )
    await intent.async_handle(
        opp. "test", " OppShoppingListAddItem", {"item": {"value": "wine"}}
    )
    await intent.async_handle(
        opp. "test", " OppShoppingListAddItem", {"item": {"value": "apple"}}
    )

    beer_id = opp.data["shopping_list"].items[0]["id"]
    wine_id = opp.data["shopping_list"].items[1]["id"]
    apple_id = opp.data["shopping_list"].items[2]["id"]

    client = await opp_ws_client.opp)
    await client.send_json(
        {
            "id": 6,
            "type": "shopping_list/items/reorder",
            "item_ids": [wine_id, apple_id, beer_id],
        }
    )
    msg = await client.receive_json()
    assert msg["success"] is True
    assert opp.data["shopping_list"].items[0] == {
        "id": wine_id,
        "name": "wine",
        "complete": False,
    }
    assert opp.data["shopping_list"].items[1] == {
        "id": apple_id,
        "name": "apple",
        "complete": False,
    }
    assert opp.data["shopping_list"].items[2] == {
        "id": beer_id,
        "name": "beer",
        "complete": False,
    }

    # Mark wine as completed.
    await client.send_json(
        {
            "id": 7,
            "type": "shopping_list/items/update",
            "item_id": wine_id,
            "complete": True,
        }
    )
    _ = await client.receive_json()

    await client.send_json(
        {
            "id": 8,
            "type": "shopping_list/items/reorder",
            "item_ids": [apple_id, beer_id],
        }
    )
    msg = await client.receive_json()
    assert msg["success"] is True
    assert opp.data["shopping_list"].items[0] == {
        "id": apple_id,
        "name": "apple",
        "complete": False,
    }
    assert opp.data["shopping_list"].items[1] == {
        "id": beer_id,
        "name": "beer",
        "complete": False,
    }
    assert opp.data["shopping_list"].items[2] == {
        "id": wine_id,
        "name": "wine",
        "complete": True,
    }


async def test_ws_reorder_items_failure(opp, opp_ws_client, sl_setup):
    """Test reordering shopping_list items websocket command."""
    await intent.async_handle(
        opp. "test", " OppShoppingListAddItem", {"item": {"value": "beer"}}
    )
    await intent.async_handle(
        opp. "test", " OppShoppingListAddItem", {"item": {"value": "wine"}}
    )
    await intent.async_handle(
        opp. "test", " OppShoppingListAddItem", {"item": {"value": "apple"}}
    )

    beer_id = opp.data["shopping_list"].items[0]["id"]
    wine_id = opp.data["shopping_list"].items[1]["id"]
    apple_id = opp.data["shopping_list"].items[2]["id"]

    client = await opp_ws_client.opp)

    # Testing sending bad item id.
    await client.send_json(
        {
            "id": 8,
            "type": "shopping_list/items/reorder",
            "item_ids": [wine_id, apple_id, beer_id, "BAD_ID"],
        }
    )
    msg = await client.receive_json()
    assert msg["success"] is False
    assert msg["error"]["code"] == ERR_NOT_FOUND

    # Testing not sending all unchecked item ids.
    await client.send_json(
        {
            "id": 9,
            "type": "shopping_list/items/reorder",
            "item_ids": [wine_id, apple_id],
        }
    )
    msg = await client.receive_json()
    assert msg["success"] is False
    assert msg["error"]["code"] == ERR_INVALID_FORMAT
