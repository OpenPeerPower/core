"""Test discovery of entities for device-specific schemas for the Z-Wave JS integration."""
import pytest

from openpeerpower.components.zwave_js.discovery import (
    FirmwareVersionRange,
    ZWaveDiscoverySchema,
    ZWaveValueDiscoverySchema,
)


async def test_iblinds_v2(opp, client, iblinds_v2, integration):
    """Test that an iBlinds v2.0 multilevel switch value is discovered as a cover."""
    node = iblinds_v2
    assert node.device_class.specific.label == "Unused"

    state = opp.states.get("light.window_blind_controller")
    assert not state

    state = opp.states.get("cover.window_blind_controller")
    assert state


async def test_ge_12730(opp, client, ge_12730, integration):
    """Test GE 12730 Fan Controller v2.0 multilevel switch is discovered as a fan."""
    node = ge_12730
    assert node.device_class.specific.label == "Multilevel Power Switch"

    state = opp.states.get("light.in_wall_smart_fan_control")
    assert not state

    state = opp.states.get("fan.in_wall_smart_fan_control")
    assert state


async def test_inovelli_lzw36(opp, client, inovelli_lzw36, integration):
    """Test LZW36 Fan Controller multilevel switch endpoint 2 is discovered as a fan."""
    node = inovelli_lzw36
    assert node.device_class.specific.label == "Unused"

    state = opp.states.get("light.family_room_combo")
    assert state.state == "off"

    state = opp.states.get("fan.family_room_combo_2")
    assert state


async def test_vision_security_zl7432(opp, client, vision_security_zl7432, integration):
    """Test Vision Security ZL7432 is caught by the device specific discovery."""
    for entity_id in (
        "switch.in_wall_dual_relay_switch",
        "switch.in_wall_dual_relay_switch_2",
    ):
        state = opp.states.get(entity_id)
        assert state
        assert state.attributes["assumed_state"]


async def test_firmware_version_range_exception(opp):
    """Test FirmwareVersionRange exception."""
    with pytest.raises(ValueError):
        ZWaveDiscoverySchema(
            "test",
            ZWaveValueDiscoverySchema(command_class=1),
            firmware_version_range=FirmwareVersionRange(),
        )
