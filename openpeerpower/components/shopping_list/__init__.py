"""Support to manage a shopping list."""
import logging
import uuid

import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.components import http, websocket_api
from openpeerpower.components.http.data_validator import RequestDataValidator
from openpeerpower.const import HTTP_BAD_REQUEST, HTTP_NOT_FOUND
from openpeerpower.core import callback
import openpeerpower.helpers.config_validation as cv
from openpeerpower.util.json import load_json, save_json

from .const import DOMAIN

ATTR_NAME = "name"
ATTR_COMPLETE = "complete"

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = vol.Schema({DOMAIN: {}}, extra=vol.ALLOW_EXTRA)
EVENT = "shopping_list_updated"
ITEM_UPDATE_SCHEMA = vol.Schema({ATTR_COMPLETE: bool, ATTR_NAME: str})
PERSISTENCE = ".shopping_list.json"

SERVICE_ADD_ITEM = "add_item"
SERVICE_COMPLETE_ITEM = "complete_item"
SERVICE_INCOMPLETE_ITEM = "incomplete_item"
SERVICE_COMPLETE_ALL = "complete_all"
SERVICE_INCOMPLETE_ALL = "incomplete_all"
SERVICE_ITEM_SCHEMA = vol.Schema({vol.Required(ATTR_NAME): vol.Any(None, cv.string)})
SERVICE_LIST_SCHEMA = vol.Schema({})

WS_TYPE_SHOPPING_LIST_ITEMS = "shopping_list/items"
WS_TYPE_SHOPPING_LIST_ADD_ITEM = "shopping_list/items/add"
WS_TYPE_SHOPPING_LIST_UPDATE_ITEM = "shopping_list/items/update"
WS_TYPE_SHOPPING_LIST_CLEAR_ITEMS = "shopping_list/items/clear"

SCHEMA_WEBSOCKET_ITEMS = websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend(
    {vol.Required("type"): WS_TYPE_SHOPPING_LIST_ITEMS}
)

SCHEMA_WEBSOCKET_ADD_ITEM = websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend(
    {vol.Required("type"): WS_TYPE_SHOPPING_LIST_ADD_ITEM, vol.Required("name"): str}
)

SCHEMA_WEBSOCKET_UPDATE_ITEM = websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend(
    {
        vol.Required("type"): WS_TYPE_SHOPPING_LIST_UPDATE_ITEM,
        vol.Required("item_id"): str,
        vol.Optional("name"): str,
        vol.Optional("complete"): bool,
    }
)

SCHEMA_WEBSOCKET_CLEAR_ITEMS = websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend(
    {vol.Required("type"): WS_TYPE_SHOPPING_LIST_CLEAR_ITEMS}
)


async def async_setup(opp, config):
    """Initialize the shopping list."""

    if DOMAIN not in config:
        return True

    opp.async_create_task(
        opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}
        )
    )

    return True


