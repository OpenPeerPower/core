"""Provides device automations for Tasmota."""

from hatasmota.const import AUTOMATION_TYPE_TRIGGER

from openpeerpower.helpers.device_registry import EVENT_DEVICE_REGISTRY_UPDATED
from openpeerpower.helpers.dispatcher import async_dispatcher_connect

from . import device_trigger
from .const import DATA_REMOVE_DISCOVER_COMPONENT, DATA_UNSUB
from .discovery import TASMOTA_DISCOVERY_ENTITY_NEW


async def async_remove_automations(opp, device_id):
    """Remove automations for a Tasmota device."""
    await device_trigger.async_remove_triggers(opp, device_id)


async def async_setup_entry(opp, config_entry):
    """Set up Tasmota device automation dynamically through discovery."""

    async def async_device_removed(event):
        """Handle the removal of a device."""
        if event.data["action"] != "remove":
            return
        await async_remove_automations(opp, event.data["device_id"])

    async def async_discover(tasmota_automation, discovery_hash):
        """Discover and add a Tasmota device automation."""
        if tasmota_automation.automation_type == AUTOMATION_TYPE_TRIGGER:
            await device_trigger.async_setup_trigger(
                opp, tasmota_automation, config_entry, discovery_hash
            )

    opp.data[
        DATA_REMOVE_DISCOVER_COMPONENT.format("device_automation")
    ] = async_dispatcher_connect(
        opp,
        TASMOTA_DISCOVERY_ENTITY_NEW.format("device_automation"),
        async_discover,
    )
    opp.data[DATA_UNSUB].append(
        opp.bus.async_listen(EVENT_DEVICE_REGISTRY_UPDATED, async_device_removed)
    )
