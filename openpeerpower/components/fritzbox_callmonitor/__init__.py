"""The fritzbox_callmonitor integration."""
from asyncio import gather
import logging

from fritzconnection.core.exceptions import FritzConnectionException, FritzSecurityError
from requests.exceptions import ConnectionError as RequestsConnectionError

from openpeerpower.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from openpeerpower.exceptions import ConfigEntryNotReady

from .base import FritzBoxPhonebook
from .const import (
    CONF_PHONEBOOK,
    CONF_PREFIXES,
    DOMAIN,
    FRITZBOX_PHONEBOOK,
    PLATFORMS,
    UNDO_UPDATE_LISTENER,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup(opp, config):
    """Set up the fritzbox_callmonitor integration."""
    return True


async def async_setup_entry(opp, config_entry):
    """Set up the fritzbox_callmonitor platforms."""
    fritzbox_phonebook = FritzBoxPhonebook(
        host=config_entry.data[CONF_HOST],
        username=config_entry.data[CONF_USERNAME],
        password=config_entry.data[CONF_PASSWORD],
        phonebook_id=config_entry.data[CONF_PHONEBOOK],
        prefixes=config_entry.options.get(CONF_PREFIXES),
    )

    try:
        await opp.async_add_executor_job(fritzbox_phonebook.init_phonebook)
    except FritzSecurityError as ex:
        _LOGGER.error(
            "User has insufficient permissions to access AVM FRITZ!Box settings and its phonebooks: %s",
            ex,
        )
        return False
    except FritzConnectionException as ex:
        _LOGGER.error("Invalid authentication: %s", ex)
        return False
    except RequestsConnectionError as ex:
        _LOGGER.error("Unable to connect to AVM FRITZ!Box call monitor: %s", ex)
        raise ConfigEntryNotReady from ex

    undo_listener = config_entry.add_update_listener(update_listener)

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][config_entry.entry_id] = {
        FRITZBOX_PHONEBOOK: fritzbox_phonebook,
        UNDO_UPDATE_LISTENER: undo_listener,
    }

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    return True


async def async_unload_entry(opp, config_entry):
    """Unloading the fritzbox_callmonitor platforms."""

    unload_ok = all(
        await gather(
            *[
                opp.config_entries.async_forward_entry_unload(config_entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    opp.data[DOMAIN][config_entry.entry_id][UNDO_UPDATE_LISTENER]()

    if unload_ok:
        opp.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok


async def update_listener(opp, config_entry):
    """Update listener to reload after option has changed."""
    await opp.config_entries.async_reload(config_entry.entry_id)
