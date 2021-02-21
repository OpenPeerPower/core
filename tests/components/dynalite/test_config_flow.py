"""Test Dynalite config flow."""

from unittest.mock import AsyncMock, patch

import pytest

from openpeerpower import config_entries
from openpeerpower.components import dynalite

from tests.common import MockConfigEntry


@pytest.mark.parametrize(
    "first_con, second_con,exp_type, exp_result, exp_reason",
    [
        (True, True, "create_entry", "loaded", ""),
        (False, False, "abort", "", "no_connection"),
        (True, False, "create_entry", "setup_retry", ""),
    ],
)
async def test_flow.opp, first_con, second_con, exp_type, exp_result, exp_reason):
    """Run a flow with or without errors and return result."""
    host = "1.2.3.4"
    with patch(
        "openpeerpower.components.dynalite.bridge.DynaliteDevices.async_setup",
        side_effect=[first_con, second_con],
    ):
        result = await.opp.config_entries.flow.async_init(
            dynalite.DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={dynalite.CONF_HOST: host},
        )
        await opp.async_block_till_done()
    assert result["type"] == exp_type
    if exp_result:
        assert result["result"].state == exp_result
    if exp_reason:
        assert result["reason"] == exp_reason


async def test_existing.opp):
    """Test when the entry exists with the same config."""
    host = "1.2.3.4"
    MockConfigEntry(
        domain=dynalite.DOMAIN, data={dynalite.CONF_HOST: host}
    ).add_to_opp.opp)
    with patch(
        "openpeerpower.components.dynalite.bridge.DynaliteDevices.async_setup",
        return_value=True,
    ):
        result = await.opp.config_entries.flow.async_init(
            dynalite.DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={dynalite.CONF_HOST: host},
        )
    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


async def test_existing_update.opp):
    """Test when the entry exists with a different config."""
    host = "1.2.3.4"
    port1 = 7777
    port2 = 8888
    entry = MockConfigEntry(
        domain=dynalite.DOMAIN,
        data={dynalite.CONF_HOST: host, dynalite.CONF_PORT: port1},
    )
    entry.add_to_opp.opp)
    with patch(
        "openpeerpower.components.dynalite.bridge.DynaliteDevices"
    ) as mock_dyn_dev:
        mock_dyn_dev().async_setup = AsyncMock(return_value=True)
        assert await.opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()
        mock_dyn_dev().configure.assert_called_once()
        assert mock_dyn_dev().configure.mock_calls[0][1][0]["port"] == port1
        result = await.opp.config_entries.flow.async_init(
            dynalite.DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={dynalite.CONF_HOST: host, dynalite.CONF_PORT: port2},
        )
        await opp.async_block_till_done()
        assert mock_dyn_dev().configure.call_count == 2
        assert mock_dyn_dev().configure.mock_calls[1][1][0]["port"] == port2
    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


async def test_two_entries.opp):
    """Test when two different entries exist with different hosts."""
    host1 = "1.2.3.4"
    host2 = "5.6.7.8"
    MockConfigEntry(
        domain=dynalite.DOMAIN, data={dynalite.CONF_HOST: host1}
    ).add_to_opp.opp)
    with patch(
        "openpeerpower.components.dynalite.bridge.DynaliteDevices.async_setup",
        return_value=True,
    ):
        result = await.opp.config_entries.flow.async_init(
            dynalite.DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={dynalite.CONF_HOST: host2},
        )
    assert result["type"] == "create_entry"
    assert result["result"].state == "loaded"
