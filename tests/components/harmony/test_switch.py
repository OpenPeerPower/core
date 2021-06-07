"""Test the Logitech Harmony Hub activity switches."""

from datetime import timedelta

from openpeerpower.components.harmony.const import DOMAIN
from openpeerpower.components.switch import (
    DOMAIN as SWITCH_DOMAIN,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    CONF_HOST,
    CONF_NAME,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from openpeerpower.util import utcnow

from .const import ENTITY_PLAY_MUSIC, ENTITY_REMOTE, ENTITY_WATCH_TV, HUB_NAME

from tests.common import MockConfigEntry, async_fire_time_changed


async def test_connection_state_changes(
    harmony_client, mock_hc, opp, mock_write_config
):
    """Ensure connection changes are reflected in the switch states."""
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "192.0.2.0", CONF_NAME: HUB_NAME}
    )

    entry.add_to_opp(opp)
    await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    # mocks start with current activity == Watch TV
    assert opp.states.is_state(ENTITY_WATCH_TV, STATE_ON)
    assert opp.states.is_state(ENTITY_PLAY_MUSIC, STATE_OFF)

    harmony_client.mock_disconnection()
    await opp.async_block_till_done()

    # Entities do not immediately show as unavailable
    assert opp.states.is_state(ENTITY_WATCH_TV, STATE_ON)
    assert opp.states.is_state(ENTITY_PLAY_MUSIC, STATE_OFF)

    future_time = utcnow() + timedelta(seconds=10)
    async_fire_time_changed(opp, future_time)
    await opp.async_block_till_done()
    assert opp.states.is_state(ENTITY_WATCH_TV, STATE_UNAVAILABLE)
    assert opp.states.is_state(ENTITY_PLAY_MUSIC, STATE_UNAVAILABLE)

    harmony_client.mock_reconnection()
    await opp.async_block_till_done()

    assert opp.states.is_state(ENTITY_WATCH_TV, STATE_ON)
    assert opp.states.is_state(ENTITY_PLAY_MUSIC, STATE_OFF)

    harmony_client.mock_disconnection()
    harmony_client.mock_reconnection()
    future_time = utcnow() + timedelta(seconds=10)
    async_fire_time_changed(opp, future_time)

    await opp.async_block_till_done()
    assert opp.states.is_state(ENTITY_WATCH_TV, STATE_ON)
    assert opp.states.is_state(ENTITY_PLAY_MUSIC, STATE_OFF)


async def test_switch_toggles(mock_hc, opp, mock_write_config):
    """Ensure calls to the switch modify the harmony state."""
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "192.0.2.0", CONF_NAME: HUB_NAME}
    )

    entry.add_to_opp(opp)
    await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    # mocks start with current activity == Watch TV
    assert opp.states.is_state(ENTITY_REMOTE, STATE_ON)
    assert opp.states.is_state(ENTITY_WATCH_TV, STATE_ON)
    assert opp.states.is_state(ENTITY_PLAY_MUSIC, STATE_OFF)

    # turn off watch tv switch
    await _toggle_switch_and_wait(opp, SERVICE_TURN_OFF, ENTITY_WATCH_TV)
    assert opp.states.is_state(ENTITY_REMOTE, STATE_OFF)
    assert opp.states.is_state(ENTITY_WATCH_TV, STATE_OFF)
    assert opp.states.is_state(ENTITY_PLAY_MUSIC, STATE_OFF)

    # turn on play music switch
    await _toggle_switch_and_wait(opp, SERVICE_TURN_ON, ENTITY_PLAY_MUSIC)
    assert opp.states.is_state(ENTITY_REMOTE, STATE_ON)
    assert opp.states.is_state(ENTITY_WATCH_TV, STATE_OFF)
    assert opp.states.is_state(ENTITY_PLAY_MUSIC, STATE_ON)

    # turn on watch tv switch
    await _toggle_switch_and_wait(opp, SERVICE_TURN_ON, ENTITY_WATCH_TV)
    assert opp.states.is_state(ENTITY_REMOTE, STATE_ON)
    assert opp.states.is_state(ENTITY_WATCH_TV, STATE_ON)
    assert opp.states.is_state(ENTITY_PLAY_MUSIC, STATE_OFF)


async def _toggle_switch_and_wait(opp, service_name, entity):
    await opp.services.async_call(
        SWITCH_DOMAIN,
        service_name,
        {ATTR_ENTITY_ID: entity},
        blocking=True,
    )
    await opp.async_block_till_done()
