"""Test the Logitech Harmony Hub entities with connection state changes."""

from datetime import timedelta

from openpeerpower.components.harmony.const import DOMAIN
from openpeerpower.const import (
    CONF_HOST,
    CONF_NAME,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from openpeerpower.util import utcnow

from .const import ENTITY_PLAY_MUSIC, ENTITY_REMOTE, ENTITY_WATCH_TV, HUB_NAME

from tests.common import MockConfigEntry, async_fire_time_changed


async def test_connection_state_changes(mock_hc, opp, mock_write_config):
    """Ensure connection changes are reflected in the switch states."""
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "192.0.2.0", CONF_NAME: HUB_NAME}
    )

    entry.add_to_opp(opp)
    await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    data = opp.data[DOMAIN][entry.entry_id]

    # mocks start with current activity == Watch TV
    assert opp.states.is_state(ENTITY_REMOTE, STATE_ON)
    assert opp.states.is_state(ENTITY_WATCH_TV, STATE_ON)
    assert opp.states.is_state(ENTITY_PLAY_MUSIC, STATE_OFF)

    data._disconnected()
    await opp.async_block_till_done()

    # Entities do not immediately show as unavailable
    assert opp.states.is_state(ENTITY_REMOTE, STATE_ON)
    assert opp.states.is_state(ENTITY_WATCH_TV, STATE_ON)
    assert opp.states.is_state(ENTITY_PLAY_MUSIC, STATE_OFF)

    future_time = utcnow() + timedelta(seconds=10)
    async_fire_time_changed(opp, future_time)
    await opp.async_block_till_done()
    assert opp.states.is_state(ENTITY_REMOTE, STATE_UNAVAILABLE)
    assert opp.states.is_state(ENTITY_WATCH_TV, STATE_UNAVAILABLE)
    assert opp.states.is_state(ENTITY_PLAY_MUSIC, STATE_UNAVAILABLE)

    data._connected()
    await opp.async_block_till_done()

    assert opp.states.is_state(ENTITY_REMOTE, STATE_ON)
    assert opp.states.is_state(ENTITY_WATCH_TV, STATE_ON)
    assert opp.states.is_state(ENTITY_PLAY_MUSIC, STATE_OFF)

    data._disconnected()
    data._connected()
    future_time = utcnow() + timedelta(seconds=10)
    async_fire_time_changed(opp, future_time)

    await opp.async_block_till_done()
    assert opp.states.is_state(ENTITY_REMOTE, STATE_ON)
    assert opp.states.is_state(ENTITY_WATCH_TV, STATE_ON)
    assert opp.states.is_state(ENTITY_PLAY_MUSIC, STATE_OFF)
