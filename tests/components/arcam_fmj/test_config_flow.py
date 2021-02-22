"""Tests for the Arcam FMJ config flow module."""

from unittest.mock import AsyncMock, patch

from arcam.fmj.client import ConnectionFailed
import pytest

from openpeerpower import data_entry_flow
from openpeerpower.components import ssdp
from openpeerpower.components.arcam_fmj.config_flow import get_entry_client
from openpeerpower.components.arcam_fmj.const import DOMAIN, DOMAIN_DATA_ENTRIES
from openpeerpower.config_entries import SOURCE_SSDP, SOURCE_USER
from openpeerpower.const import CONF_HOST, CONF_PORT, CONF_SOURCE

from .conftest import (
    MOCK_CONFIG_ENTRY,
    MOCK_HOST,
    MOCK_NAME,
    MOCK_PORT,
    MOCK_UDN,
    MOCK_UUID,
)

from tests.common import MockConfigEntry

MOCK_UPNP_DEVICE = f"""
<root xmlns="urn:schemas-upnp-org:device-1-0">
  <device>
    <UDN>{MOCK_UDN}</UDN>
  </device>
</root>
"""

MOCK_UPNP_LOCATION = f"http://{MOCK_HOST}:8080/dd.xml"

MOCK_DISCOVER = {
    ssdp.ATTR_UPNP_MANUFACTURER: "ARCAM",
    ssdp.ATTR_UPNP_MODEL_NAME: " ",
    ssdp.ATTR_UPNP_MODEL_NUMBER: "AVR450, AVR750",
    ssdp.ATTR_UPNP_FRIENDLY_NAME: f"Arcam media client {MOCK_UUID}",
    ssdp.ATTR_UPNP_SERIAL: "12343",
    ssdp.ATTR_SSDP_LOCATION: f"http://{MOCK_HOST}:8080/dd.xml",
    ssdp.ATTR_UPNP_UDN: MOCK_UDN,
    ssdp.ATTR_UPNP_DEVICE_TYPE: "urn:schemas-upnp-org:device:MediaRenderer:1",
}


@pytest.fixture(name="dummy_client", autouse=True)
def dummy_client_fixture.opp):
    """Mock out the real client."""
    with patch("openpeerpower.components.arcam_fmj.config_flow.Client") as client:
        client.return_value.start.side_effect = AsyncMock(return_value=None)
        client.return_value.stop.side_effect = AsyncMock(return_value=None)
        yield client.return_value


async def test_ssdp.opp, dummy_client):
    """Test a ssdp import flow."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_SSDP},
        data=MOCK_DISCOVER,
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "confirm"

    result = await opp.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == f"Arcam FMJ ({MOCK_HOST})"
    assert result["data"] == MOCK_CONFIG_ENTRY


async def test_ssdp_abort.opp):
    """Test a ssdp import flow."""
    entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_ENTRY, title=MOCK_NAME, unique_id=MOCK_UUID
    )
    entry.add_to.opp.opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_SSDP},
        data=MOCK_DISCOVER,
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_ssdp_unable_to_connect.opp, dummy_client):
    """Test a ssdp import flow."""
    dummy_client.start.side_effect = AsyncMock(side_effect=ConnectionFailed)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_SSDP},
        data=MOCK_DISCOVER,
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "confirm"

    result = await opp.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "cannot_connect"


async def test_ssdp_update.opp):
    """Test a ssdp import flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "old_host", CONF_PORT: MOCK_PORT},
        title=MOCK_NAME,
        unique_id=MOCK_UUID,
    )
    entry.add_to.opp.opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_SSDP},
        data=MOCK_DISCOVER,
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"

    assert entry.data[CONF_HOST] == MOCK_HOST


async def test_user.opp, aioclient_mock):
    """Test a manual user configuration flow."""

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data=None,
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    user_input = {
        CONF_HOST: MOCK_HOST,
        CONF_PORT: MOCK_PORT,
    }

    aioclient_mock.get(MOCK_UPNP_LOCATION, text=MOCK_UPNP_DEVICE)
    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == f"Arcam FMJ ({MOCK_HOST})"
    assert result["data"] == MOCK_CONFIG_ENTRY
    assert result["result"].unique_id == MOCK_UUID


async def test_invalid_ssdp.opp, aioclient_mock):
    """Test a a config flow where ssdp fails."""
    user_input = {
        CONF_HOST: MOCK_HOST,
        CONF_PORT: MOCK_PORT,
    }

    aioclient_mock.get(MOCK_UPNP_LOCATION, text="")
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data=user_input,
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == f"Arcam FMJ ({MOCK_HOST})"
    assert result["data"] == MOCK_CONFIG_ENTRY
    assert result["result"].unique_id is None


async def test_user_wrong.opp, aioclient_mock):
    """Test a manual user configuration flow with no ssdp response."""
    user_input = {
        CONF_HOST: MOCK_HOST,
        CONF_PORT: MOCK_PORT,
    }

    aioclient_mock.get(MOCK_UPNP_LOCATION, status=404)
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data=user_input,
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == f"Arcam FMJ ({MOCK_HOST})"
    assert result["result"].unique_id is None


async def test_get_entry_client.opp):
    """Test helper for configuration."""
    entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_ENTRY, title=MOCK_NAME, unique_id=MOCK_UUID
    )
    opp.data[DOMAIN_DATA_ENTRIES] = {entry.entry_id: "dummy"}
    assert get_entry_client.opp, entry) == "dummy"
