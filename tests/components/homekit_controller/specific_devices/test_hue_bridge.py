"""Tests for handling accessories on a Hue bridge via HomeKit."""

from tests.common import assert_lists_same, async_get_device_automations
from tests.components.homekit_controller.common import (
    Helper,
    setup_accessories_from_file,
    setup_test_accessories,
)


async def test_hue_bridge_setup(opp):
    """Test that a Hue hub can be correctly setup in OP via HomeKit."""
    accessories = await setup_accessories_from_file(opp, "hue_bridge.json")
    config_entry, pairing = await setup_test_accessories(opp, accessories)

    entity_registry = await opp.helpers.entity_registry.async_get_registry()

    # Check that the battery is correctly found and set up
    battery_id = "sensor.hue_dimmer_switch_battery"
    battery = entity_registry.async_get(battery_id)
    assert battery.unique_id == "homekit-6623462389072572-644245094400"

    battery_helper = Helper(
        opp, "sensor.hue_dimmer_switch_battery", pairing, accessories[0], config_entry
    )
    battery_state = await battery_helper.poll_and_get_state()
    assert battery_state.attributes["friendly_name"] == "Hue dimmer switch Battery"
    assert battery_state.attributes["icon"] == "mdi:battery"
    assert battery_state.state == "100"

    device_registry = await opp.helpers.device_registry.async_get_registry()

    device = device_registry.async_get(battery.device_id)
    assert device.manufacturer == "Philips"
    assert device.name == "Hue dimmer switch"
    assert device.model == "RWL021"
    assert device.sw_version == "45.1.17846"

    # The fixture file has 1 dimmer, which is a remote with 4 buttons
    # It (incorrectly) claims to support single, double and long press events
    # It also has a battery

    expected = [
        {
            "device_id": device.id,
            "domain": "sensor",
            "entity_id": "sensor.hue_dimmer_switch_battery",
            "platform": "device",
            "type": "battery_level",
        }
    ]

    for button in ("button1", "button2", "button3", "button4"):
        expected.append(
            {
                "device_id": device.id,
                "domain": "homekit_controller",
                "platform": "device",
                "type": button,
                "subtype": "single_press",
            }
        )

    triggers = await async_get_device_automations(opp, "trigger", device.id)
    assert_lists_same(triggers, expected)
