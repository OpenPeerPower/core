"""Open Peer Power Switcher Component."""
from asyncio import QueueEmpty, TimeoutError as Asyncio_TimeoutError, wait_for
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional

from aioswitcher.bridge import SwitcherV2Bridge
import voluptuous as vol

from openpeerpower.components.switch import DOMAIN as SWITCH_DOMAIN
from openpeerpower.const import CONF_DEVICE_ID, EVENT_OPENPEERPOWER_STOP
from openpeerpower.core import callback
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.discovery import async_load_platform
from openpeerpower.helpers.dispatcher import async_dispatcher_send
from openpeerpower.helpers.event import async_track_time_interval
from openpeerpower.helpers.typing import EventType, OpenPeerPowerType

_LOGGER = logging.getLogger(__name__)

DOMAIN = "switcher_kis"

CONF_DEVICE_PASSWORD = "device_password"
CONF_PHONE_ID = "phone_id"

DATA_DEVICE = "device"

SIGNAL_SWITCHER_DEVICE_UPDATE = "switcher_device_update"

ATTR_AUTO_OFF_SET = "auto_off_set"
ATTR_ELECTRIC_CURRENT = "electric_current"
ATTR_REMAINING_TIME = "remaining_time"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_PHONE_ID): cv.string,
                vol.Required(CONF_DEVICE_ID): cv.string,
                vol.Required(CONF_DEVICE_PASSWORD): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp: OpenPeerPowerType, config: Dict) -> bool:
    """Set up the switcher component."""
    phone_id = config[DOMAIN][CONF_PHONE_ID]
    device_id = config[DOMAIN][CONF_DEVICE_ID]
    device_password = config[DOMAIN][CONF_DEVICE_PASSWORD]

    v2bridge = SwitcherV2Bridge(opp.loop, phone_id, device_id, device_password)

    await v2bridge.start()

    async def async_stop_bridge(event: EventType) -> None:
        """On Open Peer Power stop, gracefully stop the bridge if running."""
        await v2bridge.stop()

    opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, async_stop_bridge)

    try:
        device_data = await wait_for(v2bridge.queue.get(), timeout=10.0)
    except (Asyncio_TimeoutError, RuntimeError):
        _LOGGER.exception("Failed to get response from device")
        await v2bridge.stop()
        return False
    opp.data[DOMAIN] = {DATA_DEVICE: device_data}

    opp.async_create_task(async_load_platform(opp, SWITCH_DOMAIN, DOMAIN, {}, config))

    @callback
    def device_updates(timestamp: Optional[datetime]) -> None:
        """Use for updating the device data from the queue."""
        if v2bridge.running:
            try:
                device_new_data = v2bridge.queue.get_nowait()
                if device_new_data:
                    async_dispatcher_send(
                        opp, SIGNAL_SWITCHER_DEVICE_UPDATE, device_new_data
                    )
            except QueueEmpty:
                pass

    async_track_time_interval(opp, device_updates, timedelta(seconds=4))

    return True
