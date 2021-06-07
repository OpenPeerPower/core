"""Tests for the Cast integration."""
from unittest.mock import patch

from openpeerpower.components import cast
from openpeerpower.setup import async_setup_component


async def test_import(opp, caplog):
    """Test that specifying config will create an entry."""
    with patch(
        "openpeerpower.components.cast.async_setup_entry", return_value=True
    ) as mock_setup:
        await async_setup_component(
            opp,
            cast.DOMAIN,
            {
                "cast": {
                    "media_player": [
                        {"uuid": "abcd"},
                        {"uuid": "abcd", "ignore_cec": "milk"},
                        {"uuid": "efgh", "ignore_cec": "beer"},
                        {"incorrect": "config"},
                    ]
                }
            },
        )
        await opp.async_block_till_done()

    assert len(mock_setup.mock_calls) == 1

    assert len(opp.config_entries.async_entries("cast")) == 1
    entry = opp.config_entries.async_entries("cast")[0]
    assert set(entry.data["ignore_cec"]) == {"milk", "beer"}
    assert set(entry.data["uuid"]) == {"abcd", "efgh"}

    assert "Invalid config '{'incorrect': 'config'}'" in caplog.text


async def test_not_configuring_cast_not_creates_entry(opp):
    """Test that an empty config does not create an entry."""
    with patch(
        "openpeerpower.components.cast.async_setup_entry", return_value=True
    ) as mock_setup:
        await async_setup_component(opp, cast.DOMAIN, {})
        await opp.async_block_till_done()

    assert len(mock_setup.mock_calls) == 0
