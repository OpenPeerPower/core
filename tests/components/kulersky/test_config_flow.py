"""Test the Kuler Sky config flow."""
from unittest.mock import patch

import pykulersky

from openpeerpower import config_entries, setup
from openpeerpower.components.kulersky.config_flow import DOMAIN


async def test_flow_success.opp):
    """Test we get the form."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] is None

    with patch(
        "openpeerpower.components.kulersky.config_flow.pykulersky.discover_bluetooth_devices",
        return_value=[
            {
                "address": "AA:BB:CC:11:22:33",
                "name": "Bedroom",
            }
        ],
    ), patch(
        "openpeerpower.components.kulersky.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.kulersky.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "Kuler Sky"
    assert result2["data"] == {}

    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_flow_no_devices_found.opp):
    """Test we get the form."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] is None

    with patch(
        "openpeerpower.components.kulersky.config_flow.pykulersky.discover_bluetooth_devices",
        return_value=[],
    ), patch(
        "openpeerpower.components.kulersky.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.kulersky.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )

    assert result2["type"] == "abort"
    assert result2["reason"] == "no_devices_found"
    await opp.async_block_till_done()
    assert len(mock_setup.mock_calls) == 0
    assert len(mock_setup_entry.mock_calls) == 0


async def test_flow_exceptions_caught.opp):
    """Test we get the form."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] is None

    with patch(
        "openpeerpower.components.kulersky.config_flow.pykulersky.discover_bluetooth_devices",
        side_effect=pykulersky.PykulerskyException("TEST"),
    ), patch(
        "openpeerpower.components.kulersky.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.kulersky.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )

    assert result2["type"] == "abort"
    assert result2["reason"] == "no_devices_found"
    await opp.async_block_till_done()
    assert len(mock_setup.mock_calls) == 0
    assert len(mock_setup_entry.mock_calls) == 0
