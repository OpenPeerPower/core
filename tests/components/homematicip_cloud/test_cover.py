"""Tests for HomematicIP Cloud cover."""
from homematicip.base.enums import DoorCommand, DoorState

from openpeerpower.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_CURRENT_TILT_POSITION,
    DOMAIN as COVER_DOMAIN,
)
from openpeerpower.components.homematicip_cloud import DOMAIN as HMIPC_DOMAIN
from openpeerpower.const import STATE_CLOSED, STATE_OPEN, STATE_UNKNOWN
from openpeerpower.setup import async_setup_component

from .helper import async_manipulate_test_data, get_and_check_entity_basics


async def test_manually_configured_platform.opp):
    """Test that we do not set up an access point."""
    assert await async_setup_component(
       .opp, COVER_DOMAIN, {COVER_DOMAIN: {"platform": HMIPC_DOMAIN}}
    )
    assert not.opp.data.get(HMIPC_DOMAIN)


async def test_hmip_cover_shutter.opp, default_mock_hap_factory):
    """Test HomematicipCoverShutte."""
    entity_id = "cover.broll_1"
    entity_name = "BROLL_1"
    device_model = "HmIP-BROLL"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=[entity_name]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
       .opp, mock_hap, entity_id, entity_name, device_model
    )

    assert ha_state.state == "closed"
    assert ha_state.attributes["current_position"] == 0
    service_call_counter = len(hmip_device.mock_calls)

    await.opp.services.async_call(
        "cover", "open_cover", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 1
    assert hmip_device.mock_calls[-1][0] == "set_shutter_level"
    assert hmip_device.mock_calls[-1][1] == (0, 1)
    await async_manipulate_test_data.opp, hmip_device, "shutterLevel", 0)
    ha_state =.opp.states.get(entity_id)
    assert ha_state.state == STATE_OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 100

    await.opp.services.async_call(
        "cover",
        "set_cover_position",
        {"entity_id": entity_id, "position": "50"},
        blocking=True,
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 3
    assert hmip_device.mock_calls[-1][0] == "set_shutter_level"
    assert hmip_device.mock_calls[-1][1] == (0.5, 1)
    await async_manipulate_test_data.opp, hmip_device, "shutterLevel", 0.5)
    ha_state =.opp.states.get(entity_id)
    assert ha_state.state == STATE_OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 50

    await.opp.services.async_call(
        "cover", "close_cover", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 5
    assert hmip_device.mock_calls[-1][0] == "set_shutter_level"
    assert hmip_device.mock_calls[-1][1] == (1, 1)
    await async_manipulate_test_data.opp, hmip_device, "shutterLevel", 1)
    ha_state =.opp.states.get(entity_id)
    assert ha_state.state == STATE_CLOSED
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 0

    await.opp.services.async_call(
        "cover", "stop_cover", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 7
    assert hmip_device.mock_calls[-1][0] == "set_shutter_stop"
    assert hmip_device.mock_calls[-1][1] == (1,)

    await async_manipulate_test_data.opp, hmip_device, "shutterLevel", None)
    ha_state =.opp.states.get(entity_id)
    assert ha_state.state == STATE_UNKNOWN


