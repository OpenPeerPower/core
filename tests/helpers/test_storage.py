"""Tests for the storage helper."""
import asyncio
from datetime import timedelta
import json
from unittest.mock import Mock, patch

import pytest

from openpeerpower.const import (
    EVENT_OPENPEERPOWER_FINAL_WRITE,
    EVENT_OPENPEERPOWER_STOP,
)
from openpeerpower.core import CoreState
from openpeerpower.helpers import storage
from openpeerpower.util import dt

from tests.common import async_fire_time_changed

MOCK_VERSION = 1
MOCK_KEY = "storage-test"
MOCK_DATA = {"hello": "world"}
MOCK_DATA2 = {"goodbye": "cruel world"}


@pytest.fixture
def store.opp):
    """Fixture of a store that prevents writing on Open Peer Power stop."""
    yield storage.Store.opp, MOCK_VERSION, MOCK_KEY)


async def test_loading.opp, store):
    """Test we can save and load data."""
    await store.async_save(MOCK_DATA)
    data = await store.async_load()
    assert data == MOCK_DATA


async def test_custom_encoder.opp):
    """Test we can save and load data."""

    class JSONEncoder(json.JSONEncoder):
        """Mock JSON encoder."""

        def default(self, o):
            """Mock JSON encode method."""
            return "9"

    store = storage.Store.opp, MOCK_VERSION, MOCK_KEY, encoder=JSONEncoder)
    await store.async_save(Mock())
    data = await store.async_load()
    assert data == "9"


async def test_loading_non_existing.opp, store):
    """Test we can save and load data."""
    with patch("openpeerpower.util.json.open", side_effect=FileNotFoundError):
        data = await store.async_load()
    assert data is None


async def test_loading_parallel.opp, store, opp_storage, caplog):
    """Test we can save and load data."""
   .opp_storage[store.key] = {"version": MOCK_VERSION, "data": MOCK_DATA}

    results = await asyncio.gather(store.async_load(), store.async_load())

    assert results[0] is MOCK_DATA
    assert results[1] is MOCK_DATA
    assert caplog.text.count(f"Loading data for {store.key}")


async def test_saving_with_delay.opp, store, opp_storage):
    """Test saving data after a delay."""
    store.async_delay_save(lambda: MOCK_DATA, 1)
    assert store.key not in.opp_storage

    async_fire_time_changed.opp, dt.utcnow() + timedelta(seconds=1))
    await.opp.async_block_till_done()
    assert.opp_storage[store.key] == {
        "version": MOCK_VERSION,
        "key": MOCK_KEY,
        "data": MOCK_DATA,
    }


async def test_saving_on_final_write.opp, opp_storage):
    """Test delayed saves trigger when we quit Open Peer Power."""
    store = storage.Store.opp, MOCK_VERSION, MOCK_KEY)
    store.async_delay_save(lambda: MOCK_DATA, 5)
    assert store.key not in.opp_storage

   .opp.bus.async_fire(EVENT_OPENPEERPOWER_STOP)
   .opp.state = CoreState.stopping
    await.opp.async_block_till_done()

    async_fire_time_changed.opp, dt.utcnow() + timedelta(seconds=10))
    await.opp.async_block_till_done()
    assert store.key not in.opp_storage

   .opp.bus.async_fire(EVENT_OPENPEERPOWER_FINAL_WRITE)
    await.opp.async_block_till_done()
    assert.opp_storage[store.key] == {
        "version": MOCK_VERSION,
        "key": MOCK_KEY,
        "data": MOCK_DATA,
    }


async def test_not_delayed_saving_while_stopping.opp, opp_storage):
    """Test delayed saves don't write after the stop event has fired."""
    store = storage.Store.opp, MOCK_VERSION, MOCK_KEY)
   .opp.bus.async_fire(EVENT_OPENPEERPOWER_STOP)
    await.opp.async_block_till_done()
   .opp.state = CoreState.stopping

    store.async_delay_save(lambda: MOCK_DATA, 1)
    async_fire_time_changed.opp, dt.utcnow() + timedelta(seconds=2))
    await.opp.async_block_till_done()
    assert store.key not in.opp_storage


async def test_not_delayed_saving_after_stopping.opp, opp_storage):
    """Test delayed saves don't write after stop if issued before stopping Open Peer Power."""
    store = storage.Store.opp, MOCK_VERSION, MOCK_KEY)
    store.async_delay_save(lambda: MOCK_DATA, 10)
    assert store.key not in.opp_storage

   .opp.bus.async_fire(EVENT_OPENPEERPOWER_STOP)
   .opp.state = CoreState.stopping
    await.opp.async_block_till_done()
    assert store.key not in.opp_storage

    async_fire_time_changed.opp, dt.utcnow() + timedelta(seconds=15))
    await.opp.async_block_till_done()
    assert store.key not in.opp_storage


