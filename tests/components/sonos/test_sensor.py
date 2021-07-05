"""Tests for the Sonos battery sensor platform."""
from pysonos.exceptions import NotSupportedException

from openpeerpower.components.sonos import DOMAIN
from openpeerpower.components.sonos.binary_sensor import ATTR_BATTERY_POWER_SOURCE
from openpeerpower.const import STATE_OFF, STATE_ON
from openpeerpower.setup import async_setup_component


async def setup_platform(opp, config_entry, config):
    """Set up the media player platform for testing."""
    config_entry.add_to_opp(opp)
    assert await async_setup_component(opp, DOMAIN, config)
    await opp.async_block_till_done()


async def test_entity_registry_unsupported(opp, config_entry, config, soco):
    """Test sonos device without battery registered in the device registry."""
    soco.get_battery_info.side_effect = NotSupportedException

    await setup_platform(opp, config_entry, config)

    entity_registry = await opp.helpers.entity_registry.async_get_registry()

    assert "media_player.zone_a" in entity_registry.entities
    assert "sensor.zone_a_battery" not in entity_registry.entities
    assert "binary_sensor.zone_a_power" not in entity_registry.entities


async def test_entity_registry_supported(opp, config_entry, config, soco):
    """Test sonos device with battery registered in the device registry."""
    await setup_platform(opp, config_entry, config)

    entity_registry = await opp.helpers.entity_registry.async_get_registry()

    assert "media_player.zone_a" in entity_registry.entities
    assert "sensor.zone_a_battery" in entity_registry.entities
    assert "binary_sensor.zone_a_power" in entity_registry.entities


async def test_battery_attributes(opp, config_entry, config, soco):
    """Test sonos device with battery state."""
    await setup_platform(opp, config_entry, config)

    entity_registry = await opp.helpers.entity_registry.async_get_registry()

    battery = entity_registry.entities["sensor.zone_a_battery"]
    battery_state = opp.states.get(battery.entity_id)
    assert battery_state.state == "100"
    assert battery_state.attributes.get("unit_of_measurement") == "%"

    power = entity_registry.entities["binary_sensor.zone_a_power"]
    power_state = opp.states.get(power.entity_id)
    assert power_state.state == STATE_ON
    assert (
        power_state.attributes.get(ATTR_BATTERY_POWER_SOURCE) == "SONOS_CHARGING_RING"
    )


async def test_battery_on_S1(opp, config_entry, config, soco, battery_event):
    """Test battery state updates on a Sonos S1 device."""
    soco.get_battery_info.return_value = {}

    await setup_platform(opp, config_entry, config)

    subscription = soco.deviceProperties.subscribe.return_value
    sub_callback = subscription.callback

    entity_registry = await opp.helpers.entity_registry.async_get_registry()

    assert "sensor.zone_a_battery" not in entity_registry.entities
    assert "binary_sensor.zone_a_power" not in entity_registry.entities

    # Update the speaker with a callback event
    sub_callback(battery_event)
    await opp.async_block_till_done()

    battery = entity_registry.entities["sensor.zone_a_battery"]
    battery_state = opp.states.get(battery.entity_id)
    assert battery_state.state == "100"

    power = entity_registry.entities["binary_sensor.zone_a_power"]
    power_state = opp.states.get(power.entity_id)
    assert power_state.state == STATE_OFF
    assert power_state.attributes.get(ATTR_BATTERY_POWER_SOURCE) == "BATTERY"
