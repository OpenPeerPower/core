"""Intents for the Shopping List integration."""
from openpeerpower.helpers import intent
import openpeerpower.helpers.config_validation as cv

from . import DOMAIN, EVENT

INTENT_ADD_ITEM = "OppShoppingListAddItem"
INTENT_LAST_ITEMS = "OppShoppingListLastItems"


async def async_setup_intents(opp):
    """Set up the Shopping List intents."""
    intent.async_register(opp, AddItemIntent())
    intent.async_register(opp, ListTopItemsIntent())


class AddItemIntent(intent.IntentHandler):
    """Handle AddItem intents."""

    intent_type = INTENT_ADD_ITEM
    slot_schema = {"item": cv.string}

    async def async_handle(self, intent_obj):
        """Handle the intent."""
        slots = self.async_validate_slots(intent_obj.slots)
        item = slots["item"]["value"]
        await intent_obj.opp.data[DOMAIN].async_add(item)

        response = intent_obj.create_response()
        response.async_set_speech(f"I've added {item} to your shopping list")
        intent_obj.opp.bus.async_fire(EVENT)
        return response


class ListTopItemsIntent(intent.IntentHandler):
    """Handle AddItem intents."""

    intent_type = INTENT_LAST_ITEMS
    slot_schema = {"item": cv.string}

    async def async_handle(self, intent_obj):
        """Handle the intent."""
        items = intent_obj.opp.data[DOMAIN].items[-5:]
        response = intent_obj.create_response()

        if not items:
            response.async_set_speech("There are no items on your shopping list")
        else:
            response.async_set_speech(
                "These are the top {} items on your shopping list: {}".format(
                    min(len(items), 5),
                    ", ".join(itm["name"] for itm in reversed(items)),
                )
            )
        return response