async def test_hmip_cover_slats.opp, default_mock_hap_factory):
    """Test HomematicipCoverSlats."""
    entity_id = "cover.sofa_links"
    entity_name = "Sofa links"
    device_model = "HmIP-FBL"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=[entity_name]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
       .opp, mock_hap, entity_id, entity_name, device_model
    )

    assert ha_state.state == STATE_CLOSED
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 0
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 0
    service_call_counter = len(hmip_device.mock_calls)

    await.opp.services.async_call(
        "cover", "open_cover_tilt", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 1
    assert hmip_device.mock_calls[-1][0] == "set_slats_level"
    assert hmip_device.mock_calls[-1][1] == (0, 1)
    await async_manipulate_test_data.opp, hmip_device, "shutterLevel", 0)
    await async_manipulate_test_data.opp, hmip_device, "slatsLevel", 0)
    ha_state =.opp.states.get(entity_id)
    assert ha_state.state == STATE_OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 100
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 100

    await.opp.services.async_call(
        "cover",
        "set_cover_tilt_position",
        {"entity_id": entity_id, "tilt_position": "50"},
        blocking=True,
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 4
    assert hmip_device.mock_calls[-1][0] == "set_slats_level"
    assert hmip_device.mock_calls[-1][1] == (0.5, 1)
    await async_manipulate_test_data.opp, hmip_device, "slatsLevel", 0.5)
    ha_state =.opp.states.get(entity_id)
    assert ha_state.state == STATE_OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 100
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 50

    await.opp.services.async_call(
        "cover", "close_cover_tilt", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 6
    assert hmip_device.mock_calls[-1][0] == "set_slats_level"
    assert hmip_device.mock_calls[-1][1] == (1, 1)
    await async_manipulate_test_data.opp, hmip_device, "slatsLevel", 1)
    ha_state =.opp.states.get(entity_id)
    assert ha_state.state == STATE_OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 100
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 0

    await.opp.services.async_call(
        "cover", "stop_cover_tilt", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 8
    assert hmip_device.mock_calls[-1][0] == "set_shutter_stop"
    assert hmip_device.mock_calls[-1][1] == (1,)

    await async_manipulate_test_data.opp, hmip_device, "slatsLevel", None)
    ha_state =.opp.states.get(entity_id)
    assert not ha_state.attributes.get(ATTR_CURRENT_TILT_POSITION)

    await async_manipulate_test_data.opp, hmip_device, "shutterLevel", None)
    ha_state =.opp.states.get(entity_id)
    assert ha_state.state == STATE_UNKNOWN


async def test_hmip_multi_cover_slats.opp, default_mock_hap_factory):
    """Test HomematicipCoverSlats."""
    entity_id = "cover.wohnzimmer_fenster"
    entity_name = "Wohnzimmer Fenster"
    device_model = "HmIP-DRBLI4"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=["Jalousieaktor 1 für Hutschienenmontage – 4-fach"]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
       .opp, mock_hap, entity_id, entity_name, device_model
    )

    await async_manipulate_test_data.opp, hmip_device, "shutterLevel", 1, channel=4)
    await async_manipulate_test_data.opp, hmip_device, "slatsLevel", 1, channel=4)
    ha_state =.opp.states.get(entity_id)

    assert ha_state.state == STATE_CLOSED
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 0
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 0
    service_call_counter = len(hmip_device.mock_calls)

    await.opp.services.async_call(
        "cover", "open_cover_tilt", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 1
    assert hmip_device.mock_calls[-1][0] == "set_slats_level"
    assert hmip_device.mock_calls[-1][1] == (0, 4)
    await async_manipulate_test_data.opp, hmip_device, "shutterLevel", 0, channel=4)
    await async_manipulate_test_data.opp, hmip_device, "slatsLevel", 0, channel=4)
    ha_state =.opp.states.get(entity_id)
    assert ha_state.state == STATE_OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 100
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 100

    await.opp.services.async_call(
        "cover",
        "set_cover_tilt_position",
        {"entity_id": entity_id, "tilt_position": "50"},
        blocking=True,
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 4
    assert hmip_device.mock_calls[-1][0] == "set_slats_level"
    assert hmip_device.mock_calls[-1][1] == (0.5, 4)
    await async_manipulate_test_data.opp, hmip_device, "slatsLevel", 0.5, channel=4)
    ha_state =.opp.states.get(entity_id)
    assert ha_state.state == STATE_OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 100
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 50

    await.opp.services.async_call(
        "cover", "close_cover_tilt", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 6
    assert hmip_device.mock_calls[-1][0] == "set_slats_level"
    assert hmip_device.mock_calls[-1][1] == (1, 4)
    await async_manipulate_test_data.opp, hmip_device, "slatsLevel", 1, channel=4)
    ha_state =.opp.states.get(entity_id)
    assert ha_state.state == STATE_OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 100
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 0

    await.opp.services.async_call(
        "cover", "stop_cover_tilt", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 8
    assert hmip_device.mock_calls[-1][0] == "set_shutter_stop"
    assert hmip_device.mock_calls[-1][1] == (4,)

    await async_manipulate_test_data.opp, hmip_device, "slatsLevel", None, channel=4)
    ha_state =.opp.states.get(entity_id)
    assert not ha_state.attributes.get(ATTR_CURRENT_TILT_POSITION)

    await async_manipulate_test_data.opp, hmip_device, "shutterLevel", None, channel=4)
    ha_state =.opp.states.get(entity_id)
    assert ha_state.state == STATE_UNKNOWN


