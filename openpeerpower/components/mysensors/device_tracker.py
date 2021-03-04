"""Support for tracking MySensors devices."""
from openpeerpower.components import mysensors
from openpeerpower.components.device_tracker import DOMAIN
from openpeerpower.components.mysensors import DevId, on_unload
from openpeerpower.components.mysensors.const import ATTR_GATEWAY_ID, GatewayId
from openpeerpower.helpers.dispatcher import async_dispatcher_connect
from openpeerpower.helpers.typing import OpenPeerPowerType
from openpeerpower.util import slugify


async def async_setup_scanner(
    opp: OpenPeerPowerType, config, async_see, discovery_info=None
):
    """Set up the MySensors device scanner."""
    new_devices = mysensors.setup_mysensors_platform(
        opp,
        DOMAIN,
        discovery_info,
        MySensorsDeviceScanner,
        device_args=(opp, async_see),
    )
    if not new_devices:
        return False

    for device in new_devices:
        gateway_id: GatewayId = discovery_info[ATTR_GATEWAY_ID]
        dev_id: DevId = (gateway_id, device.node_id, device.child_id, device.value_type)
        await on_unload(
            opp,
            gateway_id,
            async_dispatcher_connect(
                opp,
                mysensors.const.CHILD_CALLBACK.format(*dev_id),
                device.async_update_callback,
            ),
        )
        await on_unload(
            opp,
            gateway_id,
            async_dispatcher_connect(
                opp,
                mysensors.const.NODE_CALLBACK.format(gateway_id, device.node_id),
                device.async_update_callback,
            ),
        )

    return True


class MySensorsDeviceScanner(mysensors.device.MySensorsDevice):
    """Represent a MySensors scanner."""

    def __init__(self, opp: OpenPeerPowerType, async_see, *args):
        """Set up instance."""
        super().__init__(*args)
        self.async_see = async_see
        self.opp = opp

    async def _async_update_callback(self):
        """Update the device."""
        await self.async_update()
        node = self.gateway.sensors[self.node_id]
        child = node.children[self.child_id]
        position = child.values[self.value_type]
        latitude, longitude, _ = position.split(",")

        await self.async_see(
            dev_id=slugify(self.name),
            host_name=self.name,
            gps=(latitude, longitude),
            battery=node.battery_level,
            attributes=self.device_state_attributes,
        )