async def async_setup_entry(opp, config_entry):
    """Set up shopping list from config flow."""

    async def add_item_service(call):
        """Add an item with `name`."""
        data = opp.data[DOMAIN]
        name = call.data.get(ATTR_NAME)
        if name is not None:
            await data.async_add(name)

    async def complete_item_service(call):
        """Mark the item provided via `name` as completed."""
        data = opp.data[DOMAIN]
        name = call.data.get(ATTR_NAME)
        if name is None:
            return
        try:
            item = [item for item in data.items if item["name"] == name][0]
        except IndexError:
            _LOGGER.error("Removing of item failed: %s cannot be found", name)
        else:
            await data.async_update(item["id"], {"name": name, "complete": True})

    async def incomplete_item_service(call):
        """Mark the item provided via `name` as incomplete."""
        data = opp.data[DOMAIN]
        name = call.data.get(ATTR_NAME)
        if name is None:
            return
        try:
            item = [item for item in data.items if item["name"] == name][0]
        except IndexError:
            _LOGGER.error("Restoring of item failed: %s cannot be found", name)
        else:
            await data.async_update(item["id"], {"name": name, "complete": False})

    async def complete_all_service(call):
        """Mark all items in the list as complete."""
        await data.async_update_list({"complete": True})

    async def incomplete_all_service(call):
        """Mark all items in the list as incomplete."""
        await data.async_update_list({"complete": False})

    data = opp.data[DOMAIN] = ShoppingData(opp)
    await data.async_load()

    opp.services.async_register(
        DOMAIN, SERVICE_ADD_ITEM, add_item_service, schema=SERVICE_ITEM_SCHEMA
    )
    opp.services.async_register(
        DOMAIN, SERVICE_COMPLETE_ITEM, complete_item_service, schema=SERVICE_ITEM_SCHEMA
    )
    opp.services.async_register(
        DOMAIN,
        SERVICE_INCOMPLETE_ITEM,
        incomplete_item_service,
        schema=SERVICE_ITEM_SCHEMA,
    )
    opp.services.async_register(
        DOMAIN,
        SERVICE_COMPLETE_ALL,
        complete_all_service,
        schema=SERVICE_LIST_SCHEMA,
    )
    opp.services.async_register(
        DOMAIN,
        SERVICE_INCOMPLETE_ALL,
        incomplete_all_service,
        schema=SERVICE_LIST_SCHEMA,
    )

    opp.http.register_view(ShoppingListView)
    opp.http.register_view(CreateShoppingListItemView)
    opp.http.register_view(UpdateShoppingListItemView)
    opp.http.register_view(ClearCompletedItemsView)

    opp.components.frontend.async_register_built_in_panel(
        "shopping-list", "shopping_list", "mdi:cart"
    )

    opp.components.websocket_api.async_register_command(
        WS_TYPE_SHOPPING_LIST_ITEMS, websocket_handle_items, SCHEMA_WEBSOCKET_ITEMS
    )
    opp.components.websocket_api.async_register_command(
        WS_TYPE_SHOPPING_LIST_ADD_ITEM, websocket_handle_add, SCHEMA_WEBSOCKET_ADD_ITEM
    )
    opp.components.websocket_api.async_register_command(
        WS_TYPE_SHOPPING_LIST_UPDATE_ITEM,
        websocket_handle_update,
        SCHEMA_WEBSOCKET_UPDATE_ITEM,
    )
    opp.components.websocket_api.async_register_command(
        WS_TYPE_SHOPPING_LIST_CLEAR_ITEMS,
        websocket_handle_clear,
        SCHEMA_WEBSOCKET_CLEAR_ITEMS,
    )

    websocket_api.async_register_command(opp, websocket_handle_reorder)

    return True


class ShoppingData:
    """Class to hold shopping list data."""

    def __init__(self, opp):
        """Initialize the shopping list."""
        self.opp = opp
        self.items = []

    async def async_add(self, name):
        """Add a shopping list item."""
        item = {"name": name, "id": uuid.uuid4().hex, "complete": False}
        self.items.append(item)
        await self.opp.async_add_executor_job(self.save)
        return item

    async def async_update(self, item_id, info):
        """Update a shopping list item."""
        item = next((itm for itm in self.items if itm["id"] == item_id), None)

        if item is None:
            raise KeyError

        info = ITEM_UPDATE_SCHEMA(info)
        item.update(info)
        await self.opp.async_add_executor_job(self.save)
        return item

    async def async_clear_completed(self):
        """Clear completed items."""
        self.items = [itm for itm in self.items if not itm["complete"]]
        await self.opp.async_add_executor_job(self.save)

    async def async_update_list(self, info):
        """Update all items in the list."""
        for item in self.items:
            item.update(info)
        await self.opp.async_add_executor_job(self.save)
        return self.items

    @callback
    def async_reorder(self, item_ids):
        """Reorder items."""
        # The array for sorted items.
        new_items = []
        all_items_mapping = {item["id"]: item for item in self.items}
        # Append items by the order of passed in array.
        for item_id in item_ids:
            if item_id not in all_items_mapping:
                raise KeyError
            new_items.append(all_items_mapping[item_id])
            # Remove the item from mapping after it's appended in the result array.
            del all_items_mapping[item_id]
        # Append the rest of the items
        for key in all_items_mapping:
            # All the unchecked items must be passed in the item_ids array,
            # so all items left in the mapping should be checked items.
            if all_items_mapping[key]["complete"] is False:
                raise vol.Invalid(
                    "The item ids array doesn't contain all the unchecked shopping list items."
                )
            new_items.append(all_items_mapping[key])
        self.items = new_items
        self.opp.async_add_executor_job(self.save)

    async def async_load(self):
        """Load items."""

        def load():
            """Load the items synchronously."""
            return load_json(self.opp.config.path(PERSISTENCE), default=[])

        self.items = await self.opp.async_add_executor_job(load)

    def save(self):
        """Save the items."""
        save_json(self.opp.config.path(PERSISTENCE), self.items)


