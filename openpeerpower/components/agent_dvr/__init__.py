"""Support for Agent."""
import asyncio

from agent import AgentError
from agent.a import Agent

from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import device_registry as dr
from openpeerpower.helpers.aiohttp_client import async_get_clientsession

from .const import CONNECTION, DOMAIN as AGENT_DOMAIN, SERVER_URL

ATTRIBUTION = "ispyconnect.com"
DEFAULT_BRAND = "Agent DVR by ispyconnect.com"

FORWARDS = ["alarm_control_panel", "camera"]


async def async_setup(opp, config):
    """Old way to set up integrations."""
    return True


async def async_setup_entry(opp, config_entry):
    """Set up the Agent component."""
    opp.data.setdefault(AGENT_DOMAIN, {})

    server_origin = config_entry.data[SERVER_URL]

    agent_client = Agent(server_origin, async_get_clientsession(opp))
    try:
        await agent_client.update()
    except AgentError as err:
        await agent_client.close()
        raise ConfigEntryNotReady from err

    if not agent_client.is_available:
        raise ConfigEntryNotReady

    await agent_client.get_devices()

    opp.data[AGENT_DOMAIN][config_entry.entry_id] = {CONNECTION: agent_client}

    device_registry = await dr.async_get_registry(opp)

    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(AGENT_DOMAIN, agent_client.unique)},
        manufacturer="iSpyConnect",
        name=f"Agent {agent_client.name}",
        model="Agent DVR",
        sw_version=agent_client.version,
    )

    for forward in FORWARDS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(config_entry, forward)
        )

    return True


async def async_unload_entry(opp, config_entry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(config_entry, forward)
                for forward in FORWARDS
            ]
        )
    )

    await opp.data[AGENT_DOMAIN][config_entry.entry_id][CONNECTION].close()

    if unload_ok:
        opp.data[AGENT_DOMAIN].pop(config_entry.entry_id)

    return unload_ok
