"""Test Keenetic NDMS2 setup process."""

from unittest.mock import Mock, patch

from ndms2_client import ConnectionException
from ndms2_client.client import InterfaceInfo, RouterInfo
import pytest

from openpeerpower import config_entries, data_entry_flow
from openpeerpower.components import keenetic_ndms2 as keenetic, ssdp
from openpeerpower.components.keenetic_ndms2 import const
from openpeerpower.const import CONF_HOST, CONF_SOURCE
from openpeerpower.core import OpenPeerPower

from . import MOCK_DATA, MOCK_NAME, MOCK_OPTIONS, MOCK_SSDP_DISCOVERY_INFO

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


async def test_flow_works(opp: OpenPeerPower, connect) -> None:
    """Test config flow."""

    result = await opp.config_entries.flow.async_init(
        keenetic.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    with patch(
        "openpeerpower.components.keenetic_ndms2.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=MOCK_DATA,
        )
        await opp.async_block_till_done()

    assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result2["title"] == MOCK_NAME
    assert result2["data"] == MOCK_DATA
    assert len(mock_setup_entry.mock_calls) == 1


async def test_import_works(opp: OpenPeerPower, connect) -> None:
    """Test config flow."""

    with patch(
        "openpeerpower.components.keenetic_ndms2.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result = await opp.config_entries.flow.async_init(
            keenetic.DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=MOCK_DATA,
        )
        await opp.async_block_till_done()

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == MOCK_NAME
    assert result["data"] == MOCK_DATA
    assert len(mock_setup_entry.mock_calls) == 1


async def test_options(opp: OpenPeerPower) -> None:
    """Test updating options."""
    entry = MockConfigEntry(domain=keenetic.DOMAIN, data=MOCK_DATA)
    entry.add_to_opp(opp)
    with patch(
        "openpeerpower.components.keenetic_ndms2.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()

    assert len(mock_setup_entry.mock_calls) == 1

    # fake router
    opp.data.setdefault(keenetic.DOMAIN, {})
    opp.data[keenetic.DOMAIN][entry.entry_id] = {
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

    result = await opp.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result2 = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input=MOCK_OPTIONS,
    )

    assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result2["data"] == MOCK_OPTIONS


async def test_host_already_configured(opp: OpenPeerPower, connect) -> None:
    """Test host already configured."""

    entry = MockConfigEntry(
        domain=keenetic.DOMAIN, data=MOCK_DATA, options=MOCK_OPTIONS
    )
    entry.add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        keenetic.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_DATA
    )

    assert result2["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result2["reason"] == "already_configured"


async def test_connection_error(opp: OpenPeerPower, connect_error) -> None:
    """Test error when connection is unsuccessful."""

    result = await opp.config_entries.flow.async_init(
        keenetic.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_DATA
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_ssdp_works(opp: OpenPeerPower, connect) -> None:
    """Test host already configured and discovered."""

    discovery_info = MOCK_SSDP_DISCOVERY_INFO.copy()
    result = await opp.config_entries.flow.async_init(
        keenetic.DOMAIN,
        context={CONF_SOURCE: config_entries.SOURCE_SSDP},
        data=discovery_info,
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    with patch(
        "openpeerpower.components.keenetic_ndms2.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        user_input = MOCK_DATA.copy()
        user_input.pop(CONF_HOST)

        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=user_input,
        )
        await opp.async_block_till_done()

    assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result2["title"] == MOCK_NAME
    assert result2["data"] == MOCK_DATA
    assert len(mock_setup_entry.mock_calls) == 1


async def test_ssdp_already_configured(opp: OpenPeerPower) -> None:
    """Test host already configured and discovered."""

    entry = MockConfigEntry(
        domain=keenetic.DOMAIN, data=MOCK_DATA, options=MOCK_OPTIONS
    )
    entry.add_to_opp(opp)

    discovery_info = MOCK_SSDP_DISCOVERY_INFO.copy()
    result = await opp.config_entries.flow.async_init(
        keenetic.DOMAIN,
        context={CONF_SOURCE: config_entries.SOURCE_SSDP},
        data=discovery_info,
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_ssdp_reject_no_udn(opp: OpenPeerPower) -> None:
    """Discovered device has no UDN."""

    discovery_info = {
        **MOCK_SSDP_DISCOVERY_INFO,
    }
    discovery_info.pop(ssdp.ATTR_UPNP_UDN)

    result = await opp.config_entries.flow.async_init(
        keenetic.DOMAIN,
        context={CONF_SOURCE: config_entries.SOURCE_SSDP},
        data=discovery_info,
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "no_udn"


async def test_ssdp_reject_non_keenetic(opp: OpenPeerPower) -> None:
    """Discovered device does not look like a keenetic router."""

    discovery_info = {
        **MOCK_SSDP_DISCOVERY_INFO,
        ssdp.ATTR_UPNP_FRIENDLY_NAME: "Suspicious device",
    }
    result = await opp.config_entries.flow.async_init(
        keenetic.DOMAIN,
        context={CONF_SOURCE: config_entries.SOURCE_SSDP},
        data=discovery_info,
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "not_keenetic_ndms2"
