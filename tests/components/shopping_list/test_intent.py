"""Test Shopping List intents."""
from openpeerpower.helpers import intent


async def test_recent_items_intent.opp, sl_setup):
    """Test recent items."""
    await intent.async_handle(
        opp, "test", "HassShoppingListAddItem", {"item": {"value": "beer"}}
    )
    await intent.async_handle(
        opp, "test", "HassShoppingListAddItem", {"item": {"value": "wine"}}
    )
    await intent.async_handle(
        opp, "test", "HassShoppingListAddItem", {"item": {"value": "soda"}}
    )

    response = await intent.async_handle.opp, "test", "HassShoppingListLastItems")

    assert (
        response.speech["plain"]["speech"]
        == "These are the top 3 items on your shopping list: soda, wine, beer"
    )
