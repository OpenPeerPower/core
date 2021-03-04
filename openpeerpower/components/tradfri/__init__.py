"""Support for IKEA Tradfri."""
import asyncio
from datetime import timedelta
import logging

from pytradfri import Gateway, RequestError
from pytradfri.api.aiocoap_api import APIFactory
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import EVENT_OPENPEERPOWER_STOP
from openpeerpower.exceptions import ConfigEntryNotReady
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.event import async_track_time_interval
from openpeerpower.helpers.typing import ConfigType, OpenPeerPowerType
from openpeerpower.util.json import load_json

from .const import (
    ATTR_TRADFRI_GATEWAY,
    ATTR_TRADFRI_GATEWAY_MODEL,
    ATTR_TRADFRI_MANUFACTURER,
    CONF_ALLOW_TRADFRI_GROUPS,
    CONF_GATEWAY_ID,
    CONF_HOST,
    CONF_IDENTITY,
    CONF_IMPORT_GROUPS,
    CONF_KEY,
    CONFIG_FILE,
    DEFAULT_ALLOW_TRADFRI_GROUPS,
    DEVICES,
    DOMAIN,
    GROUPS,
    KEY_API,
    PLATFORMS,
)

_LOGGER = logging.getLogger(__name__)

FACTORY = "tradfri_factory"
LISTENERS = "tradfri_listeners"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_HOST): cv.string,
                vol.Optional(
                    CONF_ALLOW_TRADFRI_GROUPS, default=DEFAULT_ALLOW_TRADFRI_GROUPS
                ): cv.boolean,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp: OpenPeerPowerType, config: ConfigType):
    """Set up the Tradfri component."""
    conf = config.get(DOMAIN)

    if conf is None:
        return True

    configured_hosts = [
        entry.data.get("host") for entry in opp.config_entries.async_entries(DOMAIN)
    ]

    legacy_hosts = await opp.async_add_executor_job(
        load_json, opp.config.path(CONFIG_FILE)
    )

    for host, info in legacy_hosts.items():
        if host in configured_hosts:
            continue

        info[CONF_HOST] = host
        info[CONF_IMPORT_GROUPS] = conf[CONF_ALLOW_TRADFRI_GROUPS]

        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data=info
            )
        )

    host = conf.get(CONF_HOST)
    import_groups = conf[CONF_ALLOW_TRADFRI_GROUPS]

    if host is None or host in configured_hosts or host in legacy_hosts:
        return True

    opp.async_create_task(
        opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={CONF_HOST: host, CONF_IMPORT_GROUPS: import_groups},
        )
    )

    return True


async def async_setup_entry(opp: OpenPeerPowerType, entry: ConfigEntry):
    """Create a gateway."""
    # host, identity, key, allow_tradfri_groups
    tradfri_data = opp.data.setdefault(DOMAIN, {})[entry.entry_id] = {}
    listeners = tradfri_data[LISTENERS] = []

    factory = await APIFactory.init(
        entry.data[CONF_HOST],
        psk_id=entry.data[CONF_IDENTITY],
        psk=entry.data[CONF_KEY],
    )

    async def on_opp_stop(event):
        """Close connection when opp stops."""
        await factory.shutdown()

    listeners.append(opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, on_opp_stop))

    api = factory.request
    gateway = Gateway()

    try:
        gateway_info = await api(gateway.get_gateway_info())
        devices_commands = await api(gateway.get_devices())
        devices = await api(devices_commands)
        groups_commands = await api(gateway.get_groups())
        groups = await api(groups_commands)
    except RequestError as err:
        await factory.shutdown()
        raise ConfigEntryNotReady from err

    tradfri_data[KEY_API] = api
    tradfri_data[FACTORY] = factory
    tradfri_data[DEVICES] = devices
    tradfri_data[GROUPS] = groups

    dev_reg = await opp.helpers.device_registry.async_get_registry()
    dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=set(),
        identifiers={(DOMAIN, entry.data[CONF_GATEWAY_ID])},
        manufacturer=ATTR_TRADFRI_MANUFACTURER,
        name=ATTR_TRADFRI_GATEWAY,
        # They just have 1 gateway model. Type is not exposed yet.
        model=ATTR_TRADFRI_GATEWAY_MODEL,
        sw_version=gateway_info.firmware_version,
    )

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    async def async_keep_alive(now):
        if opp.is_stopping:
            return

        try:
            await api(gateway.get_gateway_info())
        except RequestError:
            _LOGGER.error("Keep-alive failed")

    listeners.append(
        async_track_time_interval(opp, async_keep_alive, timedelta(seconds=60))
    )

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
        tradfri_data = opp.data[DOMAIN].pop(entry.entry_id)
        factory = tradfri_data[FACTORY]
        await factory.shutdown()
        # unsubscribe listeners
        for listener in tradfri_data[LISTENERS]:
            listener()

    return unload_ok
