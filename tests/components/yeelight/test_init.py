"""Test Yeelight."""
from unittest.mock import MagicMock, patch

from yeelight import BulbType

from openpeerpower.components.yeelight import (
    CONF_NIGHTLIGHT_SWITCH,
    CONF_NIGHTLIGHT_SWITCH_TYPE,
    DATA_CONFIG_ENTRIES,
    DATA_DEVICE,
    DOMAIN,
    NIGHTLIGHT_SWITCH_TYPE_LIGHT,
)
from openpeerpower.const import CONF_DEVICES, CONF_HOST, CONF_NAME, STATE_UNAVAILABLE
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers import entity_registry
from openpeerpower.setup import async_setup_component

from . import (
    CAPABILITIES,
    CONFIG_ENTRY_DATA,
    ENTITY_AMBILIGHT,
    ENTITY_BINARY_SENSOR,
    ENTITY_BINARY_SENSOR_TEMPLATE,
    ENTITY_LIGHT,
    ENTITY_NIGHTLIGHT,
    ID,
    IP_ADDRESS,
    MODULE,
    MODULE_CONFIG_FLOW,
    _mocked_bulb,
    _patch_discovery,
)

from tests.common import MockConfigEntry


async def test_setup_discovery(opp: OpenPeerPower):
    """Test setting up Yeelight by discovery."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=CONFIG_ENTRY_DATA)
    config_entry.add_to(opp.opp)

    mocked_bulb = _mocked_bulb()
    with _patch_discovery(MODULE), patch(f"{MODULE}.Bulb", return_value=mocked_bulb):
        assert await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()

    assert opp.states.get(ENTITY_BINARY_SENSOR) is not None
    assert opp.states.get(ENTITY_LIGHT) is not None

    # Unload
    assert await opp.config_entries.async_unload(config_entry.entry_id)
    assert opp.states.get(ENTITY_BINARY_SENSOR).state == STATE_UNAVAILABLE
    assert opp.states.get(ENTITY_LIGHT).state == STATE_UNAVAILABLE

    # Remove
    assert await opp.config_entries.async_remove(config_entry.entry_id)
    await opp.async_block_till_done()
    assert opp.states.get(ENTITY_BINARY_SENSOR) is None
    assert opp.states.get(ENTITY_LIGHT) is None


async def test_setup_import(opp: OpenPeerPower):
    """Test import from yaml."""
    mocked_bulb = _mocked_bulb()
    name = "yeelight"
    with patch(f"{MODULE}.Bulb", return_value=mocked_bulb), patch(
        f"{MODULE_CONFIG_FLOW}.yeelight.Bulb", return_value=mocked_bulb
    ):
        assert await async_setup_component(
            opp,
            DOMAIN,
            {
                DOMAIN: {
                    CONF_DEVICES: {
                        IP_ADDRESS: {
                            CONF_NAME: name,
                            CONF_NIGHTLIGHT_SWITCH_TYPE: NIGHTLIGHT_SWITCH_TYPE_LIGHT,
                        }
                    }
                }
            },
        )
        await opp.async_block_till_done()

    assert opp.states.get(f"binary_sensor.{name}_nightlight") is not None
    assert opp.states.get(f"light.{name}") is not None
    assert opp.states.get(f"light.{name}_nightlight") is not None


async def test_unique_ids_device(opp: OpenPeerPower):
    """Test Yeelight unique IDs from yeelight device IDs."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            **CONFIG_ENTRY_DATA,
            CONF_NIGHTLIGHT_SWITCH: True,
        },
        unique_id=ID,
    )
    config_entry.add_to(opp.opp)

    mocked_bulb = _mocked_bulb()
    mocked_bulb.bulb_type = BulbType.WhiteTempMood
    with _patch_discovery(MODULE), patch(f"{MODULE}.Bulb", return_value=mocked_bulb):
        assert await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()

    er = await entity_registry.async_get_registry(opp)
    assert er.async_get(ENTITY_BINARY_SENSOR).unique_id == f"{ID}-nightlight_sensor"
    assert er.async_get(ENTITY_LIGHT).unique_id == ID
    assert er.async_get(ENTITY_NIGHTLIGHT).unique_id == f"{ID}-nightlight"
    assert er.async_get(ENTITY_AMBILIGHT).unique_id == f"{ID}-ambilight"


async def test_unique_ids_entry(opp: OpenPeerPower):
    """Test Yeelight unique IDs from entry IDs."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            **CONFIG_ENTRY_DATA,
            CONF_NIGHTLIGHT_SWITCH: True,
        },
    )
    config_entry.add_to(opp.opp)

    mocked_bulb = _mocked_bulb()
    mocked_bulb.bulb_type = BulbType.WhiteTempMood

    with _patch_discovery(MODULE), patch(f"{MODULE}.Bulb", return_value=mocked_bulb):
        assert await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()

    er = await entity_registry.async_get_registry(opp)
    assert (
        er.async_get(ENTITY_BINARY_SENSOR).unique_id
        == f"{config_entry.entry_id}-nightlight_sensor"
    )
    assert er.async_get(ENTITY_LIGHT).unique_id == config_entry.entry_id
    assert (
        er.async_get(ENTITY_NIGHTLIGHT).unique_id
        == f"{config_entry.entry_id}-nightlight"
    )
    assert (
        er.async_get(ENTITY_AMBILIGHT).unique_id == f"{config_entry.entry_id}-ambilight"
    )


async def test_bulb_off_while_adding_in_ha(opp: OpenPeerPower):
    """Test Yeelight off while adding to ha, for example on HA start."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            **CONFIG_ENTRY_DATA,
            CONF_HOST: IP_ADDRESS,
        },
        unique_id=ID,
    )
    config_entry.add_to(opp.opp)

    mocked_bulb = _mocked_bulb(True)
    mocked_bulb.bulb_type = BulbType.WhiteTempMood

    with patch(f"{MODULE}.Bulb", return_value=mocked_bulb), patch(
        f"{MODULE}.config_flow.yeelight.Bulb", return_value=mocked_bulb
    ):
        assert await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()

    binary_sensor_entity_id = ENTITY_BINARY_SENSOR_TEMPLATE.format(
        IP_ADDRESS.replace(".", "_")
    )
    er = await entity_registry.async_get_registry(opp)
    assert er.async_get(binary_sensor_entity_id) is None

    type(mocked_bulb).get_capabilities = MagicMock(CAPABILITIES)
    type(mocked_bulb).get_properties = MagicMock(None)

    opp.data[DOMAIN][DATA_CONFIG_ENTRIES][config_entry.entry_id][DATA_DEVICE].update()
    await opp.async_block_till_done()

    er = await entity_registry.async_get_registry(opp)
    assert er.async_get(binary_sensor_entity_id) is not None
