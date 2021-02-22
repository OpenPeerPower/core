"""Tests for Islamic Prayer Times config flow."""
from unittest.mock import patch

import pytest

from openpeerpower import data_entry_flow
from openpeerpower.components import islamic_prayer_times
from openpeerpower.components.islamic_prayer_times.const import CONF_CALC_METHOD, DOMAIN

from tests.common import MockConfigEntry


@pytest.fixture(name="mock_setup", autouse=True)
def mock_setup():
    """Mock entry setup."""
    with patch(
        "openpeerpower.components.islamic_prayer_times.async_setup_entry",
        return_value=True,
    ):
        yield


async def test_flow_works.opp):
    """Test user config."""
    result = await opp.config_entries.flow.async_init(
        islamic_prayer_times.DOMAIN, context={"source": "user"}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "Islamic Prayer Times"


async def test_options.opp):
    """Test updating options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Islamic Prayer Times",
        data={},
        options={CONF_CALC_METHOD: "isna"},
    )
    entry.add_to.opp.opp)

    result = await opp.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    result = await opp.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_CALC_METHOD: "makkah"}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["data"][CONF_CALC_METHOD] == "makkah"


async def test_import.opp):
    """Test import step."""
    result = await opp.config_entries.flow.async_init(
        islamic_prayer_times.DOMAIN,
        context={"source": "import"},
        data={CONF_CALC_METHOD: "makkah"},
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "Islamic Prayer Times"
    assert result["data"][CONF_CALC_METHOD] == "makkah"


async def test_integration_already_configured.opp):
    """Test integration is already configured."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={},
    )
    entry.add_to.opp.opp)
    result = await opp.config_entries.flow.async_init(
        islamic_prayer_times.DOMAIN, context={"source": "user"}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "single_instance_allowed"
