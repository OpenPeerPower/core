"""Tests for SpeedTest config flow."""
from datetime import timedelta
from unittest.mock import patch

import pytest
from speedtest import NoMatchedServers

from openpeerpower import data_entry_flow
from openpeerpower.components import speedtestdotnet
from openpeerpower.components.speedtestdotnet.const import (
    CONF_MANUAL,
    CONF_SERVER_ID,
    CONF_SERVER_NAME,
    DOMAIN,
    SENSOR_TYPES,
)
from openpeerpower.const import CONF_MONITORED_CONDITIONS, CONF_SCAN_INTERVAL

from . import MOCK_SERVERS

from tests.common import MockConfigEntry


@pytest.fixture(name="mock_setup")
def mock_setup():
    """Mock entry setup."""
    with patch(
        "openpeerpower.components.speedtestdotnet.async_setup_entry",
        return_value=True,
    ):
        yield


async def test_flow_works(opp, mock_setup):
    """Test user config."""
    result = await opp.config_entries.flow.async_init(
        speedtestdotnet.DOMAIN, context={"source": "user"}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "SpeedTest"


async def test_import_fails(opp, mock_setup):
    """Test import step fails if server_id is not valid."""

    with patch("speedtest.Speedtest") as mock_api:
        mock_api.return_value.get_servers.side_effect = NoMatchedServers
        result = await opp.config_entries.flow.async_init(
            speedtestdotnet.DOMAIN,
            context={"source": "import"},
            data={
                CONF_SERVER_ID: "223",
                CONF_MANUAL: True,
                CONF_SCAN_INTERVAL: timedelta(minutes=1),
                CONF_MONITORED_CONDITIONS: list(SENSOR_TYPES),
            },
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
        assert result["reason"] == "wrong_server_id"


async def test_import_success(opp, mock_setup):
    """Test import step is successful if server_id is valid."""

    with patch("speedtest.Speedtest"):
        result = await opp.config_entries.flow.async_init(
            speedtestdotnet.DOMAIN,
            context={"source": "import"},
            data={
                CONF_SERVER_ID: "1",
                CONF_MANUAL: True,
                CONF_SCAN_INTERVAL: timedelta(minutes=1),
                CONF_MONITORED_CONDITIONS: list(SENSOR_TYPES),
            },
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == "SpeedTest"
        assert result["data"][CONF_SERVER_ID] == "1"
        assert result["data"][CONF_MANUAL] is True
        assert result["data"][CONF_SCAN_INTERVAL] == 1


async def test_options(opp):
    """Test updating options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="SpeedTest",
        data={},
        options={},
    )
    entry.add_to_opp(opp)

    with patch("speedtest.Speedtest") as mock_api:
        mock_api.return_value.get_servers.return_value = MOCK_SERVERS
        await opp.config_entries.async_setup(entry.entry_id)

        result = await opp.config_entries.options.async_init(entry.entry_id)
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "init"

        result = await opp.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_SERVER_NAME: "Country1 - Sponsor1 - Server1",
                CONF_SCAN_INTERVAL: 30,
                CONF_MANUAL: False,
            },
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["data"] == {
            CONF_SERVER_NAME: "Country1 - Sponsor1 - Server1",
            CONF_SERVER_ID: "1",
            CONF_SCAN_INTERVAL: 30,
            CONF_MANUAL: False,
        }


async def test_integration_already_configured(opp):
    """Test integration is already configured."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={},
    )
    entry.add_to_opp(opp)
    result = await opp.config_entries.flow.async_init(
        speedtestdotnet.DOMAIN, context={"source": "user"}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "single_instance_allowed"
