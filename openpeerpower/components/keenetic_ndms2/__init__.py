"""The keenetic_ndms2 component."""

from openpeerpower.components import binary_sensor, device_tracker
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_HOST, CONF_SCAN_INTERVAL
from openpeerpower.core import Config, OpenPeerPower

from .const import (
    CONF_CONSIDER_HOME,
    CONF_INCLUDE_ARP,
    CONF_INCLUDE_ASSOCIATED,
    CONF_INTERFACES,
    CONF_TRY_HOTSPOT,
    DEFAULT_CONSIDER_HOME,
    DEFAULT_INTERFACE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ROUTER,
    UNDO_UPDATE_LISTENER,
)
from .router import KeeneticRouter

PLATFORMS = [device_tracker.DOMAIN, binary_sensor.DOMAIN]


async def async_setup(opp: OpenPeerPower, _config: Config) -> bool:
    """Set up configured entries."""
    opp.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(opp: OpenPeerPower, config_entry: ConfigEntry) -> bool:
    """Set up the component."""

    async_add_defaults(opp, config_entry)

    router = KeeneticRouter(opp, config_entry)
    await router.async_setup()

    undo_listener = config_entry.add_update_listener(update_listener)

    opp.data[DOMAIN][config_entry.entry_id] = {
        ROUTER: router,
        UNDO_UPDATE_LISTENER: undo_listener,
    }

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    return True


async def async_unload_entry(opp: OpenPeerPower, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    opp.data[DOMAIN][config_entry.entry_id][UNDO_UPDATE_LISTENER]()

    for platform in PLATFORMS:
        await opp.config_entries.async_forward_entry_unload(config_entry, platform)

    router: KeeneticRouter = opp.data[DOMAIN][config_entry.entry_id][ROUTER]

    await router.async_teardown()

    opp.data[DOMAIN].pop(config_entry.entry_id)

    return True


async def update_listener(opp, config_entry):
    """Handle options update."""
    await opp.config_entries.async_reload(config_entry.entry_id)


def async_add_defaults(opp: OpenPeerPower, config_entry: ConfigEntry):
    """Populate default options."""
    host: str = config_entry.data[CONF_HOST]
    imported_options: dict = opp.data[DOMAIN].get(f"imported_options_{host}", {})
    options = {
        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
        CONF_CONSIDER_HOME: DEFAULT_CONSIDER_HOME,
        CONF_INTERFACES: [DEFAULT_INTERFACE],
        CONF_TRY_HOTSPOT: True,
        CONF_INCLUDE_ARP: True,
        CONF_INCLUDE_ASSOCIATED: True,
        **imported_options,
        **config_entry.options,
    }

    if options.keys() - config_entry.options.keys():
        opp.config_entries.async_update_entry(config_entry, options=options)
