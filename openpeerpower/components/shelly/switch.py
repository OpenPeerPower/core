"""Switch for Shelly."""
from aioshelly import Block

from openpeerpower.components.switch import SwitchEntity
from openpeerpower.core import callback

from . import ShellyDeviceWrapper
from .const import COAP, DATA_CONFIG_ENTRY, DOMAIN
from .entity import ShellyBlockEntity
from .utils import async_remove_shelly_entity


async def async_setup_entry(opp, config_entry, async_add_entities):
    """Set up switches for device."""
    wrapper = opp.data[DOMAIN][DATA_CONFIG_ENTRY][config_entry.entry_id][COAP]

    # In roller mode the relay blocks exist but do not contain required info
    if (
        wrapper.model in ["SHSW-21", "SHSW-25"]
        and wrapper.device.settings["mode"] != "relay"
    ):
        return

    relay_blocks = []
    for block in wrapper.device.blocks:
        if block.type == "relay":
            appliance_type = wrapper.device.settings["relays"][int(block.channel)].get(
                "appliance_type"
            )
            if not appliance_type or appliance_type.lower() != "light":
                relay_blocks.append(block)
                unique_id = (
                    f'{wrapper.device.shelly["mac"]}-{block.type}_{block.channel}'
                )
                await async_remove_shelly_entity(
                    opp,
                    "light",
                    unique_id,
                )

    if not relay_blocks:
        return

    async_add_entities(RelaySwitch(wrapper, block) for block in relay_blocks)


class RelaySwitch(ShellyBlockEntity, SwitchEntity):
    """Switch that controls a relay block on Shelly devices."""

    def __init__(self, wrapper: ShellyDeviceWrapper, block: Block) -> None:
        """Initialize relay switch."""
        super().__init__(wrapper, block)
        self.control_result = None

    @property
    def is_on(self) -> bool:
        """If switch is on."""
        if self.control_result:
            return self.control_result["ison"]

        return self.block.output

    async def async_turn_on(self, **kwargs):
        """Turn on relay."""
        self.control_result = await self.block.set_state(turn="on")
        self.async_write_op_state()

    async def async_turn_off(self, **kwargs):
        """Turn off relay."""
        self.control_result = await self.block.set_state(turn="off")
        self.async_write_op_state()

    @callback
    def _update_callback(self):
        """When device updates, clear control result that overrides state."""
        self.control_result = None
        super()._update_callback()
