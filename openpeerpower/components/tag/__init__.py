"""The Tag integration."""
import logging
import typing
import uuid

import voluptuous as vol

from openpeerpower.const import CONF_NAME
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.exceptions import OpenPeerPowerError
from openpeerpower.helpers import collection
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.storage import Store
from openpeerpower.loader import bind.opp
import openpeerpower.util.dt as dt_util

from .const import DEVICE_ID, DOMAIN, EVENT_TAG_SCANNED, TAG_ID

_LOGGER = logging.getLogger(__name__)

LAST_SCANNED = "last_scanned"
STORAGE_KEY = DOMAIN
STORAGE_VERSION = 1
TAGS = "tags"

CREATE_FIELDS = {
    vol.Optional(TAG_ID): cv.string,
    vol.Optional(CONF_NAME): vol.All(str, vol.Length(min=1)),
    vol.Optional("description"): cv.string,
    vol.Optional(LAST_SCANNED): cv.datetime,
}

UPDATE_FIELDS = {
    vol.Optional(CONF_NAME): vol.All(str, vol.Length(min=1)),
    vol.Optional("description"): cv.string,
    vol.Optional(LAST_SCANNED): cv.datetime,
}


class TagIDExistsError(OpenPeerPowerError):
    """Raised when an item is not found."""

    def __init__(self, item_id: str):
        """Initialize tag ID exists error."""
        super().__init__(f"Tag with ID {item_id} already exists.")
        self.item_id = item_id


class TagIDManager(collection.IDManager):
    """ID manager for tags."""

    def generate_id(self, suggestion: str) -> str:
        """Generate an ID."""
        if self.has_id(suggestion):
            raise TagIDExistsError(suggestion)

        return suggestion


class TagStorageCollection(collection.StorageCollection):
    """Tag collection stored in storage."""

    CREATE_SCHEMA = vol.Schema(CREATE_FIELDS)
    UPDATE_SCHEMA = vol.Schema(UPDATE_FIELDS)

    async def _process_create_data(self, data: typing.Dict) -> typing.Dict:
        """Validate the config is valid."""
        data = self.CREATE_SCHEMA(data)
        if not data[TAG_ID]:
            data[TAG_ID] = str(uuid.uuid4())
        # make last_scanned JSON serializeable
        if LAST_SCANNED in data:
            data[LAST_SCANNED] = data[LAST_SCANNED].isoformat()
        return data

    @callback
    def _get_suggested_id(self, info: typing.Dict) -> str:
        """Suggest an ID based on the config."""
        return info[TAG_ID]

    async def _update_data(self, data: dict, update_data: typing.Dict) -> typing.Dict:
        """Return a new updated data object."""
        data = {**data, **self.UPDATE_SCHEMA(update_data)}
        # make last_scanned JSON serializeable
        if LAST_SCANNED in update_data:
            data[LAST_SCANNED] = data[LAST_SCANNED].isoformat()
        return data


async def async_setup_opp: OpenPeerPower, config: dict):
    """Set up the Tag component."""
    opp.data[DOMAIN] = {}
    id_manager = TagIDManager()
    opp.data[DOMAIN][TAGS] = storage_collection = TagStorageCollection(
        Store.opp, STORAGE_VERSION, STORAGE_KEY),
        logging.getLogger(f"{__name__}.storage_collection"),
        id_manager,
    )
    await storage_collection.async_load()
    collection.StorageCollectionWebsocket(
        storage_collection, DOMAIN, DOMAIN, CREATE_FIELDS, UPDATE_FIELDS
    ).async_setup_opp)

    return True


@bind.opp
async def async_scan_tag.opp, tag_id, device_id, context=None):
    """Handle when a tag is scanned."""
    if DOMAIN not in.opp.config.components:
        raise OpenPeerPowerError("tag component has not been set up.")

    opp.bus.async_fire(
        EVENT_TAG_SCANNED, {TAG_ID: tag_id, DEVICE_ID: device_id}, context=context
    )
    helper = opp.data[DOMAIN][TAGS]
    if tag_id in helper.data:
        await helper.async_update_item(tag_id, {LAST_SCANNED: dt_util.utcnow()})
    else:
        await helper.async_create_item({TAG_ID: tag_id, LAST_SCANNED: dt_util.utcnow()})
    _LOGGER.debug("Tag: %s scanned by device: %s", tag_id, device_id)
