"""Tests for the GogoGate2 component."""
from unittest.mock import MagicMock, patch

from ismartgate import GogoGate2Api, ISmartGateApi
from ismartgate.common import ApiError
from ismartgate.const import GogoGate2ApiErrorCode

from openpeerpower import config_entries, setup
from openpeerpower.components.gogogate2.const import (
    DEVICE_TYPE_GOGOGATE2,
    DEVICE_TYPE_ISMARTGATE,
    DOMAIN,
)
from openpeerpower.config_entries import SOURCE_USER
from openpeerpower.const import (
    CONF_DEVICE,
    CONF_IP_ADDRESS,
    CONF_PASSWORD,
    CONF_USERNAME,
)
from openpeerpower.core import OpenPeerPower
from openpeerpower.data_entry_flow import (
    RESULT_TYPE_ABORT,
    RESULT_TYPE_CREATE_ENTRY,
    RESULT_TYPE_FORM,
)

from . import _mocked_ismartgate_closed_door_response

from tests.common import MockConfigEntry

MOCK_MAC_ADDR = "AA:BB:CC:DD:EE:FF"


@patch("openpeerpower.components.gogogate2.async_setup_entry", return_value=True)
@patch("openpeerpower.components.gogogate2.common.GogoGate2Api")
async def test_auth_fail(
    gogogate2api_mock, async_setup_entry_mock, opp: OpenPeerPower
) -> None:
    """Test authorization failures."""
    api: GogoGate2Api = MagicMock(spec=GogoGate2Api)
    gogogate2api_mock.return_value = api

    api.reset_mock()
    api.async_info.side_effect = ApiError(
        GogoGate2ApiErrorCode.CREDENTIALS_INCORRECT, "blah"
    )
    result = await opp.config_entries.flow.async_init(
        "gogogate2", context={"source": SOURCE_USER}
    )
    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DEVICE: DEVICE_TYPE_GOGOGATE2,
            CONF_IP_ADDRESS: "127.0.0.2",
            CONF_USERNAME: "user0",
            CONF_PASSWORD: "password0",
        },
    )
    assert result
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {
        "base": "invalid_auth",
    }

    api.reset_mock()
    api.async_info.side_effect = Exception("Generic connection error.")
    result = await opp.config_entries.flow.async_init(
        "gogogate2", context={"source": SOURCE_USER}
    )
    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DEVICE: DEVICE_TYPE_GOGOGATE2,
            CONF_IP_ADDRESS: "127.0.0.2",
            CONF_USERNAME: "user0",
            CONF_PASSWORD: "password0",
        },
    )
    assert result
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {"base": "cannot_connect"}

    api.reset_mock()
    api.async_info.side_effect = ApiError(0, "blah")
    result = await opp.config_entries.flow.async_init(
        "gogogate2", context={"source": SOURCE_USER}
    )
    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DEVICE: DEVICE_TYPE_GOGOGATE2,
            CONF_IP_ADDRESS: "127.0.0.2",
            CONF_USERNAME: "user0",
            CONF_PASSWORD: "password0",
        },
    )
    assert result
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_form_homekit_unique_id_already_setup(opp):
    """Test that we abort from homekit if gogogate2 is already setup."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_HOMEKIT},
        data={"host": "1.2.3.4", "properties": {"id": MOCK_MAC_ADDR}},
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {}
    flow = next(
        flow
        for flow in opp.config_entries.flow.async_progress()
        if flow["flow_id"] == result["flow_id"]
    )
    assert flow["context"]["unique_id"] == MOCK_MAC_ADDR

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_IP_ADDRESS: "1.2.3.4", CONF_USERNAME: "mock", CONF_PASSWORD: "mock"},
    )
    entry.add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_HOMEKIT},
        data={"host": "1.2.3.4", "properties": {"id": MOCK_MAC_ADDR}},
    )
    assert result["type"] == RESULT_TYPE_ABORT


async def test_form_homekit_ip_address_already_setup(opp):
    """Test that we abort from homekit if gogogate2 is already setup."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_IP_ADDRESS: "1.2.3.4", CONF_USERNAME: "mock", CONF_PASSWORD: "mock"},
    )
    entry.add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_HOMEKIT},
        data={"host": "1.2.3.4", "properties": {"id": MOCK_MAC_ADDR}},
    )
    assert result["type"] == RESULT_TYPE_ABORT


async def test_form_homekit_ip_address(opp):
    """Test homekit includes the defaults ip address."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_HOMEKIT},
        data={"host": "1.2.3.4", "properties": {"id": MOCK_MAC_ADDR}},
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {}

    data_schema = result["data_schema"]
    assert data_schema({CONF_USERNAME: "username", CONF_PASSWORD: "password"}) == {
        CONF_DEVICE: DEVICE_TYPE_ISMARTGATE,
        CONF_IP_ADDRESS: "1.2.3.4",
        CONF_PASSWORD: "password",
        CONF_USERNAME: "username",
    }


@patch("openpeerpower.components.gogogate2.async_setup_entry", return_value=True)
@patch("openpeerpower.components.gogogate2.common.ISmartGateApi")
async def test_discovered_dhcp(ismartgateapi_mock, async_setup_entry_mock, opp) -> None:
    """Test we get the form with homekit and abort for dhcp source when we get both."""
    api: ISmartGateApi = MagicMock(spec=ISmartGateApi)
    ismartgateapi_mock.return_value = api

    api.reset_mock()
    await setup.async_setup_component(opp, "persistent_notification", {})

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data={"ip": "1.2.3.4", "macaddress": MOCK_MAC_ADDR},
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {}
    result2 = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_DEVICE: DEVICE_TYPE_ISMARTGATE,
            CONF_IP_ADDRESS: "1.2.3.4",
            CONF_USERNAME: "user0",
            CONF_PASSWORD: "password0",
        },
    )
    assert result2
    assert result2["type"] == RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "cannot_connect"}
    api.reset_mock()

    closed_door_response = _mocked_ismartgate_closed_door_response()
    api.async_info.return_value = closed_door_response
    result3 = await opp.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={
            CONF_DEVICE: DEVICE_TYPE_ISMARTGATE,
            CONF_IP_ADDRESS: "1.2.3.4",
            CONF_USERNAME: "user0",
            CONF_PASSWORD: "password0",
        },
    )
    assert result3
    assert result3["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result3["data"] == {
        "device": "ismartgate",
        "ip_address": "1.2.3.4",
        "password": "password0",
        "username": "user0",
    }


async def test_discovered_by_homekit_and_dhcp(opp):
    """Test we get the form with homekit and abort for dhcp source when we get both."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_HOMEKIT},
        data={"host": "1.2.3.4", "properties": {"id": MOCK_MAC_ADDR}},
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {}

    result2 = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data={"ip": "1.2.3.4", "macaddress": MOCK_MAC_ADDR},
    )
    assert result2["type"] == RESULT_TYPE_ABORT
    assert result2["reason"] == "already_in_progress"

    result3 = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data={"ip": "1.2.3.4", "macaddress": "00:00:00:00:00:00"},
    )
    assert result3["type"] == RESULT_TYPE_ABORT
    assert result3["reason"] == "already_in_progress"
