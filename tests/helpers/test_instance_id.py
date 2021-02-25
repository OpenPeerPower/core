"""Tests for instance ID helper."""
from unittest.mock import patch


async def test_get_id_empty(opp, opp_storage):
    """Get unique ID."""
    uuid = await opp.helpers.instance_id.async_get()
    assert uuid is not None
    # Assert it's stored
    assert opp_storage["core.uuid"]["data"]["uuid"] == uuid


async def test_get_id_migrate(opp, opp_storage):
    """Migrate existing file."""
    with patch(
        "openpeerpower.util.json.load_json", return_value={"uuid": "1234"}
    ), patch("os.path.isfile", return_value=True), patch("os.remove") as mock_remove:
        uuid = await opp.helpers.instance_id.async_get()

    assert uuid == "1234"

    # Assert it's stored
    assert opp_storage["core.uuid"]["data"]["uuid"] == uuid

    # assert old deleted
    assert len(mock_remove.mock_calls) == 1