async def test_hmip_blind_module.opp, default_mock_hap_factory):
    """Test HomematicipBlindModule."""
    entity_id = "cover.sonnenschutz_balkontur"
    entity_name = "Sonnenschutz Balkontür"
    device_model = "HmIP-HDM1"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=[entity_name]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
       .opp, mock_hap, entity_id, entity_name, device_model
    )

    assert ha_state.state == STATE_OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 5
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 100
    service_call_counter = len(hmip_device.mock_calls)

    await.opp.services.async_call(
        "cover", "open_cover_tilt", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 1
    assert hmip_device.mock_calls[-1][0] == "set_secondary_shading_level"
    assert hmip_device.mock_calls[-1][2] == {
        "primaryShadingLevel": 0.94956,
        "secondaryShadingLevel": 0,
    }

    await async_manipulate_test_data.opp, hmip_device, "primaryShadingLevel", 0)
    await async_manipulate_test_data.opp, hmip_device, "secondaryShadingLevel", 0)
    await.opp.services.async_call(
        "cover", "open_cover", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 4

    assert hmip_device.mock_calls[-1][0] == "set_primary_shading_level"
    assert hmip_device.mock_calls[-1][2] == {"primaryShadingLevel": 0}

    ha_state =.opp.states.get(entity_id)
    assert ha_state.state == STATE_OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 100
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 100

    await async_manipulate_test_data.opp, hmip_device, "primaryShadingLevel", 0.5)
    await async_manipulate_test_data.opp, hmip_device, "secondaryShadingLevel", 0.5)
    await.opp.services.async_call(
        "cover",
        "set_cover_tilt_position",
        {"entity_id": entity_id, "tilt_position": "50"},
        blocking=True,
    )
    await.opp.services.async_call(
        "cover",
        "set_cover_position",
        {"entity_id": entity_id, "position": "50"},
        blocking=True,
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 8

    assert hmip_device.mock_calls[-1][0] == "set_primary_shading_level"
    assert hmip_device.mock_calls[-1][2] == {"primaryShadingLevel": 0.5}
    ha_state =.opp.states.get(entity_id)
    assert ha_state.state == STATE_OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 50
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 50

    await async_manipulate_test_data.opp, hmip_device, "primaryShadingLevel", 1)
    await async_manipulate_test_data.opp, hmip_device, "secondaryShadingLevel", 1)
    await.opp.services.async_call(
        "cover", "close_cover", {"entity_id": entity_id}, blocking=True
    )
    await.opp.services.async_call(
        "cover", "close_cover_tilt", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 12

    assert hmip_device.mock_calls[-1][0] == "set_secondary_shading_level"
    assert hmip_device.mock_calls[-1][2] == {
        "primaryShadingLevel": 1,
        "secondaryShadingLevel": 1,
    }

    ha_state =.opp.states.get(entity_id)
    assert ha_state.state == STATE_CLOSED
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 0
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 0

    await.opp.services.async_call(
        "cover", "stop_cover", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 13
    assert hmip_device.mock_calls[-1][0] == "stop"
    assert hmip_device.mock_calls[-1][1] == ()

    await.opp.services.async_call(
        "cover", "stop_cover_tilt", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 14
    assert hmip_device.mock_calls[-1][0] == "stop"
    assert hmip_device.mock_calls[-1][1] == ()

    await async_manipulate_test_data.opp, hmip_device, "secondaryShadingLevel", None)
    ha_state =.opp.states.get(entity_id)
    assert not ha_state.attributes.get(ATTR_CURRENT_TILT_POSITION)

    await async_manipulate_test_data.opp, hmip_device, "primaryShadingLevel", None)
    ha_state =.opp.states.get(entity_id)
    assert ha_state.state == STATE_UNKNOWN


async def test_hmip_garage_door_tormatic.opp, default_mock_hap_factory):
    """Test HomematicipCoverShutte."""
    entity_id = "cover.garage_door_module"
    entity_name = "Garage Door Module"
    device_model = "HmIP-MOD-TM"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=[entity_name]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
       .opp, mock_hap, entity_id, entity_name, device_model
    )

    assert ha_state.state == "closed"
    assert ha_state.attributes["current_position"] == 0
    service_call_counter = len(hmip_device.mock_calls)

    await.opp.services.async_call(
        "cover", "open_cover", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 1
    assert hmip_device.mock_calls[-1][0] == "send_door_command"
    assert hmip_device.mock_calls[-1][1] == (DoorCommand.OPEN,)
    await async_manipulate_test_data.opp, hmip_device, "doorState", DoorState.OPEN)
    ha_state =.opp.states.get(entity_id)
    assert ha_state.state == STATE_OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 100

    await.opp.services.async_call(
        "cover", "close_cover", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 3
    assert hmip_device.mock_calls[-1][0] == "send_door_command"
    assert hmip_device.mock_calls[-1][1] == (DoorCommand.CLOSE,)
    await async_manipulate_test_data.opp, hmip_device, "doorState", DoorState.CLOSED)
    ha_state =.opp.states.get(entity_id)
    assert ha_state.state == STATE_CLOSED
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 0

    await.opp.services.async_call(
        "cover", "stop_cover", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 5
    assert hmip_device.mock_calls[-1][0] == "send_door_command"
    assert hmip_device.mock_calls[-1][1] == (DoorCommand.STOP,)


async def test_hmip_garage_door_hoermann.opp, default_mock_hap_factory):
    """Test HomematicipCoverShutte."""
    entity_id = "cover.garage_door"
    entity_name = "Garage door"
    device_model = "HmIP-MOD-HO"
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(
        test_devices=[entity_name]
    )

    ha_state, hmip_device = get_and_check_entity_basics(
       .opp, mock_hap, entity_id, entity_name, device_model
    )

    assert ha_state.state == "closed"
    assert ha_state.attributes["current_position"] == 0
    service_call_counter = len(hmip_device.mock_calls)

    await.opp.services.async_call(
        "cover", "open_cover", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 1
    assert hmip_device.mock_calls[-1][0] == "send_door_command"
    assert hmip_device.mock_calls[-1][1] == (DoorCommand.OPEN,)
    await async_manipulate_test_data.opp, hmip_device, "doorState", DoorState.OPEN)
    ha_state =.opp.states.get(entity_id)
    assert ha_state.state == STATE_OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 100

    await.opp.services.async_call(
        "cover", "close_cover", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 3
    assert hmip_device.mock_calls[-1][0] == "send_door_command"
    assert hmip_device.mock_calls[-1][1] == (DoorCommand.CLOSE,)
    await async_manipulate_test_data.opp, hmip_device, "doorState", DoorState.CLOSED)
    ha_state =.opp.states.get(entity_id)
    assert ha_state.state == STATE_CLOSED
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 0

    await.opp.services.async_call(
        "cover", "stop_cover", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 5
    assert hmip_device.mock_calls[-1][0] == "send_door_command"
    assert hmip_device.mock_calls[-1][1] == (DoorCommand.STOP,)


async def test_hmip_cover_shutter_group.opp, default_mock_hap_factory):
    """Test HomematicipCoverShutteGroup."""
    entity_id = "cover.rollos_shuttergroup"
    entity_name = "Rollos ShutterGroup"
    device_model = None
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(test_groups=["Rollos"])

    ha_state, hmip_device = get_and_check_entity_basics(
       .opp, mock_hap, entity_id, entity_name, device_model
    )

    assert ha_state.state == "closed"
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 0
    service_call_counter = len(hmip_device.mock_calls)

    await.opp.services.async_call(
        "cover", "open_cover", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 1
    assert hmip_device.mock_calls[-1][0] == "set_shutter_level"
    assert hmip_device.mock_calls[-1][1] == (0,)
    await async_manipulate_test_data.opp, hmip_device, "shutterLevel", 0)
    ha_state =.opp.states.get(entity_id)
    assert ha_state.state == STATE_OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 100

    await.opp.services.async_call(
        "cover",
        "set_cover_position",
        {"entity_id": entity_id, "position": "50"},
        blocking=True,
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 3
    assert hmip_device.mock_calls[-1][0] == "set_shutter_level"
    assert hmip_device.mock_calls[-1][1] == (0.5,)
    await async_manipulate_test_data.opp, hmip_device, "shutterLevel", 0.5)
    ha_state =.opp.states.get(entity_id)
    assert ha_state.state == STATE_OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 50

    await.opp.services.async_call(
        "cover", "close_cover", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 5
    assert hmip_device.mock_calls[-1][0] == "set_shutter_level"
    assert hmip_device.mock_calls[-1][1] == (1,)
    await async_manipulate_test_data.opp, hmip_device, "shutterLevel", 1)
    ha_state =.opp.states.get(entity_id)
    assert ha_state.state == STATE_CLOSED
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 0

    await.opp.services.async_call(
        "cover", "stop_cover", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 7
    assert hmip_device.mock_calls[-1][0] == "set_shutter_stop"
    assert hmip_device.mock_calls[-1][1] == ()

    await async_manipulate_test_data.opp, hmip_device, "shutterLevel", None)
    ha_state =.opp.states.get(entity_id)
    assert ha_state.state == STATE_UNKNOWN


