"""Test the zerproc config flow."""
from unittest.mock import patch

import pyzerproc

from openpeerpower import config_entries, setup
from openpeerpower.components.zerproc.config_flow import DOMAIN


async def test_flow_success.opp):
    """Test we get the form."""
    await setup.async_setup_component.opp, "persistent_notification", {})
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] is None

    with patch(
        "openpeerpower.components.zerproc.config_flow.pyzerproc.discover",
        return_value=["Light1", "Light2"],
    ), patch(
        "openpeerpower.components.zerproc.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.zerproc.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await.opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "Zerproc"
    assert result2["data"] == {}

    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_flow_no_devices_found.opp):
    """Test we get the form."""
    await setup.async_setup_component.opp, "persistent_notification", {})
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] is None

    with patch(
        "openpeerpower.components.zerproc.config_flow.pyzerproc.discover",
        return_value=[],
    ), patch(
        "openpeerpower.components.zerproc.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.zerproc.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )

    assert result2["type"] == "abort"
    assert result2["reason"] == "no_devices_found"
    await.opp.async_block_till_done()
    assert len(mock_setup.mock_calls) == 0
    assert len(mock_setup_entry.mock_calls) == 0


async def test_flow_exceptions_caught.opp):
    """Test we get the form."""
    await setup.async_setup_component.opp, "persistent_notification", {})
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] is None

    with patch(
        "openpeerpower.components.zerproc.config_flow.pyzerproc.discover",
        side_effect=pyzerproc.ZerprocException("TEST"),
    ), patch(
        "openpeerpower.components.zerproc.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.zerproc.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )

    assert result2["type"] == "abort"
    assert result2["reason"] == "no_devices_found"
    await.opp.async_block_till_done()
    assert len(mock_setup.mock_calls) == 0
    assert len(mock_setup_entry.mock_calls) == 0