class ShoppingListView(http.OpenPeerPowerView):
    """View to retrieve shopping list content."""

    url = "/api/shopping_list"
    name = "api:shopping_list"

    @callback
    def get(self, request):
        """Retrieve shopping list items."""
        return self.json(request.app["opp"].data[DOMAIN].items)


class UpdateShoppingListItemView(http.OpenPeerPowerView):
    """View to retrieve shopping list content."""

    url = "/api/shopping_list/item/{item_id}"
    name = "api:shopping_list:item:id"

    async def post(self, request, item_id):
        """Update a shopping list item."""
        data = await request.json()

        try:
            item = await request.app["opp"].data[DOMAIN].async_update(item_id, data)
            request.app["opp"].bus.async_fire(EVENT)
            return self.json(item)
        except KeyError:
            return self.json_message("Item not found", HTTP_NOT_FOUND)
        except vol.Invalid:
            return self.json_message("Item not found", HTTP_BAD_REQUEST)


class CreateShoppingListItemView(http.OpenPeerPowerView):
    """View to retrieve shopping list content."""

    url = "/api/shopping_list/item"
    name = "api:shopping_list:item"

    @RequestDataValidator(vol.Schema({vol.Required("name"): str}))
    async def post(self, request, data):
        """Create a new shopping list item."""
        item = await request.app["opp"].data[DOMAIN].async_add(data["name"])
        request.app["opp"].bus.async_fire(EVENT)
        return self.json(item)


class ClearCompletedItemsView(http.OpenPeerPowerView):
    """View to retrieve shopping list content."""

    url = "/api/shopping_list/clear_completed"
    name = "api:shopping_list:clear_completed"

    async def post(self, request):
        """Retrieve if API is running."""
        opp = request.app["opp"]
        await opp.data[DOMAIN].async_clear_completed()
        opp.bus.async_fire(EVENT)
        return self.json_message("Cleared completed items.")


@callback
def websocket_handle_items(opp, connection, msg):
    """Handle get shopping_list items."""
    connection.send_message(
        websocket_api.result_message(msg["id"], opp.data[DOMAIN].items)
    )


@websocket_api.async_response
async def websocket_handle_add(opp, connection, msg):
    """Handle add item to shopping_list."""
    item = await opp.data[DOMAIN].async_add(msg["name"])
    opp.bus.async_fire(EVENT, {"action": "add", "item": item})
    connection.send_message(websocket_api.result_message(msg["id"], item))


@websocket_api.async_response
async def websocket_handle_update(opp, connection, msg):
    """Handle update shopping_list item."""
    msg_id = msg.pop("id")
    item_id = msg.pop("item_id")
    msg.pop("type")
    data = msg

    try:
        item = await opp.data[DOMAIN].async_update(item_id, data)
        opp.bus.async_fire(EVENT, {"action": "update", "item": item})
        connection.send_message(websocket_api.result_message(msg_id, item))
    except KeyError:
        connection.send_message(
            websocket_api.error_message(msg_id, "item_not_found", "Item not found")
        )


@websocket_api.async_response
async def websocket_handle_clear(opp, connection, msg):
    """Handle clearing shopping_list items."""
    await opp.data[DOMAIN].async_clear_completed()
    opp.bus.async_fire(EVENT, {"action": "clear"})
    connection.send_message(websocket_api.result_message(msg["id"]))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "shopping_list/items/reorder",
        vol.Required("item_ids"): [str],
    }
)
def websocket_handle_reorder(opp, connection, msg):
    """Handle reordering shopping_list items."""
    msg_id = msg.pop("id")
    try:
        opp.data[DOMAIN].async_reorder(msg.pop("item_ids"))
        opp.bus.async_fire(EVENT, {"action": "reorder"})
        connection.send_result(msg_id)
    except KeyError:
        connection.send_error(
            msg_id,
            websocket_api.const.ERR_NOT_FOUND,
            "One or more item id(s) not found.",
        )
    except vol.Invalid as err:
        connection.send_error(msg_id, websocket_api.const.ERR_INVALID_FORMAT, f"{err}")
