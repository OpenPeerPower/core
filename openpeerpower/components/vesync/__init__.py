"""VeSync integration."""
import asyncio
import logging

from pyvesync import VeSync
import voluptuous as vol

from openpeerpower.config_entries import SOURCE_IMPORT
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.dispatcher import async_dispatcher_send

from .common import async_process_devices
from .config_flow import configured_instances
from .const import (
    DOMAIN,
    SERVICE_UPDATE_DEVS,
    VS_DISCOVERY,
    VS_DISPATCHERS,
    VS_FANS,
    VS_LIGHTS,
    VS_MANAGER,
    VS_SWITCHES,
)

PLATFORMS = ["switch", "fan", "light"]

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Set up the VeSync component."""
    conf = config.get(DOMAIN)

    if conf is None:
        return True

    if not configured_instances(opp):
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data={
                    CONF_USERNAME: conf[CONF_USERNAME],
                    CONF_PASSWORD: conf[CONF_PASSWORD],
                },
            )
        )

    return True


async def async_setup_entry(opp, config_entry):
    """Set up Vesync as config entry."""
    username = config_entry.data[CONF_USERNAME]
    password = config_entry.data[CONF_PASSWORD]

    time_zone = str(opp.config.time_zone)

    manager = VeSync(username, password, time_zone)

    login = await opp.async_add_executor_job(manager.login)

    if not login:
        _LOGGER.error("Unable to login to the VeSync server")
        return False

    device_dict = await async_process_devices(opp, manager)

    forward_setup = opp.config_entries.async_forward_entry_setup

    opp.data[DOMAIN] = {}
    opp.data[DOMAIN][VS_MANAGER] = manager

    switches = opp.data[DOMAIN][VS_SWITCHES] = []
    fans = opp.data[DOMAIN][VS_FANS] = []
    lights = opp.data[DOMAIN][VS_LIGHTS] = []

    opp.data[DOMAIN][VS_DISPATCHERS] = []

    if device_dict[VS_SWITCHES]:
        switches.extend(device_dict[VS_SWITCHES])
        opp.async_create_task(forward_setup(config_entry, "switch"))

    if device_dict[VS_FANS]:
        fans.extend(device_dict[VS_FANS])
        opp.async_create_task(forward_setup(config_entry, "fan"))

    if device_dict[VS_LIGHTS]:
        lights.extend(device_dict[VS_LIGHTS])
        opp.async_create_task(forward_setup(config_entry, "light"))

    async def async_new_device_discovery(service):
        """Discover if new devices should be added."""
        manager = opp.data[DOMAIN][VS_MANAGER]
        switches = opp.data[DOMAIN][VS_SWITCHES]
        fans = opp.data[DOMAIN][VS_FANS]
        lights = opp.data[DOMAIN][VS_LIGHTS]

        dev_dict = await async_process_devices(opp, manager)
        switch_devs = dev_dict.get(VS_SWITCHES, [])
        fan_devs = dev_dict.get(VS_FANS, [])
        light_devs = dev_dict.get(VS_LIGHTS, [])

        switch_set = set(switch_devs)
        new_switches = list(switch_set.difference(switches))
        if new_switches and switches:
            switches.extend(new_switches)
            async_dispatcher_send(opp, VS_DISCOVERY.format(VS_SWITCHES), new_switches)
            return
        if new_switches and not switches:
            switches.extend(new_switches)
            opp.async_create_task(forward_setup(config_entry, "switch"))

        fan_set = set(fan_devs)
        new_fans = list(fan_set.difference(fans))
        if new_fans and fans:
            fans.extend(new_fans)
            async_dispatcher_send(opp, VS_DISCOVERY.format(VS_FANS), new_fans)
            return
        if new_fans and not fans:
            fans.extend(new_fans)
            opp.async_create_task(forward_setup(config_entry, "fan"))

        light_set = set(light_devs)
        new_lights = list(light_set.difference(lights))
        if new_lights and lights:
            lights.extend(new_lights)
            async_dispatcher_send(opp, VS_DISCOVERY.format(VS_LIGHTS), new_lights)
            return
        if new_lights and not lights:
            lights.extend(new_lights)
            opp.async_create_task(forward_setup(config_entry, "light"))

    opp.services.async_register(DOMAIN, SERVICE_UPDATE_DEVS, async_new_device_discovery)

    return True


async def async_unload_entry(opp, entry):
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
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
