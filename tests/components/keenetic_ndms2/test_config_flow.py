"""Test Keenetic NDMS2 setup process."""

from unittest.mock import Mock, patch

from ndms2_client import ConnectionException
from ndms2_client.client import InterfaceInfo, RouterInfo
import pytest

from openpeerpower import config_entries, data_entry_flow
from openpeerpower.components import keenetic_ndms2 as keenetic
from openpeerpower.components.keenetic_ndms2 import const
from openpeerpower.helpers.typing import OpenPeerPowerType

from . import MOCK_DATA, MOCK_NAME, MOCK_OPTIONS

from tests.common import MockConfigEntry


@pytest.fixture(name="connect")
def mock_keenetic_connect():
    """Mock connection routine."""
    with patch("ndms2_client.client.Client.get_router_info") as mock_get_router_info:
        mock_get_router_info.return_value = RouterInfo(
            name=MOCK_NAME,
            fw_version="3.0.4",
            fw_channel="stable",
            model="mock",
            hw_version="0000",
            manufacturer="pytest",
            vendor="foxel",
            region="RU",
        )
        yield


@pytest.fixture(name="connect_error")
def mock_keenetic_connect_failed():
    """Mock connection routine."""
    with patch(
        "ndms2_client.client.Client.get_router_info",
        side_effect=ConnectionException("Mocked failure"),
    ):
        yield


async def test_flow_works.opp: OpenPeerPowerType, connect):
    """Test config flow."""

    result = await.opp.config_entries.flow.async_init(
        keenetic.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    with patch(
        "openpeerpower.components.keenetic_ndms2.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.keenetic_ndms2.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=MOCK_DATA,
        )
        await.opp.async_block_till_done()

    assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result2["title"] == MOCK_NAME
    assert result2["data"] == MOCK_DATA
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_import_works.opp: OpenPeerPowerType, connect):
    """Test config flow."""

    with patch(
        "openpeerpower.components.keenetic_ndms2.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.keenetic_ndms2.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result = await.opp.config_entries.flow.async_init(
            keenetic.DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=MOCK_DATA,
        )
        await.opp.async_block_till_done()

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == MOCK_NAME
    assert result["data"] == MOCK_DATA
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_options.opp):
    """Test updating options."""
    entry = MockConfigEntry(domain=keenetic.DOMAIN, data=MOCK_DATA)
    entry.add_to.opp.opp)
    with patch(
        "openpeerpower.components.keenetic_ndms2.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.keenetic_ndms2.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        await.opp.config_entries.async_setup(entry.entry_id)
        await.opp.async_block_till_done()

    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1

    # fake router
   .opp.data.setdefault(keenetic.DOMAIN, {})
   .opp.data[keenetic.DOMAIN][entry.entry_id] = {
        keenetic.ROUTER: Mock(
            client=Mock(
                get_interfaces=Mock(
                    return_value=[
                        InterfaceInfo.from_dict({"id": name, "type": "bridge"})
                        for name in MOCK_OPTIONS[const.CONF_INTERFACES]
                    ]
                )
            )
        )
    }

    result = await.opp.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result2 = await.opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input=MOCK_OPTIONS,
    )

    assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result2["data"] == MOCK_OPTIONS


async def test_host_already_configured.opp, connect):
    """Test host already configured."""

    entry = MockConfigEntry(
        domain=keenetic.DOMAIN, data=MOCK_DATA, options=MOCK_OPTIONS
    )
    entry.add_to.opp.opp)

    result = await.opp.config_entries.flow.async_init(
        keenetic.DOMAIN, context={"source": "user"}
    )

    result2 = await.opp.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_DATA
    )

    assert result2["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result2["reason"] == "already_configured"


async def test_connection_error.opp, connect_error):
    """Test error when connection is unsuccessful."""

    result = await.opp.config_entries.flow.async_init(
        keenetic.DOMAIN, context={"source": "user"}
    )
    result = await.opp.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_DATA
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {"base": "cannot_connect"}
