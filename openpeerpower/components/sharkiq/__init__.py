"""Shark IQ Integration."""

import asyncio

import async_timeout
from sharkiqpy import (
    AylaApi,
    SharkIqAuthError,
    SharkIqAuthExpiringError,
    SharkIqNotAuthedError,
    get_ayla_api,
)

from openpeerpower import exceptions
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME

from .const import _LOGGER, API_TIMEOUT, DOMAIN, PLATFORMS
from .update_coordinator import SharkIqUpdateCoordinator


class CannotConnect(exceptions.OpenPeerPowerError):
    """Error to indicate we cannot connect."""


async def async_setup(opp, config):
    """Set up the sharkiq environment."""
    opp.data.setdefault(DOMAIN, {})
    return True


async def async_connect_or_timeout(ayla_api: AylaApi) -> bool:
    """Connect to vacuum."""
    try:
        with async_timeout.timeout(API_TIMEOUT):
            _LOGGER.debug("Initialize connection to Ayla networks API")
            await ayla_api.async_sign_in()
    except SharkIqAuthError:
        _LOGGER.error("Authentication error connecting to Shark IQ api")
        return False
    except asyncio.TimeoutError as exc:
        _LOGGER.error("Timeout expired")
        raise CannotConnect from exc

    return True


async def async_setup_entry(opp, config_entry):
    """Initialize the sharkiq platform via config entry."""
    ayla_api = get_ayla_api(
        username=config_entry.data[CONF_USERNAME],
        password=config_entry.data[CONF_PASSWORD],
        websession=opp.helpers.aiohttp_client.async_get_clientsession(),
    )

    try:
        if not await async_connect_or_timeout(ayla_api):
            return False
    except CannotConnect as exc:
        raise exceptions.ConfigEntryNotReady from exc

    shark_vacs = await ayla_api.async_get_devices(False)
    device_names = ", ".join([d.name for d in shark_vacs])
    _LOGGER.debug("Found %d Shark IQ device(s): %s", len(shark_vacs), device_names)
    coordinator = SharkIqUpdateCoordinator(opp, config_entry, ayla_api, shark_vacs)

    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise exceptions.ConfigEntryNotReady

    opp.data[DOMAIN][config_entry.entry_id] = coordinator

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    return True


async def async_disconnect_or_timeout(coordinator: SharkIqUpdateCoordinator):
    """Disconnect to vacuum."""
    _LOGGER.debug("Disconnecting from Ayla Api")
    with async_timeout.timeout(5):
        try:
            await coordinator.ayla_api.async_sign_out()
        except (SharkIqAuthError, SharkIqAuthExpiringError, SharkIqNotAuthedError):
            pass


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
        try:
            await async_disconnect_or_timeout(coordinator=domain_data)
        except SharkIqAuthError:
            pass
        opp.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok
