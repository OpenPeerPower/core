"""The devolo_home_control integration."""
import asyncio
from functools import partial

from devolo_home_control_api.exceptions.gateway import GatewayOfflineError
from devolo_home_control_api.homecontrol import HomeControl
from devolo_home_control_api.mydevolo import Mydevolo

from openpeerpower.components import zeroconf
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME, EVENT_OPENPEERPOWER_STOP
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.typing import OpenPeerPowerType

from .const import CONF_MYDEVOLO, DOMAIN, GATEWAY_SERIAL_PATTERN, PLATFORMS


async def async_setup(opp, config):
    """Get all devices and add them to opp."""
    return True


async def async_setup_entry(opp: OpenPeerPowerType, entry: ConfigEntry) -> bool:
    """Set up the devolo account from a config entry."""
    opp.data.setdefault(DOMAIN, {})

    mydevolo = _mydevolo(entry.data)

    credentials_valid = await opp.async_add_executor_job(mydevolo.credentials_valid)

    if not credentials_valid:
        return False

    if await opp.async_add_executor_job(mydevolo.maintenance):
        raise ConfigEntryNotReady

    gateway_ids = await opp.async_add_executor_job(mydevolo.get_gateway_ids)

    if GATEWAY_SERIAL_PATTERN.match(entry.unique_id):
        uuid = await opp.async_add_executor_job(mydevolo.uuid)
        opp.config_entries.async_update_entry(entry, unique_id=uuid)

    try:
        zeroconf_instance = await zeroconf.async_get_instance(opp)
        opp.data[DOMAIN][entry.entry_id] = {"gateways": [], "listener": None}
        for gateway_id in gateway_ids:
            opp.data[DOMAIN][entry.entry_id]["gateways"].append(
                await opp.async_add_executor_job(
                    partial(
                        HomeControl,
                        gateway_id=gateway_id,
                        mydevolo_instance=mydevolo,
                        zeroconf_instance=zeroconf_instance,
                    )
                )
            )
    except (ConnectionError, GatewayOfflineError) as err:
        raise ConfigEntryNotReady from err

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    def shutdown(event):
        for gateway in opp.data[DOMAIN][entry.entry_id]["gateways"]:
            gateway.websocket_disconnect(
                f"websocket disconnect requested by {EVENT_OPENPEERPOWER_STOP}"
            )

    # Listen when EVENT_OPENPEERPOWER_STOP is fired
    opp.data[DOMAIN][entry.entry_id]["listener"] = opp.bus.async_listen_once(
        EVENT_OPENPEERPOWER_STOP, shutdown
    )

    return True


async def async_unload_entry(opp: OpenPeerPowerType, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    await asyncio.gather(
        *[
            opp.async_add_executor_job(gateway.websocket_disconnect)
            for gateway in opp.data[DOMAIN][entry.entry_id]["gateways"]
        ]
    )
    opp.data[DOMAIN][entry.entry_id]["listener"]()
    opp.data[DOMAIN].pop(entry.entry_id)
    return unload


def _mydevolo(conf: dict) -> Mydevolo:
    """Configure mydevolo."""
    mydevolo = Mydevolo()
    mydevolo.user = conf[CONF_USERNAME]
    mydevolo.password = conf[CONF_PASSWORD]
    mydevolo.url = conf[CONF_MYDEVOLO]
    return mydevolo
