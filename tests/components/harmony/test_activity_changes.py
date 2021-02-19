"""Test the Logitech Harmony Hub activity switches."""
from openpeerpower.components.harmony.const import DOMAIN
from openpeerpower.components.remote import ATTR_ACTIVITY, DOMAIN as REMOTE_DOMAIN
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
)

from .conftest import ACTIVITIES_TO_IDS
from .const import ENTITY_PLAY_MUSIC, ENTITY_REMOTE, ENTITY_WATCH_TV, HUB_NAME

from tests.common import MockConfigEntry


async def test_switch_toggles(mock_hc,.opp, mock_write_config):
    """Ensure calls to the switch modify the harmony state."""
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "192.0.2.0", CONF_NAME: HUB_NAME}
    )

    entry.add_to_opp.opp)
    await.opp.config_entries.async_setup(entry.entry_id)
    await.opp.async_block_till_done()

    # mocks start with current activity == Watch TV
    assert.opp.states.is_state(ENTITY_REMOTE, STATE_ON)
    assert.opp.states.is_state(ENTITY_WATCH_TV, STATE_ON)
    assert.opp.states.is_state(ENTITY_PLAY_MUSIC, STATE_OFF)

    # turn off watch tv switch
    await _toggle_switch_and_wait.opp, SERVICE_TURN_OFF, ENTITY_WATCH_TV)
    assert.opp.states.is_state(ENTITY_REMOTE, STATE_OFF)
    assert.opp.states.is_state(ENTITY_WATCH_TV, STATE_OFF)
    assert.opp.states.is_state(ENTITY_PLAY_MUSIC, STATE_OFF)

    # turn on play music switch
    await _toggle_switch_and_wait.opp, SERVICE_TURN_ON, ENTITY_PLAY_MUSIC)
    assert.opp.states.is_state(ENTITY_REMOTE, STATE_ON)
    assert.opp.states.is_state(ENTITY_WATCH_TV, STATE_OFF)
    assert.opp.states.is_state(ENTITY_PLAY_MUSIC, STATE_ON)

    # turn on watch tv switch
    await _toggle_switch_and_wait.opp, SERVICE_TURN_ON, ENTITY_WATCH_TV)
    assert.opp.states.is_state(ENTITY_REMOTE, STATE_ON)
    assert.opp.states.is_state(ENTITY_WATCH_TV, STATE_ON)
    assert.opp.states.is_state(ENTITY_PLAY_MUSIC, STATE_OFF)


async def test_remote_toggles(mock_hc,.opp, mock_write_config):
    """Ensure calls to the remote also updates the switches."""
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "192.0.2.0", CONF_NAME: HUB_NAME}
    )

    entry.add_to_opp.opp)
    await.opp.config_entries.async_setup(entry.entry_id)
    await.opp.async_block_till_done()

    # mocks start with current activity == Watch TV
    assert.opp.states.is_state(ENTITY_REMOTE, STATE_ON)
    assert.opp.states.is_state(ENTITY_WATCH_TV, STATE_ON)
    assert.opp.states.is_state(ENTITY_PLAY_MUSIC, STATE_OFF)

    # turn off remote
    await.opp.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_REMOTE},
        blocking=True,
    )
    await.opp.async_block_till_done()

    assert.opp.states.is_state(ENTITY_REMOTE, STATE_OFF)
    assert.opp.states.is_state(ENTITY_WATCH_TV, STATE_OFF)
    assert.opp.states.is_state(ENTITY_PLAY_MUSIC, STATE_OFF)

    # turn on remote, restoring the last activity
    await.opp.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_REMOTE},
        blocking=True,
    )
    await.opp.async_block_till_done()

    assert.opp.states.is_state(ENTITY_REMOTE, STATE_ON)
    assert.opp.states.is_state(ENTITY_WATCH_TV, STATE_ON)
    assert.opp.states.is_state(ENTITY_PLAY_MUSIC, STATE_OFF)

    # send new activity command, with activity name
    await.opp.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_REMOTE, ATTR_ACTIVITY: "Play Music"},
        blocking=True,
    )
    await.opp.async_block_till_done()

    assert.opp.states.is_state(ENTITY_REMOTE, STATE_ON)
    assert.opp.states.is_state(ENTITY_WATCH_TV, STATE_OFF)
    assert.opp.states.is_state(ENTITY_PLAY_MUSIC, STATE_ON)

    # send new activity command, with activity id
    await.opp.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_REMOTE, ATTR_ACTIVITY: ACTIVITIES_TO_IDS["Watch TV"]},
        blocking=True,
    )
    await.opp.async_block_till_done()

    assert.opp.states.is_state(ENTITY_REMOTE, STATE_ON)
    assert.opp.states.is_state(ENTITY_WATCH_TV, STATE_ON)
    assert.opp.states.is_state(ENTITY_PLAY_MUSIC, STATE_OFF)


async def _toggle_switch_and_wait.opp, service_name, entity):
    await.opp.services.async_call(
        SWITCH_DOMAIN,
        service_name,
        {ATTR_ENTITY_ID: entity},
        blocking=True,
    )
    await.opp.async_block_till_done()
