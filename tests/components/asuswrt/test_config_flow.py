"""Tests for the AsusWrt config flow."""
from socket import gaierror
from unittest.mock import AsyncMock, Mock, patch

import pytest

from openpeerpower import data_entry_flow
from openpeerpower.components.asuswrt.const import (
    CONF_DNSMASQ,
    CONF_INTERFACE,
    CONF_REQUIRE_IP,
    CONF_SSH_KEY,
    CONF_TRACK_UNKNOWN,
    DOMAIN,
)
from openpeerpower.components.device_tracker.const import CONF_CONSIDER_HOME
from openpeerpower.config_entries import SOURCE_IMPORT, SOURCE_USER
from openpeerpower.const import (
    CONF_HOST,
    CONF_MODE,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_PROTOCOL,
    CONF_USERNAME,
)

from tests.common import MockConfigEntry

HOST = "myrouter.asuswrt.com"
IP_ADDRESS = "192.168.1.1"
SSH_KEY = "1234"

CONFIG_DATA = {
    CONF_HOST: HOST,
    CONF_PORT: 22,
    CONF_PROTOCOL: "telnet",
    CONF_USERNAME: "user",
    CONF_PASSWORD: "pwd",
    CONF_MODE: "ap",
}


@pytest.fixture(name="connect")
def mock_controller_connect():
    """Mock a successful connection."""
    with patch("openpeerpower.components.asuswrt.router.AsusWrt") as service_mock:
        service_mock.return_value.connection.async_connect = AsyncMock()
        service_mock.return_value.is_connected = True
        service_mock.return_value.connection.disconnect = Mock()
        yield service_mock


async def test_user(opp, connect):
    """Test user config."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    # test with all provided
    with patch(
        "openpeerpower.components.asuswrt.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry, patch(
        "openpeerpower.components.asuswrt.config_flow.socket.gethostbyname",
        return_value=IP_ADDRESS,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=CONFIG_DATA,
        )
        await opp.async_block_till_done()

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == HOST
        assert result["data"] == CONFIG_DATA

        assert len(mock_setup_entry.mock_calls) == 1


async def test_import(opp, connect):
    """Test import step."""
    with patch(
        "openpeerpower.components.asuswrt.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry, patch(
        "openpeerpower.components.asuswrt.config_flow.socket.gethostbyname",
        return_value=IP_ADDRESS,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=CONFIG_DATA,
        )
        await opp.async_block_till_done()

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == HOST
        assert result["data"] == CONFIG_DATA

        assert len(mock_setup_entry.mock_calls) == 1


async def test_import_ssh(opp, connect):
    """Test import step with ssh file."""
    config_data = CONFIG_DATA.copy()
    config_data.pop(CONF_PASSWORD)
    config_data[CONF_SSH_KEY] = SSH_KEY

    with patch(
        "openpeerpower.components.asuswrt.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry, patch(
        "openpeerpower.components.asuswrt.config_flow.socket.gethostbyname",
        return_value=IP_ADDRESS,
    ), patch(
        "openpeerpower.components.asuswrt.config_flow.os.path.isfile",
        return_value=True,
    ), patch(
        "openpeerpower.components.asuswrt.config_flow.os.access",
        return_value=True,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=config_data,
        )
        await opp.async_block_till_done()

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == HOST
        assert result["data"] == config_data

        assert len(mock_setup_entry.mock_calls) == 1


async def test_error_no_password_ssh(opp):
    """Test we abort if component is already setup."""
    config_data = CONFIG_DATA.copy()
    config_data.pop(CONF_PASSWORD)
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=config_data,
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {"base": "pwd_or_ssh"}


async def test_error_both_password_ssh(opp):
    """Test we abort if component is already setup."""
    config_data = CONFIG_DATA.copy()
    config_data[CONF_SSH_KEY] = SSH_KEY
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=config_data,
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {"base": "pwd_and_ssh"}


async def test_error_invalid_ssh(opp):
    """Test we abort if component is already setup."""
    config_data = CONFIG_DATA.copy()
    config_data.pop(CONF_PASSWORD)
    config_data[CONF_SSH_KEY] = SSH_KEY
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=config_data,
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {"base": "ssh_not_file"}


async def test_error_invalid_host(opp):
    """Test we abort if host name is invalid."""
    with patch(
        "openpeerpower.components.asuswrt.config_flow.socket.gethostbyname",
        side_effect=gaierror,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=CONFIG_DATA,
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["errors"] == {"base": "invalid_host"}


async def test_abort_if_already_setup(opp):
    """Test we abort if component is already setup."""
    MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG_DATA,
    ).add_to_opp(opp)

    with patch(
        "openpeerpower.components.asuswrt.config_flow.socket.gethostbyname",
        return_value=IP_ADDRESS,
    ):
        # Should fail, same HOST (flow)
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=CONFIG_DATA,
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
        assert result["reason"] == "single_instance_allowed"

        # Should fail, same HOST (import)
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=CONFIG_DATA,
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
        assert result["reason"] == "single_instance_allowed"


async def test_on_connect_failed(opp):
    """Test when we have errors connecting the router."""
    flow_result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    with patch("openpeerpower.components.asuswrt.router.AsusWrt") as asus_wrt:
        asus_wrt.return_value.connection.async_connect = AsyncMock()
        asus_wrt.return_value.is_connected = False
        result = await opp.config_entries.flow.async_configure(
            flow_result["flow_id"], user_input=CONFIG_DATA
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["errors"] == {"base": "cannot_connect"}

    with patch("openpeerpower.components.asuswrt.router.AsusWrt") as asus_wrt:
        asus_wrt.return_value.connection.async_connect = AsyncMock(side_effect=OSError)
        result = await opp.config_entries.flow.async_configure(
            flow_result["flow_id"], user_input=CONFIG_DATA
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["errors"] == {"base": "cannot_connect"}

    with patch("openpeerpower.components.asuswrt.router.AsusWrt") as asus_wrt:
        asus_wrt.return_value.connection.async_connect = AsyncMock(
            side_effect=TypeError
        )
        result = await opp.config_entries.flow.async_configure(
            flow_result["flow_id"], user_input=CONFIG_DATA
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["errors"] == {"base": "unknown"}


async def test_options_flow(opp):
    """Test config flow options."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG_DATA,
        options={CONF_REQUIRE_IP: True},
    )
    config_entry.add_to_opp(opp)

    with patch("openpeerpower.components.asuswrt.async_setup_entry", return_value=True):
        await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()
        result = await opp.config_entries.options.async_init(config_entry.entry_id)

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "init"

        result = await opp.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_CONSIDER_HOME: 20,
                CONF_TRACK_UNKNOWN: True,
                CONF_INTERFACE: "aaa",
                CONF_DNSMASQ: "bbb",
                CONF_REQUIRE_IP: False,
            },
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert config_entry.options[CONF_CONSIDER_HOME] == 20
        assert config_entry.options[CONF_TRACK_UNKNOWN] is True
        assert config_entry.options[CONF_INTERFACE] == "aaa"
        assert config_entry.options[CONF_DNSMASQ] == "bbb"
        assert config_entry.options[CONF_REQUIRE_IP] is False