async def test_hmip_cover_slats_group.opp, default_mock_hap_factory):
    """Test slats with HomematicipCoverShutteGroup."""
    entity_id = "cover.rollos_shuttergroup"
    entity_name = "Rollos ShutterGroup"
    device_model = None
    mock_hap = await default_mock_hap_factory.async_get_mock_hap(test_groups=["Rollos"])

    ha_state, hmip_device = get_and_check_entity_basics(
       .opp, mock_hap, entity_id, entity_name, device_model
    )
    await async_manipulate_test_data.opp, hmip_device, "slatsLevel", 1)
    ha_state =.opp.states.get(entity_id)

    assert ha_state.state == STATE_CLOSED
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 0
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 0
    service_call_counter = len(hmip_device.mock_calls)

    await.opp.services.async_call(
        "cover",
        "set_cover_position",
        {"entity_id": entity_id, "position": "50"},
        blocking=True,
    )
    await.opp.services.async_call(
        "cover", "open_cover_tilt", {"entity_id": entity_id}, blocking=True
    )

    assert len(hmip_device.mock_calls) == service_call_counter + 2
    assert hmip_device.mock_calls[-1][0] == "set_slats_level"
    assert hmip_device.mock_calls[-1][1] == (0,)
    await async_manipulate_test_data.opp, hmip_device, "shutterLevel", 0.5)
    await async_manipulate_test_data.opp, hmip_device, "slatsLevel", 0)
    ha_state =.opp.states.get(entity_id)
    assert ha_state.state == STATE_OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 50
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 100

    await.opp.services.async_call(
        "cover",
        "set_cover_tilt_position",
        {"entity_id": entity_id, "tilt_position": "50"},
        blocking=True,
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 5
    assert hmip_device.mock_calls[-1][0] == "set_slats_level"
    assert hmip_device.mock_calls[-1][1] == (0.5,)
    await async_manipulate_test_data.opp, hmip_device, "slatsLevel", 0.5)
    ha_state =.opp.states.get(entity_id)
    assert ha_state.state == STATE_OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 50
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 50

    await.opp.services.async_call(
        "cover", "close_cover_tilt", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 7
    assert hmip_device.mock_calls[-1][0] == "set_slats_level"
    assert hmip_device.mock_calls[-1][1] == (1,)
    await async_manipulate_test_data.opp, hmip_device, "slatsLevel", 1)
    ha_state =.opp.states.get(entity_id)
    assert ha_state.state == STATE_OPEN
    assert ha_state.attributes[ATTR_CURRENT_POSITION] == 50
    assert ha_state.attributes[ATTR_CURRENT_TILT_POSITION] == 0

    await.opp.services.async_call(
        "cover", "stop_cover_tilt", {"entity_id": entity_id}, blocking=True
    )
    assert len(hmip_device.mock_calls) == service_call_counter + 9
    assert hmip_device.mock_calls[-1][0] == "set_shutter_stop"
    assert hmip_device.mock_calls[-1][1] == ()
