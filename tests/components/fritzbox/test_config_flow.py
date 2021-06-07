"""Tests for AVM Fritz!Box config flow."""
from unittest import mock
from unittest.mock import Mock, patch

from pyfritzhome import LoginError
import pytest
from requests.exceptions import HTTPError

from openpeerpower.components.fritzbox.const import DOMAIN
from openpeerpower.components.ssdp import (
    ATTR_SSDP_LOCATION,
    ATTR_UPNP_FRIENDLY_NAME,
    ATTR_UPNP_UDN,
)
from openpeerpower.config_entries import SOURCE_REAUTH, SOURCE_SSDP, SOURCE_USER
from openpeerpower.const import CONF_DEVICES, CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from openpeerpower.core import OpenPeerPower
from openpeerpower.data_entry_flow import (
    RESULT_TYPE_ABORT,
    RESULT_TYPE_CREATE_ENTRY,
    RESULT_TYPE_FORM,
)

from . import MOCK_CONFIG

from tests.common import MockConfigEntry

MOCK_USER_DATA = MOCK_CONFIG[DOMAIN][CONF_DEVICES][0]
MOCK_SSDP_DATA = {
    ATTR_SSDP_LOCATION: "https://fake_host:12345/test",
    ATTR_UPNP_FRIENDLY_NAME: "fake_name",
    ATTR_UPNP_UDN: "uuid:only-a-test",
}


@pytest.fixture(name="fritz")
def fritz_fixture() -> Mock:
    """Patch libraries."""
    with patch("openpeerpower.components.fritzbox.config_flow.Fritzhome") as fritz:
        yield fritz


async def test_user(opp: OpenPeerPower, fritz: Mock):
    """Test starting a flow by user."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_USER_DATA
    )
    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "fake_host"
    assert result["data"][CONF_HOST] == "fake_host"
    assert result["data"][CONF_PASSWORD] == "fake_pass"
    assert result["data"][CONF_USERNAME] == "fake_user"
    assert not result["result"].unique_id


async def test_user_auth_failed(opp: OpenPeerPower, fritz: Mock):
    """Test starting a flow by user with authentication failure."""
    fritz().login.side_effect = [LoginError("Boom"), mock.DEFAULT]

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=MOCK_USER_DATA
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"]["base"] == "invalid_auth"


async def test_user_not_successful(opp: OpenPeerPower, fritz: Mock):
    """Test starting a flow by user but no connection found."""
    fritz().login.side_effect = OSError("Boom")

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=MOCK_USER_DATA
    )
    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "no_devices_found"


async def test_user_already_configured(opp: OpenPeerPower, fritz: Mock):
    """Test starting a flow by user when already configured."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=MOCK_USER_DATA
    )
    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert not result["result"].unique_id

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=MOCK_USER_DATA
    )
    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_reauth_success(opp: OpenPeerPower, fritz: Mock):
    """Test starting a reauthentication flow."""
    mock_config = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_DATA)
    mock_config.add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_REAUTH, "entry_id": mock_config.entry_id},
        data=mock_config.data,
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "reauth_confirm"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: "other_fake_user",
            CONF_PASSWORD: "other_fake_password",
        },
    )

    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config.data[CONF_USERNAME] == "other_fake_user"
    assert mock_config.data[CONF_PASSWORD] == "other_fake_password"


async def test_reauth_auth_failed(opp: OpenPeerPower, fritz: Mock):
    """Test starting a reauthentication flow with authentication failure."""
    fritz().login.side_effect = LoginError("Boom")

    mock_config = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_DATA)
    mock_config.add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_REAUTH, "entry_id": mock_config.entry_id},
        data=mock_config.data,
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "reauth_confirm"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: "other_fake_user",
            CONF_PASSWORD: "other_fake_password",
        },
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"]["base"] == "invalid_auth"


