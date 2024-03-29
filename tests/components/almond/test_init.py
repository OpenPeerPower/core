"""Tests for Almond set up."""
from time import time
from unittest.mock import patch

import pytest

from openpeerpower import config_entries, core
from openpeerpower.components.almond import const
from openpeerpower.config import async_process_op_core_config
from openpeerpower.const import EVENT_OPENPEERPOWER_START
from openpeerpower.setup import async_setup_component
from openpeerpower.util.dt import utcnow

from tests.common import MockConfigEntry, async_fire_time_changed


@pytest.fixture(autouse=True)
def patch_opp_state(opp):
    """Mock the opp.state to be not_running."""
    opp.state = core.CoreState.not_running


async def test_set_up_oauth_remote_url(opp, aioclient_mock):
    """Test we set up Almond to connect to OPP if we have external url."""
    entry = MockConfigEntry(
        domain="almond",
        data={
            "type": const.TYPE_OAUTH2,
            "auth_implementation": "local",
            "host": "http://localhost:9999",
            "token": {"expires_at": time() + 1000, "access_token": "abcd"},
        },
    )
    entry.add_to_opp(opp)

    with patch(
        "openpeerpower.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation",
    ):
        assert await async_setup_component(opp, "almond", {})

    assert entry.state is config_entries.ConfigEntryState.LOADED

    opp.config.components.add("cloud")
    with patch("openpeerpower.components.almond.ALMOND_SETUP_DELAY", 0), patch(
        "openpeerpower.helpers.network.get_url",
        return_value="https://example.nabu.casa",
    ), patch("pyalmond.WebAlmondAPI.async_create_device") as mock_create_device:
        opp.bus.async_fire(EVENT_OPENPEERPOWER_START)
        await opp.async_block_till_done()
        async_fire_time_changed(opp, utcnow())
        await opp.async_block_till_done()

    assert len(mock_create_device.mock_calls) == 1


async def test_set_up_oauth_no_external_url(opp, aioclient_mock):
    """Test we do not set up Almond to connect to OPP if we have no external url."""
    entry = MockConfigEntry(
        domain="almond",
        data={
            "type": const.TYPE_OAUTH2,
            "auth_implementation": "local",
            "host": "http://localhost:9999",
            "token": {"expires_at": time() + 1000, "access_token": "abcd"},
        },
    )
    entry.add_to_opp(opp)

    with patch(
        "openpeerpower.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation",
    ), patch("pyalmond.WebAlmondAPI.async_create_device") as mock_create_device:
        assert await async_setup_component(opp, "almond", {})

    assert entry.state is config_entries.ConfigEntryState.LOADED
    assert len(mock_create_device.mock_calls) == 0


async def test_set_up_oppio(opp, aioclient_mock):
    """Test we do not set up Almond to connect to OPP if we use Opp.io."""
    entry = MockConfigEntry(
        domain="almond",
        data={
            "is_oppio": True,
            "type": const.TYPE_LOCAL,
            "host": "http://localhost:9999",
        },
    )
    entry.add_to_opp(opp)

    with patch("pyalmond.WebAlmondAPI.async_create_device") as mock_create_device:
        assert await async_setup_component(opp, "almond", {})

    assert entry.state is config_entries.ConfigEntryState.LOADED
    assert len(mock_create_device.mock_calls) == 0


async def test_set_up_local(opp, aioclient_mock):
    """Test we do not set up Almond to connect to OPP if we use local."""

    # Set up an internal URL, as Almond won't be set up if there is no URL available
    await async_process_op_core_config(
        opp,
        {"internal_url": "https://192.168.0.1"},
    )

    entry = MockConfigEntry(
        domain="almond",
        data={"type": const.TYPE_LOCAL, "host": "http://localhost:9999"},
    )
    entry.add_to_opp(opp)

    with patch("pyalmond.WebAlmondAPI.async_create_device") as mock_create_device:
        assert await async_setup_component(opp, "almond", {})

    assert entry.state is config_entries.ConfigEntryState.LOADED
    assert len(mock_create_device.mock_calls) == 1
