"""Provide functionality to keep track of devices."""
from openpeerpower.const import ATTR_GPS_ACCURACY, STATE_HOME  # noqa: F401
from openpeerpower.helpers.typing import ConfigType, OpenPeerPowerType
from openpeerpower.loader import bind_opp

from .config_entry import async_setup_entry, async_unload_entry  # noqa: F401
from .const import (  # noqa: F401
    ATTR_ATTRIBUTES,
    ATTR_BATTERY,
    ATTR_DEV_ID,
    ATTR_GPS,
    ATTR_HOST_NAME,
    ATTR_LOCATION_NAME,
    ATTR_MAC,
    ATTR_SOURCE_TYPE,
    CONF_CONSIDER_HOME,
    CONF_NEW_DEVICE_DEFAULTS,
    CONF_SCAN_INTERVAL,
    CONF_TRACK_NEW,
    DOMAIN,
    SOURCE_TYPE_BLUETOOTH,
    SOURCE_TYPE_BLUETOOTH_LE,
    SOURCE_TYPE_GPS,
    SOURCE_TYPE_ROUTER,
)
from .legacy import (  # noqa: F401
    PLATFORM_SCHEMA,
    PLATFORM_SCHEMA_BASE,
    SERVICE_SEE,
    SERVICE_SEE_PAYLOAD_SCHEMA,
    SOURCE_TYPES,
    DeviceScanner,
    async_setup_integration as async_setup_legacy_integration,
    see,
)


@bind_opp
def is_on(opp: OpenPeerPowerType, entity_id: str):
    """Return the state if any or a specified device is home."""
    return opp.states.is_state(entity_id, STATE_HOME)


async def async_setup(opp: OpenPeerPowerType, config: ConfigType):
    """Set up the device tracker."""
    await async_setup_legacy_integration(opp, config)

    return True
