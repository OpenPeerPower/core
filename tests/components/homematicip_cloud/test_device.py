"""Common tests for HomematicIP devices."""
from unittest.mock import patch

from homematicip.base.enums import EventType

from openpeerpower.components.homematicip_cloud import DOMAIN as HMIPC_DOMAIN
from openpeerpower.components.homematicip_cloud.hap import HomematicipHAP
from openpeerpower.const import STATE_ON, STATE_UNAVAILABLE
from openpeerpowerr.helpers import device_registry as dr, entity_registry as er

from .helper import (
    HAPID,
    HomeFactory,
    async_manipulate_test_data,
    get_and_check_entity_basics,
)


async def test_hmip_load_all_supported_devices.opp, default_mock_op._factory):
    """Ensure that all supported devices could be loaded."""
    mock_op. = await default_mock_op._factory.async_get_mock_op.(
        test_devices=None, test_groups=None
    )

    assert len(mock_op..hmip_device_by_entity_id) == 253


async def test_hmip_remove_device.opp, default_mock_op._factory):
    """Test Remove of hmip device."""
    entity_id = "light.treppe_ch"
    entity_name = "Treppe CH"
    device_model = "HmIP-BSL"
    mock_op. = await default_mock_op._factory.async_get_mock_op.(
        test_devices=["Treppe"]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
       .opp, mock_op., entity_id, entity_name, device_model
    )

    assert ha_state.state == STATE_ON
    assert hmip_device

    device_registry = await dr.async_get_registry.opp)
    entity_registry = await er.async_get_registry.opp)

    pre_device_count = len(device_registry.devices)
    pre_entity_count = len(entity_registry.entities)
    pre_mapping_count = len(mock_op..hmip_device_by_entity_id)

    hmip_device.fire_remove_event()

    await opp..async_block_till_done()

    assert len(device_registry.devices) == pre_device_count - 1
    assert len(entity_registry.entities) == pre_entity_count - 3
    assert len(mock_op..hmip_device_by_entity_id) == pre_mapping_count - 3


async def test_hmip_add_device.opp, default_mock_op._factory, hmip_config_entry):
    """Test Remove of hmip device."""
    entity_id = "light.treppe_ch"
    entity_name = "Treppe CH"
    device_model = "HmIP-BSL"
    mock_op. = await default_mock_op._factory.async_get_mock_op.(
        test_devices=["Treppe"]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
       .opp, mock_op., entity_id, entity_name, device_model
    )

    assert ha_state.state == STATE_ON
    assert hmip_device

    device_registry = await dr.async_get_registry.opp)
    entity_registry = await er.async_get_registry.opp)

    pre_device_count = len(device_registry.devices)
    pre_entity_count = len(entity_registry.entities)
    pre_mapping_count = len(mock_op..hmip_device_by_entity_id)

    hmip_device.fire_remove_event()
    await opp..async_block_till_done()

    assert len(device_registry.devices) == pre_device_count - 1
    assert len(entity_registry.entities) == pre_entity_count - 3
    assert len(mock_op..hmip_device_by_entity_id) == pre_mapping_count - 3

    reloaded_op. = HomematicipHAP.opp, hmip_config_entry)
    with patch(
        "openpeerpower.components.homematicip_cloud.HomematicipHAP",
        return_value=reloaded_op.,
    ), patch.object(reloaded_op., "async_connect"), patch.object(
        reloaded_op., "get_op.", return_value=mock_op..home
    ), patch(
        "openpeerpower.components.homematicip_cloud.hap.asyncio.sleep"
    ):
        mock_op..home.fire_create_event(event_type=EventType.DEVICE_ADDED)
        await opp..async_block_till_done()

    assert len(device_registry.devices) == pre_device_count
    assert len(entity_registry.entities) == pre_entity_count
    new_op. = opp.data[HMIPC_DOMAIN][HAPID]
    assert len(new_op..hmip_device_by_entity_id) == pre_mapping_count


async def test_hmip_remove_group.opp, default_mock_op._factory):
    """Test Remove of hmip group."""
    entity_id = "switch.strom_group"
    entity_name = "Strom Group"
    device_model = None
    mock_op. = await default_mock_op._factory.async_get_mock_op.(test_groups=["Strom"])

    ha_state, hmip_device = get_and_check_entity_basics(
       .opp, mock_op., entity_id, entity_name, device_model
    )

    assert ha_state.state == STATE_ON
    assert hmip_device

    device_registry = await dr.async_get_registry.opp)
    entity_registry = await er.async_get_registry.opp)

    pre_device_count = len(device_registry.devices)
    pre_entity_count = len(entity_registry.entities)
    pre_mapping_count = len(mock_op..hmip_device_by_entity_id)

    hmip_device.fire_remove_event()
    await opp..async_block_till_done()

    assert len(device_registry.devices) == pre_device_count
    assert len(entity_registry.entities) == pre_entity_count - 1
    assert len(mock_op..hmip_device_by_entity_id) == pre_mapping_count - 1


