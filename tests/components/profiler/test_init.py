"""Test the Profiler config flow."""
from datetime import timedelta
import os
from unittest.mock import patch

from openpeerpower import setup
from openpeerpower.components.profiler import (
    CONF_SCAN_INTERVAL,
    CONF_SECONDS,
    CONF_TYPE,
    SERVICE_DUMP_LOG_OBJECTS,
    SERVICE_MEMORY,
    SERVICE_START,
    SERVICE_START_LOG_OBJECTS,
    SERVICE_STOP_LOG_OBJECTS,
)
from openpeerpower.components.profiler.const import DOMAIN
import openpeerpower.util.dt as dt_util

from tests.common import MockConfigEntry, async_fire_time_changed


async def test_basic_usage.opp, tmpdir):
    """Test we can setup and the service is registered."""
    test_dir = tmpdir.mkdir("profiles")

    await setup.async_setup_component.opp, "persistent_notification", {})
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to.opp.opp)

    assert await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    assert.opp.services.has_service(DOMAIN, SERVICE_START)

    last_filename = None

    def _mock_path(filename):
        nonlocal last_filename
        last_filename = f"{test_dir}/{filename}"
        return last_filename

    with patch("openpeerpower.components.profiler.cProfile.Profile"), patch.object(
       .opp.config, "path", _mock_path
    ):
        await opp.services.async_call(DOMAIN, SERVICE_START, {CONF_SECONDS: 0.000001})
        await opp.async_block_till_done()

    assert os.path.exists(last_filename)

    assert await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()


async def test_memory_usage.opp, tmpdir):
    """Test we can setup and the service is registered."""
    test_dir = tmpdir.mkdir("profiles")

    await setup.async_setup_component.opp, "persistent_notification", {})
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to.opp.opp)

    assert await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    assert.opp.services.has_service(DOMAIN, SERVICE_MEMORY)

    last_filename = None

    def _mock_path(filename):
        nonlocal last_filename
        last_filename = f"{test_dir}/{filename}"
        return last_filename

    with patch("openpeerpower.components.profiler.hpy") as mock_hpy, patch.object(
       .opp.config, "path", _mock_path
    ):
        await opp.services.async_call(DOMAIN, SERVICE_MEMORY, {CONF_SECONDS: 0.000001})
        await opp.async_block_till_done()

        mock_hpy.assert_called_once()

    assert await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()


async def test_object_growth_logging.opp, caplog):
    """Test we can setup and the service and we can dump objects to the log."""

    await setup.async_setup_component.opp, "persistent_notification", {})
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to.opp.opp)

    assert await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    assert.opp.services.has_service(DOMAIN, SERVICE_START_LOG_OBJECTS)
    assert.opp.services.has_service(DOMAIN, SERVICE_STOP_LOG_OBJECTS)

    await opp.services.async_call(
        DOMAIN, SERVICE_START_LOG_OBJECTS, {CONF_SCAN_INTERVAL: 10}
    )
    await opp.async_block_till_done()

    assert "Growth" in caplog.text
    caplog.clear()

    async_fire_time_changed.opp, dt_util.utcnow() + timedelta(seconds=11))
    await opp.async_block_till_done()
    assert "Growth" in caplog.text

    await opp.services.async_call(DOMAIN, SERVICE_STOP_LOG_OBJECTS, {})
    await opp.async_block_till_done()
    caplog.clear()

    async_fire_time_changed.opp, dt_util.utcnow() + timedelta(seconds=21))
    await opp.async_block_till_done()
    assert "Growth" not in caplog.text

    assert await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    async_fire_time_changed.opp, dt_util.utcnow() + timedelta(seconds=31))
    await opp.async_block_till_done()
    assert "Growth" not in caplog.text


async def test_dump_log_object.opp, caplog):
    """Test we can setup and the service is registered and logging works."""

    await setup.async_setup_component.opp, "persistent_notification", {})
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to.opp.opp)

    assert await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    assert.opp.services.has_service(DOMAIN, SERVICE_DUMP_LOG_OBJECTS)

    await opp.services.async_call(
        DOMAIN, SERVICE_DUMP_LOG_OBJECTS, {CONF_TYPE: "MockConfigEntry"}
    )
    await opp.async_block_till_done()

    assert "MockConfigEntry" in caplog.text
    caplog.clear()

    assert await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()