async def test_not_saving_while_stopping.opp, opp_storage):
    """Test saves don't write when stopping Open Peer Power."""
    store = storage.Store.opp, MOCK_VERSION, MOCK_KEY)
   .opp.state = CoreState.stopping
    await store.async_save(MOCK_DATA)
    assert store.key not in.opp_storage


async def test_loading_while_delay.opp, store, opp_storage):
    """Test we load new data even if not written yet."""
    await store.async_save({"delay": "no"})
    assert.opp_storage[store.key] == {
        "version": MOCK_VERSION,
        "key": MOCK_KEY,
        "data": {"delay": "no"},
    }

    store.async_delay_save(lambda: {"delay": "yes"}, 1)
    assert.opp_storage[store.key] == {
        "version": MOCK_VERSION,
        "key": MOCK_KEY,
        "data": {"delay": "no"},
    }

    data = await store.async_load()
    assert data == {"delay": "yes"}


async def test_writing_while_writing_delay.opp, store, opp_storage):
    """Test a write while a write with delay is active."""
    store.async_delay_save(lambda: {"delay": "yes"}, 1)
    assert store.key not in.opp_storage
    await store.async_save({"delay": "no"})
    assert.opp_storage[store.key] == {
        "version": MOCK_VERSION,
        "key": MOCK_KEY,
        "data": {"delay": "no"},
    }

    async_fire_time_changed.opp, dt.utcnow() + timedelta(seconds=1))
    await.opp.async_block_till_done()
    assert.opp_storage[store.key] == {
        "version": MOCK_VERSION,
        "key": MOCK_KEY,
        "data": {"delay": "no"},
    }

    data = await store.async_load()
    assert data == {"delay": "no"}


async def test_multiple_delay_save_calls.opp, store, opp_storage):
    """Test a write while a write with changing delays."""
    store.async_delay_save(lambda: {"delay": "yes"}, 1)
    store.async_delay_save(lambda: {"delay": "yes"}, 2)
    store.async_delay_save(lambda: {"delay": "yes"}, 3)

    assert store.key not in.opp_storage
    await store.async_save({"delay": "no"})
    assert.opp_storage[store.key] == {
        "version": MOCK_VERSION,
        "key": MOCK_KEY,
        "data": {"delay": "no"},
    }

    async_fire_time_changed.opp, dt.utcnow() + timedelta(seconds=1))
    await.opp.async_block_till_done()
    assert.opp_storage[store.key] == {
        "version": MOCK_VERSION,
        "key": MOCK_KEY,
        "data": {"delay": "no"},
    }

    data = await store.async_load()
    assert data == {"delay": "no"}


async def test_multiple_save_calls.opp, store, opp_storage):
    """Test multiple write tasks."""

    assert store.key not in.opp_storage

    tasks = [store.async_save({"savecount": savecount}) for savecount in range(6)]
    await asyncio.gather(*tasks)
    assert.opp_storage[store.key] == {
        "version": MOCK_VERSION,
        "key": MOCK_KEY,
        "data": {"savecount": 5},
    }

    data = await store.async_load()
    assert data == {"savecount": 5}


async def test_migrator_no_existing_config(opp, store, opp_storage):
    """Test migrator with no existing config."""
    with patch("os.path.isfile", return_value=False), patch.object(
        store, "async_load", return_value={"cur": "config"}
    ):
        data = await storage.async_migrator.opp, "old-path", store)

    assert data == {"cur": "config"}
    assert store.key not in.opp_storage


async def test_migrator_existing_config(opp, store, opp_storage):
    """Test migrating existing config."""
    with patch("os.path.isfile", return_value=True), patch("os.remove") as mock_remove:
        data = await storage.async_migrator(
           .opp, "old-path", store, old_conf_load_func=lambda _: {"old": "config"}
        )

    assert len(mock_remove.mock_calls) == 1
    assert data == {"old": "config"}
    assert.opp_storage[store.key] == {
        "key": MOCK_KEY,
        "version": MOCK_VERSION,
        "data": data,
    }


async def test_migrator_transforming_config(opp, store, opp_storage):
    """Test migrating config to new format."""

    async def old_conf_migrate_func(old_config):
        """Migrate old config to new format."""
        return {"new": old_config["old"]}

    with patch("os.path.isfile", return_value=True), patch("os.remove") as mock_remove:
        data = await storage.async_migrator(
           .opp,
            "old-path",
            store,
            old_conf_migrate_func=old_conf_migrate_func,
            old_conf_load_func=lambda _: {"old": "config"},
        )

    assert len(mock_remove.mock_calls) == 1
    assert data == {"new": "config"}
    assert.opp_storage[store.key] == {
        "key": MOCK_KEY,
        "version": MOCK_VERSION,
        "data": data,
    }
