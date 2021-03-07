"""The Logitech Harmony Hub integration."""
import asyncio
import logging

from openpeerpower.components.remote import ATTR_ACTIVITY, ATTR_DELAY_SECS
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_HOST, CONF_NAME
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import entity_registry
from openpeerpower.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, HARMONY_OPTIONS_UPDATE, PLATFORMS
from .data import HarmonyData

_LOGGER = logging.getLogger(__name__)


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the Logitech Harmony Hub component."""
    opp.data.setdefault(DOMAIN, {})

    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Logitech Harmony Hub from a config entry."""
    # As there currently is no way to import options from yaml
    # when setting up a config entry, we fallback to adding
    # the options to the config entry and pull them out here if
    # they are missing from the options
    _async_import_options_from_data_if_missing(opp, entry)

    address = entry.data[CONF_HOST]
    name = entry.data[CONF_NAME]
    data = HarmonyData(opp, address, name, entry.unique_id)
    try:
        connected_ok = await data.connect()
    except (asyncio.TimeoutError, ValueError, AttributeError) as err:
        raise ConfigEntryNotReady from err

    if not connected_ok:
        raise ConfigEntryNotReady

    opp.data[DOMAIN][entry.entry_id] = data

    await _migrate_old_unique_ids(opp, entry.entry_id, data)

    entry.add_update_listener(_update_listener)

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def _migrate_old_unique_ids(opp: OpenPeerPower, entry_id: str, data: HarmonyData):
    names_to_ids = {activity["label"]: activity["id"] for activity in data.activities}

    @callback
    def _async_migrator(entity_entry: entity_registry.RegistryEntry):
        # Old format for switches was {remote_unique_id}-{activity_name}
        # New format is activity_{activity_id}
        parts = entity_entry.unique_id.split("-", 1)
        if len(parts) > 1:  # old format
            activity_name = parts[1]
            activity_id = names_to_ids.get(activity_name)

            if activity_id is not None:
                _LOGGER.info(
                    "Migrating unique_id from [%s] to [%s]",
                    entity_entry.unique_id,
                    activity_id,
                )
                return {"new_unique_id": f"activity_{activity_id}"}

        return None

    await entity_registry.async_migrate_entries(opp, entry_id, _async_migrator)


@callback
def _async_import_options_from_data_if_missing(opp: OpenPeerPower, entry: ConfigEntry):
    options = dict(entry.options)
    modified = 0
    for importable_option in [ATTR_ACTIVITY, ATTR_DELAY_SECS]:
        if importable_option not in entry.options and importable_option in entry.data:
            options[importable_option] = entry.data[importable_option]
            modified = 1

    if modified:
        opp.config_entries.async_update_entry(entry, options=options)


async def _update_listener(opp: OpenPeerPower, entry: ConfigEntry):
    """Handle options update."""
    async_dispatcher_send(
        opp, f"{HARMONY_OPTIONS_UPDATE}-{entry.unique_id}", entry.options
    )


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    # Shutdown a harmony remote for removal
    data = opp.data[DOMAIN][entry.entry_id]
    await data.shutdown()

    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
