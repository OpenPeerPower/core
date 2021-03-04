"""The tests for the Restore component."""
from datetime import datetime
from unittest.mock import patch

from openpeerpower.const import EVENT_OPENPEERPOWER_START
from openpeerpower.core import CoreState, State
from openpeerpower.exceptions import OpenPeerPowerError
from openpeerpower.helpers.entity import Entity
from openpeerpower.helpers.restore_state import (
    DATA_RESTORE_STATE_TASK,
    STORAGE_KEY,
    RestoreEntity,
    RestoreStateData,
    StoredState,
)
from openpeerpower.util import dt as dt_util


async def test_caching_data(opp):
    """Test that we cache data."""
    now = dt_util.utcnow()
    stored_states = [
        StoredState(State("input_boolean.b0", "on"), now),
        StoredState(State("input_boolean.b1", "on"), now),
        StoredState(State("input_boolean.b2", "on"), now),
    ]

    data = await RestoreStateData.async_get_instance(opp)
    await opp.async_block_till_done()
    await data.store.async_save([state.as_dict() for state in stored_states])

    # Emulate a fresh load
    opp.data[DATA_RESTORE_STATE_TASK] = None

    entity = RestoreEntity()
    entity.opp = opp
    entity.entity_id = "input_boolean.b1"

    # Mock that only b1 is present this run
    with patch(
        "openpeerpower.helpers.restore_state.Store.async_save"
    ) as mock_write_data:
        state = await entity.async_get_last_state()
        await opp.async_block_till_done()

    assert state is not None
    assert state.entity_id == "input_boolean.b1"
    assert state.state == "on"

    assert mock_write_data.called


async def test_opp_starting(opp):
    """Test that we cache data."""
    opp.state = CoreState.starting

    now = dt_util.utcnow()
    stored_states = [
        StoredState(State("input_boolean.b0", "on"), now),
        StoredState(State("input_boolean.b1", "on"), now),
        StoredState(State("input_boolean.b2", "on"), now),
    ]

    data = await RestoreStateData.async_get_instance(opp)
    await opp.async_block_till_done()
    await data.store.async_save([state.as_dict() for state in stored_states])

    # Emulate a fresh load
    opp.data[DATA_RESTORE_STATE_TASK] = None

    entity = RestoreEntity()
    entity.opp = opp
    entity.entity_id = "input_boolean.b1"

    # Mock that only b1 is present this run
    states = [State("input_boolean.b1", "on")]
    with patch(
        "openpeerpower.helpers.restore_state.Store.async_save"
    ) as mock_write_data, patch.object(opp.states, "async_all", return_value=states):
        state = await entity.async_get_last_state()
        await opp.async_block_till_done()

    assert state is not None
    assert state.entity_id == "input_boolean.b1"
    assert state.state == "on"

    # Assert that no data was written yet, since opp is still starting.
    assert not mock_write_data.called

    # Finish opp startup
    with patch(
        "openpeerpower.helpers.restore_state.Store.async_save"
    ) as mock_write_data:
        opp.bus.async_fire(EVENT_OPENPEERPOWER_START)
        await opp.async_block_till_done()

    # Assert that this session states were written
    assert mock_write_data.called


