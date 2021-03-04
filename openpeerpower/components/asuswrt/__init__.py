"""Support for ASUSWRT devices."""
import asyncio

import voluptuous as vol

from openpeerpower.config_entries import SOURCE_IMPORT, ConfigEntry
from openpeerpower.const import (
    CONF_HOST,
    CONF_MODE,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_PROTOCOL,
    CONF_SENSORS,
    CONF_USERNAME,
    EVENT_OPENPEERPOWER_STOP,
)
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.typing import OpenPeerPowerType

from .const import (
    CONF_DNSMASQ,
    CONF_INTERFACE,
    CONF_REQUIRE_IP,
    CONF_SSH_KEY,
    DATA_ASUSWRT,
    DEFAULT_DNSMASQ,
    DEFAULT_INTERFACE,
    DEFAULT_SSH_PORT,
    DOMAIN,
    MODE_AP,
    MODE_ROUTER,
    PROTOCOL_SSH,
    PROTOCOL_TELNET,
    SENSOR_TYPES,
)
from .router import AsusWrtRouter

PLATFORMS = ["device_tracker", "sensor"]

CONF_PUB_KEY = "pub_key"
SECRET_GROUP = "Password or SSH Key"

CONFIG_SCHEMA = vol.Schema(
    vol.All(
        cv.deprecated(DOMAIN),
        {
            DOMAIN: vol.Schema(
                {
                    vol.Required(CONF_HOST): cv.string,
                    vol.Required(CONF_USERNAME): cv.string,
                    vol.Optional(CONF_PROTOCOL, default=PROTOCOL_SSH): vol.In(
                        [PROTOCOL_SSH, PROTOCOL_TELNET]
                    ),
                    vol.Optional(CONF_MODE, default=MODE_ROUTER): vol.In(
                        [MODE_ROUTER, MODE_AP]
                    ),
                    vol.Optional(CONF_PORT, default=DEFAULT_SSH_PORT): cv.port,
                    vol.Optional(CONF_REQUIRE_IP, default=True): cv.boolean,
                    vol.Exclusive(CONF_PASSWORD, SECRET_GROUP): cv.string,
                    vol.Exclusive(CONF_SSH_KEY, SECRET_GROUP): cv.isfile,
                    vol.Exclusive(CONF_PUB_KEY, SECRET_GROUP): cv.isfile,
                    vol.Optional(CONF_SENSORS): vol.All(
                        cv.ensure_list, [vol.In(SENSOR_TYPES)]
                    ),
                    vol.Optional(CONF_INTERFACE, default=DEFAULT_INTERFACE): cv.string,
                    vol.Optional(CONF_DNSMASQ, default=DEFAULT_DNSMASQ): cv.string,
                }
            )
        },
    ),
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Set up the AsusWrt integration."""
    conf = config.get(DOMAIN)
    if conf is None:
        return True

    # save the options from config yaml
    options = {}
    mode = conf.get(CONF_MODE, MODE_ROUTER)
    for name, value in conf.items():
        if name in ([CONF_DNSMASQ, CONF_INTERFACE, CONF_REQUIRE_IP]):
            if name == CONF_REQUIRE_IP and mode != MODE_AP:
                continue
            options[name] = value
    opp.data[DOMAIN] = {"yaml_options": options}

    # check if already configured
    domains_list = opp.config_entries.async_domains()
    if DOMAIN in domains_list:
        return True

    # remove not required config keys
    pub_key = conf.pop(CONF_PUB_KEY, "")
    if pub_key:
        conf[CONF_SSH_KEY] = pub_key

    conf.pop(CONF_REQUIRE_IP, True)
    conf.pop(CONF_SENSORS, {})
    conf.pop(CONF_INTERFACE, "")
    conf.pop(CONF_DNSMASQ, "")

    opp.async_create_task(
        opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data=conf
        )
    )

    return True


async def async_setup_entry(opp: OpenPeerPowerType, entry: ConfigEntry):
    """Set up AsusWrt platform."""

    # import options from yaml if empty
    yaml_options = opp.data.get(DOMAIN, {}).pop("yaml_options", {})
    if not entry.options and yaml_options:
        opp.config_entries.async_update_entry(entry, options=yaml_options)

    router = AsusWrtRouter(opp, entry)
    await router.setup()

    router.async_on_close(entry.add_update_listener(update_listener))

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    async def async_close_connection(event):
        """Close AsusWrt connection on OP Stop."""
        await router.close()

    stop_listener = opp.bus.async_listen_once(
        EVENT_OPENPEERPOWER_STOP, async_close_connection
    )

    opp.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_ASUSWRT: router,
        "stop_listener": stop_listener,
    }

    return True


async def async_unload_entry(opp: OpenPeerPowerType, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        opp.data[DOMAIN][entry.entry_id]["stop_listener"]()
        router = opp.data[DOMAIN][entry.entry_id][DATA_ASUSWRT]
        await router.close()

        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(opp: OpenPeerPowerType, entry: ConfigEntry):
    """Update when config_entry options update."""
    router = opp.data[DOMAIN][entry.entry_id][DATA_ASUSWRT]

    if router.update_options(entry.options):
        await opp.config_entries.async_reload(entry.entry_id)
