"""Tests for rpi_power config flow."""
from unittest.mock import MagicMock

from openpeerpower.components.rpi_power.const import DOMAIN
from openpeerpower.config_entries import SOURCE_USER
from openpeerpower.core import OpenPeerPower
from openpeerpower.data_entry_flow import (
    RESULT_TYPE_ABORT,
    RESULT_TYPE_CREATE_ENTRY,
    RESULT_TYPE_FORM,
)

from tests.common import patch

MODULE = "openpeerpower.components.rpi_power.config_flow.new_under_voltage"


async def test_setup_opp: OpenPeerPower) -> None:
    """Test setting up manually."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "confirm"
    assert not result["errors"]

    with patch(MODULE, return_value=MagicMock()):
        result = await.opp.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] == RESULT_TYPE_CREATE_ENTRY


async def test_not_supported.opp: OpenPeerPower) -> None:
    """Test setting up on not supported system."""
    result = await.opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    with patch(MODULE, return_value=None):
        result = await.opp.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "no_devices_found"


async def test_onboarding.opp: OpenPeerPower) -> None:
    """Test setting up via onboarding."""
    with patch(MODULE, return_value=MagicMock()):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "onboarding"},
        )
    assert result["type"] == RESULT_TYPE_CREATE_ENTRY


async def test_onboarding_not_supported.opp: OpenPeerPower) -> None:
    """Test setting up via onboarding with unsupported system."""
    with patch(MODULE, return_value=None):
        result = await.opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "onboarding"},
        )
    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "no_devices_found"
