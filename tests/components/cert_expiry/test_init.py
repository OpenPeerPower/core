"""Tests for Cert Expiry setup."""
from datetime import timedelta
from unittest.mock import patch

from openpeerpower.components.cert_expiry.const import DOMAIN
from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.config_entries import ENTRY_STATE_LOADED, ENTRY_STATE_NOT_LOADED
from openpeerpower.const import (
    CONF_HOST,
    CONF_PORT,
    EVENT_OPENPEERPOWER_START,
    STATE_UNAVAILABLE,
)
from openpeerpower.setup import async_setup_component
import openpeerpower.util.dt as dt_util

from .const import HOST, PORT
from .helpers import future_timestamp, static_datetime

from tests.common import MockConfigEntry, async_fire_time_changed


async def test_setup_with_config.opp):
    """Test setup component with config."""
    config = {
        SENSOR_DOMAIN: [
            {"platform": DOMAIN, CONF_HOST: HOST, CONF_PORT: PORT},
            {"platform": DOMAIN, CONF_HOST: HOST, CONF_PORT: 888},
        ],
    }
    assert await async_setup_component.opp, SENSOR_DOMAIN, config) is True
    await.opp.async_block_till_done()
   .opp.bus.async_fire(EVENT_OPENPEERPOWER_START)
    await.opp.async_block_till_done()
    next_update = dt_util.utcnow() + timedelta(seconds=20)
    async_fire_time_changed.opp, next_update)

    with patch(
        "openpeerpower.components.cert_expiry.config_flow.get_cert_expiry_timestamp"
    ), patch(
        "openpeerpower.components.cert_expiry.get_cert_expiry_timestamp",
        return_value=future_timestamp(1),
    ):
        await.opp.async_block_till_done()

    assert len.opp.config_entries.async_entries(DOMAIN)) == 2


async def test_update_unique_id.opp):
    """Test updating a config entry without a unique_id."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_HOST: HOST, CONF_PORT: PORT})
    entry.add_to.opp.opp)

    config_entries =.opp.config_entries.async_entries(DOMAIN)
    assert len(config_entries) == 1
    assert entry is config_entries[0]
    assert not entry.unique_id

    with patch(
        "openpeerpower.components.cert_expiry.get_cert_expiry_timestamp",
        return_value=future_timestamp(1),
    ):
        assert await async_setup_component.opp, DOMAIN, {}) is True
        await.opp.async_block_till_done()

    assert entry.state == ENTRY_STATE_LOADED
    assert entry.unique_id == f"{HOST}:{PORT}"


@patch("openpeerpower.util.dt.utcnow", return_value=static_datetime())
async def test_unload_config_entry(mock_now,.opp):
    """Test unloading a config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: HOST, CONF_PORT: PORT},
        unique_id=f"{HOST}:{PORT}",
    )
    entry.add_to.opp.opp)

    config_entries =.opp.config_entries.async_entries(DOMAIN)
    assert len(config_entries) == 1
    assert entry is config_entries[0]

    timestamp = future_timestamp(100)
    with patch(
        "openpeerpower.components.cert_expiry.get_cert_expiry_timestamp",
        return_value=timestamp,
    ):
        assert await async_setup_component.opp, DOMAIN, {}) is True
        await.opp.async_block_till_done()

    assert entry.state == ENTRY_STATE_LOADED
    state =.opp.states.get("sensor.cert_expiry_timestamp_example_com")
    assert state.state == timestamp.isoformat()
    assert state.attributes.get("error") == "None"
    assert state.attributes.get("is_valid")

    await.opp.config_entries.async_unload(entry.entry_id)

    assert entry.state == ENTRY_STATE_NOT_LOADED
    state =.opp.states.get("sensor.cert_expiry_timestamp_example_com")
    assert state.state == STATE_UNAVAILABLE

    await.opp.config_entries.async_remove(entry.entry_id)
    await.opp.async_block_till_done()
    state =.opp.states.get("sensor.cert_expiry_timestamp_example_com")
    assert state is None
