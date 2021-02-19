"""Test Opentherm Gateway init."""
from unittest.mock import patch

from pyotgw.vars import OTGW, OTGW_ABOUT

from openpeerpower import setup
from openpeerpower.components.opentherm_gw.const import DOMAIN
from openpeerpower.const import CONF_DEVICE, CONF_ID, CONF_NAME

from tests.common import MockConfigEntry, mock_device_registry

VERSION_OLD = "4.2.5"
VERSION_NEW = "4.2.8.1"
MINIMAL_STATUS = {OTGW: {OTGW_ABOUT: f"OpenTherm Gateway {VERSION_OLD}"}}
MINIMAL_STATUS_UPD = {OTGW: {OTGW_ABOUT: f"OpenTherm Gateway {VERSION_NEW}"}}
MOCK_GATEWAY_ID = "mock_gateway"
MOCK_CONFIG_ENTRY = MockConfigEntry(
    domain=DOMAIN,
    title="Mock Gateway",
    data={
        CONF_NAME: "Mock Gateway",
        CONF_DEVICE: "/dev/null",
        CONF_ID: MOCK_GATEWAY_ID,
    },
    options={},
)


async def test_device_registry_insert.opp):
    """Test that the device registry is initialized correctly."""
    MOCK_CONFIG_ENTRY.add_to_opp.opp)

    with patch(
        "openpeerpower.components.opentherm_gw.OpenThermGatewayDevice.cleanup",
        return_value=None,
    ), patch("pyotgw.pyotgw.connect", return_value=MINIMAL_STATUS):
        await setup.async_setup_component.opp, DOMAIN, {})

    await.opp.async_block_till_done()

    device_registry = await.opp.helpers.device_registry.async_get_registry()

    gw_dev = device_registry.async_get_device(identifiers={(DOMAIN, MOCK_GATEWAY_ID)})
    assert gw_dev.sw_version == VERSION_OLD


async def test_device_registry_update.opp):
    """Test that the device registry is updated correctly."""
    MOCK_CONFIG_ENTRY.add_to_opp.opp)

    dev_reg = mock_device_registry.opp)
    dev_reg.async_get_or_create(
        config_entry_id=MOCK_CONFIG_ENTRY.entry_id,
        identifiers={(DOMAIN, MOCK_GATEWAY_ID)},
        name="Mock Gateway",
        manufacturer="Schelte Bron",
        model="OpenTherm Gateway",
        sw_version=VERSION_OLD,
    )

    with patch(
        "openpeerpower.components.opentherm_gw.OpenThermGatewayDevice.cleanup",
        return_value=None,
    ), patch("pyotgw.pyotgw.connect", return_value=MINIMAL_STATUS_UPD):
        await setup.async_setup_component.opp, DOMAIN, {})

    await.opp.async_block_till_done()
    gw_dev = dev_reg.async_get_device(identifiers={(DOMAIN, MOCK_GATEWAY_ID)})
    assert gw_dev.sw_version == VERSION_NEW
