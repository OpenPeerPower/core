"""Tests for the Sonos Alarm switch platform."""
from openpeerpower.components.sonos import DOMAIN
from openpeerpower.components.sonos.switch import (
    ATTR_DURATION,
    ATTR_ID,
    ATTR_INCLUDE_LINKED_ZONES,
    ATTR_PLAY_MODE,
    ATTR_RECURRENCE,
    ATTR_VOLUME,
)
from openpeerpower.const import ATTR_TIME, STATE_ON
from openpeerpower.helpers.entity_registry import async_get as async_get_entity_registry
from openpeerpower.setup import async_setup_component


async def setup_platform(opp, config_entry, config):
    """Set up the switch platform for testing."""
    config_entry.add_to_opp(opp)
    assert await async_setup_component(opp, DOMAIN, config)
    await opp.async_block_till_done()


async def test_entity_registry(opp, config_entry, config):
    """Test sonos device with alarm registered in the device registry."""
    await setup_platform(opp, config_entry, config)

    entity_registry = await opp.helpers.entity_registry.async_get_registry()

    assert "media_player.zone_a" in entity_registry.entities
    assert "switch.sonos_alarm_14" in entity_registry.entities


async def test_alarm_attributes(opp, config_entry, config):
    """Test for correct sonos alarm state."""
    await setup_platform(opp, config_entry, config)

    entity_registry = await opp.helpers.entity_registry.async_get_registry()

    alarm = entity_registry.entities["switch.sonos_alarm_14"]
    alarm_state = opp.states.get(alarm.entity_id)
    assert alarm_state.state == STATE_ON
    assert alarm_state.attributes.get(ATTR_TIME) == "07:00:00"
    assert alarm_state.attributes.get(ATTR_ID) == "14"
    assert alarm_state.attributes.get(ATTR_DURATION) == "02:00:00"
    assert alarm_state.attributes.get(ATTR_RECURRENCE) == "DAILY"
    assert alarm_state.attributes.get(ATTR_VOLUME) == 0.25
    assert alarm_state.attributes.get(ATTR_PLAY_MODE) == "SHUFFLE_NOREPEAT"
    assert not alarm_state.attributes.get(ATTR_INCLUDE_LINKED_ZONES)


async def test_alarm_create_delete(
    opp, config_entry, config, soco, alarm_clock, alarm_clock_extended, alarm_event
):
    """Test for correct creation and deletion of alarms during runtime."""
    soco.alarmClock = alarm_clock_extended

    await setup_platform(opp, config_entry, config)

    subscription = alarm_clock_extended.subscribe.return_value
    sub_callback = subscription.callback

    sub_callback(event=alarm_event)
    await opp.async_block_till_done()

    entity_registry = async_get_entity_registry(opp)

    assert "switch.sonos_alarm_14" in entity_registry.entities
    assert "switch.sonos_alarm_15" in entity_registry.entities

    alarm_clock_extended.ListAlarms.return_value = alarm_clock.ListAlarms.return_value
    alarm_event.increment_variable("alarm_list_version")

    sub_callback(event=alarm_event)
    await opp.async_block_till_done()

    assert "switch.sonos_alarm_14" in entity_registry.entities
    assert "switch.sonos_alarm_15" not in entity_registry.entities