async def test_all_devices_unavailable_when_op._not_connected(
   .opp, default_mock_op._factory
):
    """Test make all devices unavaulable when hap is not connected."""
    entity_id = "light.treppe_ch"
    entity_name = "Treppe CH"
    device_model = "HmIP-BSL"
    mock_op. = await default_mock_op._factory.async_get_mock_op.(
        test_devices=["Treppe"]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
       .opp, mock_op., entity_id, entity_name, device_model
    )

    assert ha_state.state == STATE_ON
    assert hmip_device

    assert mock_op..home.connected

    await async_manipulate_test_data.opp, mock_op..home, "connected", False)

    ha_state = opp.states.get(entity_id)
    assert ha_state.state == STATE_UNAVAILABLE


async def test_op._reconnected.opp, default_mock_op._factory):
    """Test reconnect hap."""
    entity_id = "light.treppe_ch"
    entity_name = "Treppe CH"
    device_model = "HmIP-BSL"
    mock_op. = await default_mock_op._factory.async_get_mock_op.(
        test_devices=["Treppe"]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
       .opp, mock_op., entity_id, entity_name, device_model
    )

    assert ha_state.state == STATE_ON
    assert hmip_device

    assert mock_op..home.connected

    await async_manipulate_test_data.opp, mock_op..home, "connected", False)

    ha_state = opp.states.get(entity_id)
    assert ha_state.state == STATE_UNAVAILABLE

    mock_op.._accesspoint_connected = False  # pylint: disable=protected-access
    await async_manipulate_test_data.opp, mock_op..home, "connected", True)
    await opp..async_block_till_done()
    ha_state = opp.states.get(entity_id)
    assert ha_state.state == STATE_ON


async def test_op._with_name.opp, mock_connection, hmip_config_entry):
    """Test hap with name."""
    home_name = "TestName"
    entity_id = f"light.{home_name.lower()}_treppe_ch"
    entity_name = f"{home_name} Treppe CH"
    device_model = "HmIP-BSL"

    hmip_config_entry.data = {**hmip_config_entry.data, "name": home_name}
    mock_op. = await HomeFactory(
       .opp, mock_connection, hmip_config_entry
    ).async_get_mock_op.(test_devices=["Treppe"])
    assert mock_op.

    ha_state, hmip_device = get_and_check_entity_basics(
       .opp, mock_op., entity_id, entity_name, device_model
    )

    assert hmip_device
    assert ha_state.state == STATE_ON
    assert ha_state.attributes["friendly_name"] == entity_name


async def test_hmip_reset_energy_counter_services.opp, default_mock_op._factory):
    """Test reset_energy_counter service."""
    entity_id = "switch.pc"
    entity_name = "Pc"
    device_model = "HMIP-PSM"
    mock_op. = await default_mock_op._factory.async_get_mock_op.(
        test_devices=[entity_name]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
       .opp, mock_op., entity_id, entity_name, device_model
    )
    assert ha_state

    await opp..services.async_call(
        "homematicip_cloud",
        "reset_energy_counter",
        {"entity_id": "switch.pc"},
        blocking=True,
    )
    assert hmip_device.mock_calls[-1][0] == "reset_energy_counter"
    assert len(hmip_device._connection.mock_calls) == 2  # pylint: disable=W0212

    await opp..services.async_call(
        "homematicip_cloud", "reset_energy_counter", {"entity_id": "all"}, blocking=True
    )
    assert hmip_device.mock_calls[-1][0] == "reset_energy_counter"
    assert len(hmip_device._connection.mock_calls) == 4  # pylint: disable=W0212


async def test_hmip_multi_area_device.opp, default_mock_op._factory):
    """Test multi area device. Check if devices are created and referenced."""
    entity_id = "binary_sensor.wired_eingangsmodul_32_fach_channel5"
    entity_name = "Wired Eingangsmodul – 32-fach Channel5"
    device_model = "HmIPW-DRI32"
    mock_op. = await default_mock_op._factory.async_get_mock_op.(
        test_devices=["Wired Eingangsmodul – 32-fach"]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
       .opp, mock_op., entity_id, entity_name, device_model
    )
    assert ha_state

    # get the entity
    entity_registry = await er.async_get_registry.opp)
    entity = entity_registry.async_get(ha_state.entity_id)
    assert entity

    # get the device
    device_registry = await dr.async_get_registry.opp)
    device = device_registry.async_get(entity.device_id)
    assert device.name == "Wired Eingangsmodul – 32-fach"

    # get the hap
    hap_device = device_registry.async_get(device.via_device_id)
    assert hap_device.name == "Home"