async def test_reauth_not_successful(opp: OpenPeerPower, fritz: Mock):
    """Test starting a reauthentication flow but no connection found."""
    fritz().login.side_effect = OSError("Boom")

    mock_config = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_DATA)
    mock_config.add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_REAUTH, "entry_id": mock_config.entry_id},
        data=mock_config.data,
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "reauth_confirm"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: "other_fake_user",
            CONF_PASSWORD: "other_fake_password",
        },
    )

    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "no_devices_found"


async def test_ssdp(opp: OpenPeerPower, fritz: Mock):
    """Test starting a flow from discovery."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=MOCK_SSDP_DATA
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "confirm"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "fake_pass", CONF_USERNAME: "fake_user"},
    )
    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "fake_name"
    assert result["data"][CONF_HOST] == "fake_host"
    assert result["data"][CONF_PASSWORD] == "fake_pass"
    assert result["data"][CONF_USERNAME] == "fake_user"
    assert result["result"].unique_id == "only-a-test"


async def test_ssdp_no_friendly_name(opp: OpenPeerPower, fritz: Mock):
    """Test starting a flow from discovery without friendly name."""
    MOCK_NO_NAME = MOCK_SSDP_DATA.copy()
    del MOCK_NO_NAME[ATTR_UPNP_FRIENDLY_NAME]
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=MOCK_NO_NAME
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "confirm"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "fake_pass", CONF_USERNAME: "fake_user"},
    )
    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "fake_host"
    assert result["data"][CONF_HOST] == "fake_host"
    assert result["data"][CONF_PASSWORD] == "fake_pass"
    assert result["data"][CONF_USERNAME] == "fake_user"
    assert result["result"].unique_id == "only-a-test"


async def test_ssdp_auth_failed(opp: OpenPeerPower, fritz: Mock):
    """Test starting a flow from discovery with authentication failure."""
    fritz().login.side_effect = LoginError("Boom")

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=MOCK_SSDP_DATA
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "confirm"
    assert result["errors"] == {}

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "whatever", CONF_USERNAME: "whatever"},
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "confirm"
    assert result["errors"]["base"] == "invalid_auth"


async def test_ssdp_not_successful(opp: OpenPeerPower, fritz: Mock):
    """Test starting a flow from discovery but no device found."""
    fritz().login.side_effect = OSError("Boom")

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=MOCK_SSDP_DATA
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "confirm"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "whatever", CONF_USERNAME: "whatever"},
    )
    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "no_devices_found"


async def test_ssdp_not_supported(opp: OpenPeerPower, fritz: Mock):
    """Test starting a flow from discovery with unsupported device."""
    fritz().get_device_elements.side_effect = HTTPError("Boom")

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=MOCK_SSDP_DATA
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "confirm"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "whatever", CONF_USERNAME: "whatever"},
    )
    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "not_supported"


async def test_ssdp_already_in_progress_unique_id(opp: OpenPeerPower, fritz: Mock):
    """Test starting a flow from discovery twice."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=MOCK_SSDP_DATA
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "confirm"

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=MOCK_SSDP_DATA
    )
    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "already_in_progress"


async def test_ssdp_already_in_progress_host(opp: OpenPeerPower, fritz: Mock):
    """Test starting a flow from discovery twice."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=MOCK_SSDP_DATA
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "confirm"

    MOCK_NO_UNIQUE_ID = MOCK_SSDP_DATA.copy()
    del MOCK_NO_UNIQUE_ID[ATTR_UPNP_UDN]
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=MOCK_NO_UNIQUE_ID
    )
    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "already_in_progress"


async def test_ssdp_already_configured(opp: OpenPeerPower, fritz: Mock):
    """Test starting a flow from discovery when already configured."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=MOCK_USER_DATA
    )
    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert not result["result"].unique_id

    result2 = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=MOCK_SSDP_DATA
    )
    assert result2["type"] == RESULT_TYPE_ABORT
    assert result2["reason"] == "already_configured"
    assert result["result"].unique_id == "only-a-test"
