"""Tests for the Hisense AEH-W4A1 init file."""
from unittest.mock import patch

from pyaehw4a1 import exceptions

from openpeerpower import config_entries, data_entry_flow
from openpeerpower.components import hisense_aehw4a1
from openpeerpower.setup import async_setup_component


async def test_creating_entry_sets_up_climate_discovery.opp):
    """Test setting up Hisense AEH-W4A1 loads the climate component."""
    with patch(
        "openpeerpower.components.hisense_aehw4a1.config_flow.AehW4a1.discovery",
        return_value=["1.2.3.4"],
    ):
        with patch(
            "openpeerpower.components.hisense_aehw4a1.climate.async_setup_entry",
            return_value=True,
        ) as mock_setup:
            result = await opp.config_entries.flow.async_init(
                hisense_aehw4a1.DOMAIN, context={"source": config_entries.SOURCE_USER}
            )

            # Confirmation form
            assert result["type"] == data_entry_flow.RESULT_TYPE_FORM

            result = await opp.config_entries.flow.async_configure(
                result["flow_id"], {}
            )
            assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY

            await opp.async_block_till_done()

    assert len(mock_setup.mock_calls) == 1


async def test_configuring_hisense_w4a1_create_entry.opp):
    """Test that specifying config will create an entry."""
    with patch(
        "openpeerpower.components.hisense_aehw4a1.config_flow.AehW4a1.check",
        return_value=True,
    ):
        with patch(
            "openpeerpower.components.hisense_aehw4a1.async_setup_entry",
            return_value=True,
        ) as mock_setup:
            await async_setup_component(
                opp,
                hisense_aehw4a1.DOMAIN,
                {"hisense_aehw4a1": {"ip_address": ["1.2.3.4"]}},
            )
            await opp.async_block_till_done()

    assert len(mock_setup.mock_calls) == 1


async def test_configuring_hisense_w4a1_not_creates_entry_for_device_not_found.opp):
    """Test that specifying config will not create an entry."""
    with patch(
        "openpeerpower.components.hisense_aehw4a1.config_flow.AehW4a1.check",
        side_effect=exceptions.ConnectionError,
    ):
        with patch(
            "openpeerpower.components.hisense_aehw4a1.async_setup_entry",
            return_value=True,
        ) as mock_setup:
            await async_setup_component(
                opp,
                hisense_aehw4a1.DOMAIN,
                {"hisense_aehw4a1": {"ip_address": ["1.2.3.4"]}},
            )
            await opp.async_block_till_done()

    assert len(mock_setup.mock_calls) == 0


async def test_configuring_hisense_w4a1_not_creates_entry_for_empty_import.opp):
    """Test that specifying config will not create an entry."""
    with patch(
        "openpeerpower.components.hisense_aehw4a1.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        await async_setup_component.opp, hisense_aehw4a1.DOMAIN, {})
        await opp.async_block_till_done()

    assert len(mock_setup.mock_calls) == 0
