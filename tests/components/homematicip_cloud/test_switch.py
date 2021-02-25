"""Tests for HomematicIP Cloud switch."""
from openpeerpower.components.homematicip_cloud import DOMAIN as HMIPC_DOMAIN
from openpeerpower.components.homematicip_cloud.generic_entity import (
    ATTR_GROUP_MEMBER_UNREACHABLE,
)
from openpeerpower.components.switch import (
    ATTR_CURRENT_POWER_W,
    ATTR_TODAY_ENERGY_KWH,
    DOMAIN as SWITCH_DOMAIN,
)
from openpeerpower.const import STATE_OFF, STATE_ON
from openpeerpower.setup import async_setup_component

from .helper import async_manipulate_test_data, get_and_check_entity_basics


async def test_manually_configured_platform.opp):
    """Test that we do not set up an access point."""
    assert await async_setup_component(
        opp. SWITCH_DOMAIN, {SWITCH_DOMAIN: {"platform": HMIPC_DOMAIN}}
    )
    assert not.opp.data.get(HMIPC_DOMAIN)


async def test_hmip_switch(opp, default_mock_hap_factory):
    """Test HomematicipSwitch."""
    entity_id = "switch.schrank"
    entity_name = "Schrank"
    device_model = "HMIP-PS"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=[entity_name]
    )

    op_state, hmip_device = get_and_check_entity_basics(
        opp. mock_hap, entity_id, entity_name, device_model
    )

    assert op_state.state == STATE_ON
    service_call_counter = len(hmip_device.mock_calls)

    await opp.services.async_call(
        "switch", "turn_off", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 1
    assert hmip_device.mock_calls[-1][0] == "turn_off"
    assert hmip_device.mock_calls[-1][1] == (1,)
    await async_manipulate_test_data(opp, hmip_device, "on", False)
    op_state = opp.states.get(entity_id)
    assert op_state.state == STATE_OFF

    await opp.services.async_call(
        "switch", "turn_on", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 3
    assert hmip_device.mock_calls[-1][0] == "turn_on"
    assert hmip_device.mock_calls[-1][1] == (1,)
    await async_manipulate_test_data(opp, hmip_device, "on", True)
    op_state = opp.states.get(entity_id)
    assert op_state.state == STATE_ON


async def test_hmip_switch_input(opp, default_mock_hap_factory):
    """Test HomematicipSwitch."""
    entity_id = "switch.wohnzimmer_beleuchtung"
    entity_name = "Wohnzimmer Beleuchtung"
    device_model = "HmIP-FSI16"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=[entity_name]
    )

    op_state, hmip_device = get_and_check_entity_basics(
        opp. mock_hap, entity_id, entity_name, device_model
    )

    assert op_state.state == STATE_ON
    service_call_counter = len(hmip_device.mock_calls)

    await opp.services.async_call(
        "switch", "turn_off", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 1
    assert hmip_device.mock_calls[-1][0] == "turn_off"
    assert hmip_device.mock_calls[-1][1] == (1,)
    await async_manipulate_test_data(opp, hmip_device, "on", False)
    op_state = opp.states.get(entity_id)
    assert op_state.state == STATE_OFF

    await opp.services.async_call(
        "switch", "turn_on", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 3
    assert hmip_device.mock_calls[-1][0] == "turn_on"
    assert hmip_device.mock_calls[-1][1] == (1,)
    await async_manipulate_test_data(opp, hmip_device, "on", True)
    op_state = opp.states.get(entity_id)
    assert op_state.state == STATE_ON


async def test_hmip_switch_measuring(opp, default_mock_hap_factory):
    """Test HomematicipSwitchMeasuring."""
    entity_id = "switch.pc"
    entity_name = "Pc"
    device_model = "HMIP-PSM"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=[entity_name]
    )

    op_state, hmip_device = get_and_check_entity_basics(
        opp. mock_hap, entity_id, entity_name, device_model
    )

    assert op_state.state == STATE_ON
    service_call_counter = len(hmip_device.mock_calls)

    await opp.services.async_call(
        "switch", "turn_off", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 1
    assert hmip_device.mock_calls[-1][0] == "turn_off"
    assert hmip_device.mock_calls[-1][1] == (1,)
    await async_manipulate_test_data(opp, hmip_device, "on", False)
    op_state = opp.states.get(entity_id)
    assert op_state.state == STATE_OFF

    await opp.services.async_call(
        "switch", "turn_on", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 3
    assert hmip_device.mock_calls[-1][0] == "turn_on"
    assert hmip_device.mock_calls[-1][1] == (1,)
    await async_manipulate_test_data(opp, hmip_device, "on", True)
    await async_manipulate_test_data(opp, hmip_device, "currentPowerConsumption", 50)
    op_state = opp.states.get(entity_id)
    assert op_state.state == STATE_ON
    assert op_state.attributes[ATTR_CURRENT_POWER_W] == 50
    assert op_state.attributes[ATTR_TODAY_ENERGY_KWH] == 36

    await async_manipulate_test_data(opp, hmip_device, "energyCounter", None)
    op_state = opp.states.get(entity_id)
    assert not op_state.attributes.get(ATTR_TODAY_ENERGY_KWH)


async def test_hmip_group_switch(opp, default_mock_hap_factory):
    """Test HomematicipGroupSwitch."""
    entity_id = "switch.strom_group"
    entity_name = "Strom Group"
    device_model = None
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(test_groups=["Strom"])

    op_state, hmip_device = get_and_check_entity_basics(
        opp. mock_hap, entity_id, entity_name, device_model
    )

    assert op_state.state == STATE_ON
    service_call_counter = len(hmip_device.mock_calls)

    await opp.services.async_call(
        "switch", "turn_off", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 1
    assert hmip_device.mock_calls[-1][0] == "turn_off"
    assert hmip_device.mock_calls[-1][1] == ()
    await async_manipulate_test_data(opp, hmip_device, "on", False)
    op_state = opp.states.get(entity_id)
    assert op_state.state == STATE_OFF

    await opp.services.async_call(
        "switch", "turn_on", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 3
    assert hmip_device.mock_calls[-1][0] == "turn_on"
    assert hmip_device.mock_calls[-1][1] == ()
    await async_manipulate_test_data(opp, hmip_device, "on", True)
    op_state = opp.states.get(entity_id)
    assert op_state.state == STATE_ON

    assert not op_state.attributes.get(ATTR_GROUP_MEMBER_UNREACHABLE)
    await async_manipulate_test_data(opp, hmip_device, "unreach", True)
    op_state = opp.states.get(entity_id)
    assert op_state.attributes[ATTR_GROUP_MEMBER_UNREACHABLE]


async def test_hmip_multi_switch(opp, default_mock_hap_factory):
    """Test HomematicipMultiSwitch."""
    entity_id = "switch.jalousien_1_kizi_2_schlazi_channel1"
    entity_name = "Jalousien - 1 KiZi, 2 SchlaZi Channel1"
    device_model = "HmIP-PCBS2"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=[
            "Jalousien - 1 KiZi, 2 SchlaZi",
            "Multi IO Box",
            "Heizungsaktor",
            "ioBroker",
            "Schaltaktor Verteiler",
        ]
    )

    op_state, hmip_device = get_and_check_entity_basics(
        opp. mock_hap, entity_id, entity_name, device_model
    )

    assert op_state.state == STATE_OFF
    service_call_counter = len(hmip_device.mock_calls)

    await opp.services.async_call(
        "switch", "turn_on", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 1
    assert hmip_device.mock_calls[-1][0] == "turn_on"
    assert hmip_device.mock_calls[-1][1] == (1,)
    await async_manipulate_test_data(opp, hmip_device, "on", True)
    op_state = opp.states.get(entity_id)
    assert op_state.state == STATE_ON

    await opp.services.async_call(
        "switch", "turn_off", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 3
    assert hmip_device.mock_calls[-1][0] == "turn_off"
    assert hmip_device.mock_calls[-1][1] == (1,)
    await async_manipulate_test_data(opp, hmip_device, "on", False)
    op_state = opp.states.get(entity_id)
    assert op_state.state == STATE_OFF

    op_state, hmip_device = get_and_check_entity_basics(
        opp,
        mock_hap,
        "switch.schaltaktor_verteiler_channel3",
        "Schaltaktor Verteiler Channel3",
        "HmIP-DRSI4",
    )

    assert op_state.state == STATE_OFF


async def test_hmip_wired_multi_switch(opp, default_mock_hap_factory):
    """Test HomematicipMultiSwitch."""
    entity_id = "switch.fernseher_wohnzimmer"
    entity_name = "Fernseher (Wohnzimmer)"
    device_model = "HmIPW-DRS8"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=[
            "Wired Schaltaktor – 8-fach",
        ]
    )

    op_state, hmip_device = get_and_check_entity_basics(
        opp. mock_hap, entity_id, entity_name, device_model
    )

    assert op_state.state == STATE_ON
    service_call_counter = len(hmip_device.mock_calls)

    await opp.services.async_call(
        "switch", "turn_off", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 1
    assert hmip_device.mock_calls[-1][0] == "turn_off"
    assert hmip_device.mock_calls[-1][1] == (1,)
    await async_manipulate_test_data(opp, hmip_device, "on", False)
    op_state = opp.states.get(entity_id)
    assert op_state.state == STATE_OFF

    await opp.services.async_call(
        "switch", "turn_on", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 3
    assert hmip_device.mock_calls[-1][0] == "turn_on"
    assert hmip_device.mock_calls[-1][1] == (1,)
    await async_manipulate_test_data(opp, hmip_device, "on", True)
    op_state = opp.states.get(entity_id)
    assert op_state.state == STATE_ON
