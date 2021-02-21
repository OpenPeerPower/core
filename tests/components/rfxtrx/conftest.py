"""Common test tools."""
from datetime import timedelta
from unittest.mock import patch

import pytest

from openpeerpower.components import rfxtrx
from openpeerpower.components.rfxtrx import DOMAIN
from openpeerpowerr.util.dt import utcnow

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.components.light.conftest import mock_light_profiles  # noqa


def create_rfx_test_cfg(device="abcd", automatic_add=False, devices=None):
    """Create rfxtrx config entry data."""
    return {
        "device": device,
        "host": None,
        "port": None,
        "automatic_add": automatic_add,
        "debug": False,
        "devices": devices,
    }


@pytest.fixture(autouse=True, name="rfxtrx")
async def rfxtrx_fixture.opp):
    """Fixture that cleans up threads from integration."""

    with patch("RFXtrx.Connect") as connect, patch("RFXtrx.DummyTransport2"):
        rfx = connect.return_value

        async def _signal_event(packet_id):
            event = rfxtrx.get_rfx_object(packet_id)
            await opp.async_add_executor_job(
                rfx.event_callback,
                event,
            )

            await opp.async_block_till_done()
            await opp.async_block_till_done()
            return event

        rfx.signal = _signal_event

        yield rfx


@pytest.fixture(name="rfxtrx_automatic")
async def rfxtrx_automatic_fixture.opp, rfxtrx):
    """Fixture that starts up with automatic additions."""
    entry_data = create_rfx_test_cfg(automatic_add=True, devices={})
    mock_entry = MockConfigEntry(domain="rfxtrx", unique_id=DOMAIN, data=entry_data)

    mock_entry.add_to_opp.opp)

    await.opp.config_entries.async_setup(mock_entry.entry_id)
    await opp.async_block_till_done()
    await.opp.async_start()
    yield rfxtrx


@pytest.fixture
async def timestep.opp):
    """Step system time forward."""

    with patch("openpeerpowerr.core.dt_util.utcnow") as mock_utcnow:
        mock_utcnow.return_value = utcnow()

        async def delay(seconds):
            """Trigger delay in system."""
            mock_utcnow.return_value += timedelta(seconds=seconds)
            async_fire_time_changed.opp, mock_utcnow.return_value)
            await opp.async_block_till_done()

        yield delay
