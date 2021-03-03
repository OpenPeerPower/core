"""The StarLine component."""
import voluptuous as vol

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_SCAN_INTERVAL
from openpeerpower.core import Config, OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady

from .account import StarlineAccount
from .const import (
    CONF_SCAN_OBD_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SCAN_OBD_INTERVAL,
    DOMAIN,
    PLATFORMS,
    SERVICE_SET_SCAN_INTERVAL,
    SERVICE_SET_SCAN_OBD_INTERVAL,
    SERVICE_UPDATE_STATE,
)


async def async_setup(opp: OpenPeerPower, config: Config) -> bool:
    """Set up configured StarLine."""
    return True


async def async_setup_entry(opp: OpenPeerPower, config_entry: ConfigEntry) -> bool:
    """Set up the StarLine device from a config entry."""
    account = StarlineAccount(opp, config_entry)
    await account.update()
    await account.update_obd()
    if not account.api.available:
        raise ConfigEntryNotReady

    if DOMAIN not in opp.data:
        opp.data[DOMAIN] = {}
    opp.data[DOMAIN][config_entry.entry_id] = account

    device_registry = await opp.helpers.device_registry.async_get_registry()
    for device in account.api.devices.values():
        device_registry.async_get_or_create(
            config_entry_id=config_entry.entry_id, **account.device_info(device)
        )

    for domain in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(config_entry, domain)
        )

    async def async_set_scan_interval(call):
        """Set scan interval."""
        options = dict(config_entry.options)
        options[CONF_SCAN_INTERVAL] = call.data[CONF_SCAN_INTERVAL]
        opp.config_entries.async_update_entry(entry=config_entry, options=options)

    async def async_set_scan_obd_interval(call):
        """Set OBD info scan interval."""
        options = dict(config_entry.options)
        options[CONF_SCAN_OBD_INTERVAL] = call.data[CONF_SCAN_INTERVAL]
        opp.config_entries.async_update_entry(entry=config_entry, options=options)

    async def async_update(call=None):
        """Update all data."""
        await account.update()
        await account.update_obd()

    opp.services.async_register(DOMAIN, SERVICE_UPDATE_STATE, async_update)
    opp.services.async_register(
        DOMAIN,
        SERVICE_SET_SCAN_INTERVAL,
        async_set_scan_interval,
        schema=vol.Schema(
            {
                vol.Required(CONF_SCAN_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=10)
                )
            }
        ),
    )
    opp.services.async_register(
        DOMAIN,
        SERVICE_SET_SCAN_OBD_INTERVAL,
        async_set_scan_obd_interval,
        schema=vol.Schema(
            {
                vol.Required(CONF_SCAN_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=180)
                )
            }
        ),
    )

    config_entry.add_update_listener(async_options_updated)
    await async_options_updated(opp, config_entry)

    return True


async def async_unload_entry(opp: OpenPeerPower, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    for domain in PLATFORMS:
        await opp.config_entries.async_forward_entry_unload(config_entry, domain)

    account: StarlineAccount = opp.data[DOMAIN][config_entry.entry_id]
    account.unload()
    return True


async def async_options_updated(opp: OpenPeerPower, config_entry: ConfigEntry) -> None:
    """Triggered by config entry options updates."""
    account: StarlineAccount = opp.data[DOMAIN][config_entry.entry_id]
    scan_interval = config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    scan_obd_interval = config_entry.options.get(
        CONF_SCAN_OBD_INTERVAL, DEFAULT_SCAN_OBD_INTERVAL
    )
    account.set_update_interval(scan_interval)
    account.set_update_obd_interval(scan_obd_interval)
