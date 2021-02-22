"""Tests for the WiLight component."""

from pywilight.const import DOMAIN

from openpeerpower.components.ssdp import (
    ATTR_SSDP_LOCATION,
    ATTR_UPNP_MANUFACTURER,
    ATTR_UPNP_MODEL_NAME,
    ATTR_UPNP_MODEL_NUMBER,
    ATTR_UPNP_SERIAL,
)
from openpeerpower.components.wilight.config_flow import (
    CONF_MODEL_NAME,
    CONF_SERIAL_NUMBER,
)
from openpeerpower.const import CONF_HOST
from openpeerpower.helpers.typing import OpenPeerPowerType

from tests.common import MockConfigEntry

HOST = "127.0.0.1"
WILIGHT_ID = "000000000099"
SSDP_LOCATION = "http://127.0.0.1/"
UPNP_MANUFACTURER = "All Automacao Ltda"
UPNP_MODEL_NAME_P_B = "WiLight 0102001800010009-10010010"
UPNP_MODEL_NAME_DIMMER = "WiLight 0100001700020009-10010010"
UPNP_MODEL_NAME_COLOR = "WiLight 0107001800020009-11010"
UPNP_MODEL_NAME_LIGHT_FAN = "WiLight 0104001800010009-10"
UPNP_MODEL_NAME_COVER = "WiLight 0103001800010009-10"
UPNP_MODEL_NUMBER = "123456789012345678901234567890123456"
UPNP_SERIAL = "000000000099"
UPNP_MAC_ADDRESS = "5C:CF:7F:8B:CA:56"
UPNP_MANUFACTURER_NOT_WILIGHT = "Test"
CONF_COMPONENTS = "components"

MOCK_SSDP_DISCOVERY_INFO_P_B = {
    ATTR_SSDP_LOCATION: SSDP_LOCATION,
    ATTR_UPNP_MANUFACTURER: UPNP_MANUFACTURER,
    ATTR_UPNP_MODEL_NAME: UPNP_MODEL_NAME_P_B,
    ATTR_UPNP_MODEL_NUMBER: UPNP_MODEL_NUMBER,
    ATTR_UPNP_SERIAL: UPNP_SERIAL,
}

MOCK_SSDP_DISCOVERY_INFO_WRONG_MANUFACTORER = {
    ATTR_SSDP_LOCATION: SSDP_LOCATION,
    ATTR_UPNP_MANUFACTURER: UPNP_MANUFACTURER_NOT_WILIGHT,
    ATTR_UPNP_MODEL_NAME: UPNP_MODEL_NAME_P_B,
    ATTR_UPNP_MODEL_NUMBER: UPNP_MODEL_NUMBER,
    ATTR_UPNP_SERIAL: ATTR_UPNP_SERIAL,
}

MOCK_SSDP_DISCOVERY_INFO_MISSING_MANUFACTORER = {
    ATTR_SSDP_LOCATION: SSDP_LOCATION,
    ATTR_UPNP_MODEL_NAME: UPNP_MODEL_NAME_P_B,
    ATTR_UPNP_MODEL_NUMBER: UPNP_MODEL_NUMBER,
    ATTR_UPNP_SERIAL: ATTR_UPNP_SERIAL,
}


async def setup_integration(
   .opp: OpenPeerPowerType,
) -> MockConfigEntry:
    """Mock ConfigEntry in Open Peer Power."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=WILIGHT_ID,
        data={
            CONF_HOST: HOST,
            CONF_SERIAL_NUMBER: UPNP_SERIAL,
            CONF_MODEL_NAME: UPNP_MODEL_NAME_P_B,
        },
    )

    entry.add_to.opp.opp)

    await.opp.config_entries.async_setup(entry.entry_id)
    await.opp.async_block_till_done()

    return entry
