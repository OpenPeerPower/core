"""Tests for the Gree Integration."""
from unittest.mock import patch

from openpeerpower import config_entries, data_entry_flow
from openpeerpower.components.gree.const import DOMAIN as GREE_DOMAIN

from .common import FakeDiscovery


async def test_creating_entry_sets_up_climate(opp):
    """Test setting up Gree creates the climate components."""
    with patch(
        "openpeerpower.components.gree.climate.async_setup_entry", return_value=True
    ) as setup, patch(
        "openpeerpower.components.gree.bridge.Discovery", return_value=FakeDiscovery()
    ), patch(
        "openpeerpower.components.gree.config_flow.Discovery",
        return_value=FakeDiscovery(),
    ):
        result = await opp.config_entries.flow.async_init(
            GREE_DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        # Confirmation form
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM

        result = await opp.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY

        await opp.async_block_till_done()

        assert len(setup.mock_calls) == 1


async def test_creating_entry_has_no_devices(opp):
    """Test setting up Gree creates the climate components."""
    with patch(
        "openpeerpower.components.gree.climate.async_setup_entry", return_value=True
    ) as setup, patch(
        "openpeerpower.components.gree.bridge.Discovery", return_value=FakeDiscovery()
    ) as discovery, patch(
        "openpeerpower.components.gree.config_flow.Discovery",
        return_value=FakeDiscovery(),
    ) as discovery2:
        discovery.return_value.mock_devices = []
        discovery2.return_value.mock_devices = []

        result = await opp.config_entries.flow.async_init(
            GREE_DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        # Confirmation form
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM

        result = await opp.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT

        await opp.async_block_till_done()

        assert len(setup.mock_calls) == 0
