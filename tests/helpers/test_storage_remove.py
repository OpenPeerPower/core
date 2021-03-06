"""Tests for the storage helper with minimal mocking."""
import asyncio
from datetime import timedelta
import os
from unittest.mock import patch

from openpeerpower.helpers import storage
from openpeerpower.util import dt

from tests.common import async_fire_time_changed, async_test_open_peer_power


async def test_removing_while_delay_in_progress(tmpdir):
    """Test removing while delay in progress."""

    loop = asyncio.get_event_loop()
    opp = await async_test_open_peer_power(loop)

    test_dir = await opp.async_add_executor_job(tmpdir.mkdir, "storage")

    with patch.object(storage, "STORAGE_DIR", test_dir):
        real_store = storage.Store(opp, 1, "remove_me")

        await real_store.async_save({"delay": "no"})

        assert await opp.async_add_executor_job(os.path.exists, real_store.path)

        real_store.async_delay_save(lambda: {"delay": "yes"}, 1)

        await real_store.async_remove()
        assert not await opp.async_add_executor_job(os.path.exists, real_store.path)

        async_fire_time_changed(opp, dt.utcnow() + timedelta(seconds=1))
        await opp.async_block_till_done()
        assert not await opp.async_add_executor_job(os.path.exists, real_store.path)
        await opp.async_stop()
