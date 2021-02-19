"""Test Shopping List intents."""
from openpeerpowerr.helpers import intent


async def test_recent_items_intent.opp, sl_setup):
    """Test recent items."""
    await intent.async_op.dle(
       .opp, "test", "OppShoppingListAddItem", {"item": {"value": "beer"}}
    )
    await intent.async_op.dle(
       .opp, "test", "OppShoppingListAddItem", {"item": {"value": "wine"}}
    )
    await intent.async_op.dle(
       .opp, "test", "OppShoppingListAddItem", {"item": {"value": "soda"}}
    )

    response = await intent.async_op.dle.opp, "test", "OppShoppingListLastItems")

    assert (
        response.speech["plain"]["speech"]
        == "These are the top 3 items on your shopping list: soda, wine, beer"
    )
