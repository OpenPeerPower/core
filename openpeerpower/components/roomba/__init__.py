"""The roomba component."""
import asyncio
import logging

import async_timeout
from roombapy import Roomba, RoombaConnectionError

from openpeerpower import exceptions
from openpeerpower.const import CONF_DELAY, CONF_HOST, CONF_NAME, CONF_PASSWORD

from .const import BLID, CONF_BLID, CONF_CONTINUOUS, DOMAIN, PLATFORMS, ROOMBA_SESSION

_LOGGER = logging.getLogger(__name__)


async def async_setup(opp, config):
    """Set up the roomba environment."""
    opp.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(opp, config_entry):
    """Set the config entry up."""
    # Set up roomba platforms with config entry

    if not config_entry.options:
        opp.config_entries.async_update_entry(
            config_entry,
            options={
                CONF_CONTINUOUS: config_entry.data[CONF_CONTINUOUS],
                CONF_DELAY: config_entry.data[CONF_DELAY],
            },
        )

    roomba = Roomba(
        address=config_entry.data[CONF_HOST],
        blid=config_entry.data[CONF_BLID],
        password=config_entry.data[CONF_PASSWORD],
        continuous=config_entry.options[CONF_CONTINUOUS],
        delay=config_entry.options[CONF_DELAY],
    )

    try:
        if not await async_connect_or_timeout(opp, roomba):
            return False
    except CannotConnect as err:
        raise exceptions.ConfigEntryNotReady from err

    opp.data[DOMAIN][config_entry.entry_id] = {
        ROOMBA_SESSION: roomba,
        BLID: config_entry.data[CONF_BLID],
    }

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    if not config_entry.update_listeners:
        config_entry.add_update_listener(async_update_options)

    return True


async def async_connect_or_timeout(opp, roomba):
    """Connect to vacuum."""
    try:
        name = None
        with async_timeout.timeout(10):
            _LOGGER.debug("Initialize connection to vacuum")
            await opp.async_add_executor_job(roomba.connect)
            while not roomba.roomba_connected or name is None:
                # Waiting for connection and check datas ready
                name = roomba_reported_state(roomba).get("name", None)
                if name:
                    break
                await asyncio.sleep(1)
    except RoombaConnectionError as err:
        _LOGGER.error("Error to connect to vacuum")
        raise CannotConnect from err
    except asyncio.TimeoutError as err:
        # api looping if user or password incorrect and roomba exist
        await async_disconnect_or_timeout(opp, roomba)
        _LOGGER.error("Timeout expired")
        raise CannotConnect from err

    return {ROOMBA_SESSION: roomba, CONF_NAME: name}


async def async_disconnect_or_timeout(opp, roomba):
    """Disconnect to vacuum."""
    _LOGGER.debug("Disconnect vacuum")
    with async_timeout.timeout(3):
        await opp.async_add_executor_job(roomba.disconnect)
    return True


async def async_update_options(opp, config_entry):
    """Update options."""
    await opp.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(opp, config_entry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(config_entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        domain_data = opp.data[DOMAIN][config_entry.entry_id]
        await async_disconnect_or_timeout(opp, roomba=domain_data[ROOMBA_SESSION])
        opp.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok


def roomba_reported_state(roomba):
    """Roomba report."""
    return roomba.master_state.get("state", {}).get("reported", {})


class CannotConnect(exceptions.OpenPeerPowerError):
    """Error to indicate we cannot connect."""
