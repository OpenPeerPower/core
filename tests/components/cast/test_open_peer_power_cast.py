"""Test Open Peer Power Cast."""

from unittest.mock import patch

from openpeerpower import config_entries
from openpeerpower.components.cast import open_peer_power_cast
from openpeerpower.config import async_process_op_core_config

from tests.common import MockConfigEntry, async_mock_signal


async def test_service_show_view_dashboard(opp, mock_zeroconf):
    """Test casting a specific dashboard."""
    await async_process_op_core_config(
        opp,
        {"external_url": "https://example.com"},
    )
    await open_peer_power_cast.async_setup_op_cast(opp, MockConfigEntry())
    calls = async_mock_signal(opp, open_peer_power_cast.SIGNAL_OPP_CAST_SHOW_VIEW)

    await opp.services.async_call(
        "cast",
        "show_lovelace_view",
        {
            "entity_id": "media_player.kitchen",
            "view_path": "mock_path",
            "dashboard_path": "mock-dashboard",
        },
        blocking=True,
    )

    assert len(calls) == 1
    _controller, entity_id, view_path, url_path = calls[0]
    assert entity_id == "media_player.kitchen"
    assert view_path == "mock_path"
    assert url_path == "mock-dashboard"


async def test_remove_entry(opp, mock_zeroconf):
    """Test removing config entry removes user."""
    entry = MockConfigEntry(
        connection_class=config_entries.CONN_CLASS_LOCAL_PUSH,
        data={},
        domain="cast",
        title="Google Cast",
    )

    entry.add_to_opp(opp)

    with patch(
        "openpeerpower.components.cast.media_player._async_setup_platform"
    ), patch(
        "pychromecast.discovery.discover_chromecasts", return_value=(True, None)
    ), patch(
        "pychromecast.discovery.stop_discovery"
    ):
        assert await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()
    assert "cast" in opp.config.components

    user_id = entry.data.get("user_id")
    assert await opp.auth.async_get_user(user_id)

    assert await opp.config_entries.async_remove(entry.entry_id)
    assert not await opp.auth.async_get_user(user_id)
