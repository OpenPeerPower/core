"""MySensors notification service."""
from openpeerpower.components import mysensors
from openpeerpower.components.notify import ATTR_TARGET, DOMAIN, BaseNotificationService


async def async_get_service(opp, config, discovery_info=None):
    """Get the MySensors notification service."""
    if not discovery_info:
        return None

    new_devices = mysensors.setup_mysensors_platform(
        opp, DOMAIN, discovery_info, MySensorsNotificationDevice
    )
    if not new_devices:
        return None
    return MySensorsNotificationService(opp)


class MySensorsNotificationDevice(mysensors.device.MySensorsDevice):
    """Represent a MySensors Notification device."""

    def send_msg(self, msg):
        """Send a message."""
        for sub_msg in [msg[i : i + 25] for i in range(0, len(msg), 25)]:
            # Max mysensors payload is 25 bytes.
            self.gateway.set_child_value(
                self.node_id, self.child_id, self.value_type, sub_msg
            )

    def __repr__(self):
        """Return the representation."""
        return f"<MySensorsNotificationDevice {self.name}>"


class MySensorsNotificationService(BaseNotificationService):
    """Implement a MySensors notification service."""

    def __init__(self, opp):
        """Initialize the service."""
        self.devices = mysensors.get_mysensors_devices(opp, DOMAIN)

    async def async_send_message(self, message="", **kwargs):
        """Send a message to a user."""
        target_devices = kwargs.get(ATTR_TARGET)
        devices = [
            device
            for device in self.devices.values()
            if target_devices is None or device.name in target_devices
        ]

        for device in devices:
            device.send_msg(message)