async def test_dump_data(opp):
    """Test that we cache data."""
    states = [
        State("input_boolean.b0", "on"),
        State("input_boolean.b1", "on"),
        State("input_boolean.b2", "on"),
        State("input_boolean.b5", "unavailable", {"restored": True}),
    ]

    entity = Entity()
    entity.opp = opp
    entity.entity_id = "input_boolean.b0"
    await entity.async_internal_added_to_opp()

    entity = RestoreEntity()
    entity.opp = opp
    entity.entity_id = "input_boolean.b1"
    await entity.async_internal_added_to_opp()

    data = await RestoreStateData.async_get_instance(opp)
    now = dt_util.utcnow()
    data.last_states = {
        "input_boolean.b0": StoredState(State("input_boolean.b0", "off"), now),
        "input_boolean.b1": StoredState(State("input_boolean.b1", "off"), now),
        "input_boolean.b2": StoredState(State("input_boolean.b2", "off"), now),
        "input_boolean.b3": StoredState(State("input_boolean.b3", "off"), now),
        "input_boolean.b4": StoredState(
            State("input_boolean.b4", "off"),
            datetime(1985, 10, 26, 1, 22, tzinfo=dt_util.UTC),
        ),
        "input_boolean.b5": StoredState(State("input_boolean.b5", "off"), now),
    }

    with patch(
        "openpeerpower.helpers.restore_state.Store.async_save"
    ) as mock_write_data, patch.object(opp.states, "async_all", return_value=states):
        await data.async_dump_states()

    assert mock_write_data.called
    args = mock_write_data.mock_calls[0][1]
    written_states = args[0]

    # b0 should not be written, since it didn't extend RestoreEntity
    # b1 should be written, since it is present in the current run
    # b2 should not be written, since it is not registered with the helper
    # b3 should be written, since it is still not expired
    # b4 should not be written, since it is now expired
    # b5 should be written, since current state is restored by entity registry
    assert len(written_states) == 3
    assert written_states[0]["state"]["entity_id"] == "input_boolean.b1"
    assert written_states[0]["state"]["state"] == "on"
    assert written_states[1]["state"]["entity_id"] == "input_boolean.b3"
    assert written_states[1]["state"]["state"] == "off"
    assert written_states[2]["state"]["entity_id"] == "input_boolean.b5"
    assert written_states[2]["state"]["state"] == "off"

    # Test that removed entities are not persisted
    await entity.async_remove()

    with patch(
        "openpeerpower.helpers.restore_state.Store.async_save"
    ) as mock_write_data, patch.object(opp.states, "async_all", return_value=states):
        await data.async_dump_states()

    assert mock_write_data.called
    args = mock_write_data.mock_calls[0][1]
    written_states = args[0]
    assert len(written_states) == 2
    assert written_states[0]["state"]["entity_id"] == "input_boolean.b3"
    assert written_states[0]["state"]["state"] == "off"
    assert written_states[1]["state"]["entity_id"] == "input_boolean.b5"
    assert written_states[1]["state"]["state"] == "off"


async def test_dump_error(opp):
    """Test that we cache data."""
    states = [
        State("input_boolean.b0", "on"),
        State("input_boolean.b1", "on"),
        State("input_boolean.b2", "on"),
    ]

    entity = Entity()
    entity.opp = opp
    entity.entity_id = "input_boolean.b0"
    await entity.async_internal_added_to_opp()

    entity = RestoreEntity()
    entity.opp = opp
    entity.entity_id = "input_boolean.b1"
    await entity.async_internal_added_to_opp()

    data = await RestoreStateData.async_get_instance(opp)

    with patch(
        "openpeerpower.helpers.restore_state.Store.async_save",
        side_effect=OpenPeerPowerError,
    ) as mock_write_data, patch.object(opp.states, "async_all", return_value=states):
        await data.async_dump_states()

    assert mock_write_data.called


async def test_load_error(opp):
    """Test that we cache data."""
    entity = RestoreEntity()
    entity.opp = opp
    entity.entity_id = "input_boolean.b1"

    with patch(
        "openpeerpower.helpers.storage.Store.async_load",
        side_effect=OpenPeerPowerError,
    ):
        state = await entity.async_get_last_state()

    assert state is None


async def test_state_saved_on_remove(opp):
    """Test that we save entity state on removal."""
    entity = RestoreEntity()
    entity.opp = opp
    entity.entity_id = "input_boolean.b0"
    await entity.async_internal_added_to_opp()

    now = dt_util.utcnow()
    opp.states.async_set(
        "input_boolean.b0", "on", {"complicated": {"value": {1, 2, now}}}
    )

    data = await RestoreStateData.async_get_instance(opp)

    # No last states should currently be saved
    assert not data.last_states

    await entity.async_remove()

    # We should store the input boolean state when it is removed
    state = data.last_states["input_boolean.b0"].state
    assert state.state == "on"
    assert isinstance(state.attributes["complicated"]["value"], list)
    assert set(state.attributes["complicated"]["value"]) == {1, 2, now.isoformat()}


async def test_restoring_invalid_entity_id(opp, opp_storage):
    """Test restoring invalid entity IDs."""
    entity = RestoreEntity()
    entity.opp = opp
    entity.entity_id = "test.invalid__entity_id"
    now = dt_util.utcnow().isoformat()
    opp_storage[STORAGE_KEY] = {
        "version": 1,
        "key": STORAGE_KEY,
        "data": [
            {
                "state": {
                    "entity_id": "test.invalid__entity_id",
                    "state": "off",
                    "attributes": {},
                    "last_changed": now,
                    "last_updated": now,
                    "context": {
                        "id": "3c2243ff5f30447eb12e7348cfd5b8ff",
                        "user_id": None,
                    },
                },
                "last_seen": dt_util.utcnow().isoformat(),
            }
        ],
    }

    state = await entity.async_get_last_state()
    assert state is None
