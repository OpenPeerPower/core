"""Tests for Samsung TV config flow."""
import socket
from unittest.mock import Mock, PropertyMock, call, patch

from samsungctl.exceptions import AccessDenied, UnhandledResponse
from samsungtvws.exceptions import ConnectionFailure
from websocket import WebSocketException, WebSocketProtocolException

from openpeerpower import config_entries
from openpeerpower.components.dhcp import IP_ADDRESS, MAC_ADDRESS
from openpeerpower.components.samsungtv.const import (
    ATTR_PROPERTIES,
    CONF_MANUFACTURER,
    CONF_MODEL,
    DEFAULT_MANUFACTURER,
    DOMAIN,
    METHOD_LEGACY,
    METHOD_WEBSOCKET,
    RESULT_AUTH_MISSING,
    RESULT_CANNOT_CONNECT,
    RESULT_NOT_SUPPORTED,
    RESULT_UNKNOWN_HOST,
    TIMEOUT_REQUEST,
    TIMEOUT_WEBSOCKET,
)
from openpeerpower.components.ssdp import (
    ATTR_SSDP_LOCATION,
    ATTR_UPNP_FRIENDLY_NAME,
    ATTR_UPNP_MANUFACTURER,
    ATTR_UPNP_MODEL_NAME,
    ATTR_UPNP_UDN,
)
from openpeerpower.const import (
    CONF_HOST,
    CONF_ID,
    CONF_IP_ADDRESS,
    CONF_MAC,
    CONF_METHOD,
    CONF_NAME,
    CONF_PORT,
    CONF_TOKEN,
)
from openpeerpower.core import OpenPeerPower
from openpeerpower.setup import async_setup_component

from tests.common import MockConfigEntry
from tests.components.samsungtv.conftest import (
    RESULT_ALREADY_CONFIGURED,
    RESULT_ALREADY_IN_PROGRESS,
)

MOCK_IMPORT_DATA = {
    CONF_HOST: "fake_host",
    CONF_NAME: "fake",
    CONF_PORT: 55000,
}
MOCK_IMPORT_DATA_WITHOUT_NAME = {
    CONF_HOST: "fake_host",
}
MOCK_IMPORT_WSDATA = {
    CONF_HOST: "fake_host",
    CONF_NAME: "fake",
    CONF_PORT: 8002,
}
MOCK_USER_DATA = {CONF_HOST: "fake_host", CONF_NAME: "fake_name"}
MOCK_SSDP_DATA = {
    ATTR_SSDP_LOCATION: "https://fake_host:12345/test",
    ATTR_UPNP_FRIENDLY_NAME: "[TV] fake_name",
    ATTR_UPNP_MANUFACTURER: "Samsung fake_manufacturer",
    ATTR_UPNP_MODEL_NAME: "fake_model",
    ATTR_UPNP_UDN: "uuid:0d1cef00-00dc-1000-9c80-4844f7b172de",
}
MOCK_SSDP_DATA_NOPREFIX = {
    ATTR_SSDP_LOCATION: "http://fake2_host:12345/test",
    ATTR_UPNP_FRIENDLY_NAME: "fake2_name",
    ATTR_UPNP_MANUFACTURER: "Samsung fake2_manufacturer",
    ATTR_UPNP_MODEL_NAME: "fake2_model",
    ATTR_UPNP_UDN: "uuid:0d1cef00-00dc-1000-9c80-4844f7b172df",
}
MOCK_SSDP_DATA_WRONGMODEL = {
    ATTR_SSDP_LOCATION: "http://fake2_host:12345/test",
    ATTR_UPNP_FRIENDLY_NAME: "fake2_name",
    ATTR_UPNP_MANUFACTURER: "fake2_manufacturer",
    ATTR_UPNP_MODEL_NAME: "HW-Qfake",
    ATTR_UPNP_UDN: "uuid:0d1cef00-00dc-1000-9c80-4844f7b172df",
}
MOCK_DHCP_DATA = {IP_ADDRESS: "fake_host", MAC_ADDRESS: "aa:bb:cc:dd:ee:ff"}
MOCK_ZEROCONF_DATA = {
    CONF_HOST: "fake_host",
    CONF_PORT: 1234,
    ATTR_PROPERTIES: {
        "deviceid": "aa:bb:cc:dd:ee:ff",
        "manufacturer": "fake_manufacturer",
        "model": "fake_model",
        "serialNumber": "fake_serial",
    },
}
MOCK_OLD_ENTRY = {
    CONF_HOST: "fake_host",
    CONF_ID: "0d1cef00-00dc-1000-9c80-4844f7b172de_old",
    CONF_IP_ADDRESS: "fake_ip_old",
    CONF_METHOD: "legacy",
    CONF_PORT: None,
}
MOCK_WS_ENTRY = {
    CONF_HOST: "fake_host",
    CONF_METHOD: METHOD_WEBSOCKET,
    CONF_PORT: 8002,
    CONF_MODEL: "any",
    CONF_NAME: "any",
}

AUTODETECT_LEGACY = {
    "name": "OpenPeerPower",
    "description": "OpenPeerPower",
    "id": "ha.component.samsung",
    "method": "legacy",
    "port": None,
    "host": "fake_host",
    "timeout": TIMEOUT_REQUEST,
}
AUTODETECT_WEBSOCKET_PLAIN = {
    "host": "fake_host",
    "name": "OpenPeerPower",
    "port": 8001,
    "timeout": TIMEOUT_REQUEST,
    "token": None,
}
AUTODETECT_WEBSOCKET_SSL = {
    "host": "fake_host",
    "name": "OpenPeerPower",
    "port": 8002,
    "timeout": TIMEOUT_REQUEST,
    "token": None,
}
DEVICEINFO_WEBSOCKET_SSL = {
    "host": "fake_host",
    "name": "OpenPeerPower",
    "port": 8002,
    "timeout": TIMEOUT_WEBSOCKET,
    "token": "123456789",
}


async def test_user_legacy(opp: OpenPeerPower, remote: Mock):
    """Test starting a flow by user."""
    # show form
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "user"

    # entry was added
    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_USER_DATA
    )
    # legacy tv entry created
    assert result["type"] == "create_entry"
    assert result["title"] == "fake_name"
    assert result["data"][CONF_HOST] == "fake_host"
    assert result["data"][CONF_NAME] == "fake_name"
    assert result["data"][CONF_METHOD] == "legacy"
    assert result["data"][CONF_MANUFACTURER] == DEFAULT_MANUFACTURER
    assert result["data"][CONF_MODEL] is None
    assert result["result"].unique_id is None


async def test_user_websocket(opp: OpenPeerPower, remotews: Mock):
    """Test starting a flow by user."""
    with patch(
        "openpeerpower.components.samsungtv.bridge.Remote", side_effect=OSError("Boom")
    ):
        # show form
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == "form"
        assert result["step_id"] == "user"

        # entry was added
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_DATA
        )
        # websocket tv entry created
        assert result["type"] == "create_entry"
        assert result["title"] == "Living Room (82GXARRS)"
        assert result["data"][CONF_HOST] == "fake_host"
        assert result["data"][CONF_NAME] == "Living Room"
        assert result["data"][CONF_METHOD] == "websocket"
        assert result["data"][CONF_MANUFACTURER] == "Samsung"
        assert result["data"][CONF_MODEL] == "82GXARRS"
        assert result["result"].unique_id == "be9554b9-c9fb-41f4-8920-22da015376a4"


async def test_user_legacy_missing_auth(opp: OpenPeerPower, remote: Mock):
    """Test starting a flow by user with authentication."""
    with patch(
        "openpeerpower.components.samsungtv.bridge.Remote",
        side_effect=AccessDenied("Boom"),
    ):
        # legacy device missing authentication
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=MOCK_USER_DATA
        )
        assert result["type"] == "abort"
        assert result["reason"] == RESULT_AUTH_MISSING


async def test_user_legacy_not_supported(opp: OpenPeerPower, remote: Mock):
    """Test starting a flow by user for not supported device."""
    with patch(
        "openpeerpower.components.samsungtv.bridge.Remote",
        side_effect=UnhandledResponse("Boom"),
    ):
        # legacy device not supported
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=MOCK_USER_DATA
        )
        assert result["type"] == "abort"
        assert result["reason"] == RESULT_NOT_SUPPORTED


async def test_user_websocket_not_supported(opp: OpenPeerPower, remotews: Mock):
    """Test starting a flow by user for not supported device."""
    with patch(
        "openpeerpower.components.samsungtv.bridge.Remote",
        side_effect=OSError("Boom"),
    ), patch(
        "openpeerpower.components.samsungtv.bridge.SamsungTVWS",
        side_effect=WebSocketProtocolException("Boom"),
    ):
        # websocket device not supported
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=MOCK_USER_DATA
        )
        assert result["type"] == "abort"
        assert result["reason"] == RESULT_NOT_SUPPORTED


async def test_user_not_successful(opp: OpenPeerPower, remotews: Mock):
    """Test starting a flow by user but no connection found."""
    with patch(
        "openpeerpower.components.samsungtv.bridge.Remote",
        side_effect=OSError("Boom"),
    ), patch(
        "openpeerpower.components.samsungtv.bridge.SamsungTVWS",
        side_effect=OSError("Boom"),
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=MOCK_USER_DATA
        )
        assert result["type"] == "abort"
        assert result["reason"] == RESULT_CANNOT_CONNECT


async def test_user_not_successful_2(opp: OpenPeerPower, remotews: Mock):
    """Test starting a flow by user but no connection found."""
    with patch(
        "openpeerpower.components.samsungtv.bridge.Remote",
        side_effect=OSError("Boom"),
    ), patch(
        "openpeerpower.components.samsungtv.bridge.SamsungTVWS",
        side_effect=ConnectionFailure("Boom"),
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=MOCK_USER_DATA
        )
        assert result["type"] == "abort"
        assert result["reason"] == RESULT_CANNOT_CONNECT


async def test_ssdp(opp: OpenPeerPower, remote: Mock):
    """Test starting a flow from discovery."""

    # confirm to add the entry
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_SSDP}, data=MOCK_SSDP_DATA
    )
    assert result["type"] == "form"
    assert result["step_id"] == "confirm"

    # entry was added
    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input="whatever"
    )
    assert result["type"] == "create_entry"
    assert result["title"] == "fake_model"
    assert result["data"][CONF_HOST] == "fake_host"
    assert result["data"][CONF_NAME] == "fake_model"
    assert result["data"][CONF_MANUFACTURER] == "Samsung fake_manufacturer"
    assert result["data"][CONF_MODEL] == "fake_model"
    assert result["result"].unique_id == "0d1cef00-00dc-1000-9c80-4844f7b172de"


async def test_ssdp_noprefix(opp: OpenPeerPower, remote: Mock):
    """Test starting a flow from discovery without prefixes."""

    # confirm to add the entry
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=MOCK_SSDP_DATA_NOPREFIX,
    )
    assert result["type"] == "form"
    assert result["step_id"] == "confirm"

    # entry was added
    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input="whatever"
    )
    assert result["type"] == "create_entry"
    assert result["title"] == "fake2_model"
    assert result["data"][CONF_HOST] == "fake2_host"
    assert result["data"][CONF_NAME] == "fake2_model"
    assert result["data"][CONF_MANUFACTURER] == "Samsung fake2_manufacturer"
    assert result["data"][CONF_MODEL] == "fake2_model"
    assert result["result"].unique_id == "0d1cef00-00dc-1000-9c80-4844f7b172df"


async def test_ssdp_legacy_missing_auth(opp: OpenPeerPower, remote: Mock):
    """Test starting a flow from discovery with authentication."""
    with patch(
        "openpeerpower.components.samsungtv.bridge.Remote",
        side_effect=AccessDenied("Boom"),
    ):

        # confirm to add the entry
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_SSDP}, data=MOCK_SSDP_DATA
        )
        assert result["type"] == "form"
        assert result["step_id"] == "confirm"

        # missing authentication
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], user_input="whatever"
        )
        assert result["type"] == "abort"
        assert result["reason"] == RESULT_AUTH_MISSING


async def test_ssdp_legacy_not_supported(opp: OpenPeerPower, remote: Mock):
    """Test starting a flow from discovery for not supported device."""
    with patch(
        "openpeerpower.components.samsungtv.bridge.Remote",
        side_effect=UnhandledResponse("Boom"),
    ):

        # confirm to add the entry
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_SSDP}, data=MOCK_SSDP_DATA
        )
        assert result["type"] == "form"
        assert result["step_id"] == "confirm"

        # device not supported
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], user_input="whatever"
        )
        assert result["type"] == "abort"
        assert result["reason"] == RESULT_NOT_SUPPORTED


async def test_ssdp_websocket_not_supported(opp: OpenPeerPower, remote: Mock):
    """Test starting a flow from discovery for not supported device."""
    with patch(
        "openpeerpower.components.samsungtv.bridge.Remote",
        side_effect=OSError("Boom"),
    ), patch(
        "openpeerpower.components.samsungtv.bridge.SamsungTVWS",
        side_effect=WebSocketProtocolException("Boom"),
    ):
        # confirm to add the entry
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_SSDP}, data=MOCK_SSDP_DATA
        )
        assert result["type"] == "form"
        assert result["step_id"] == "confirm"

        # device not supported
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], user_input="whatever"
        )
        assert result["type"] == "abort"
        assert result["reason"] == RESULT_NOT_SUPPORTED


async def test_ssdp_model_not_supported(opp: OpenPeerPower, remote: Mock):
    """Test starting a flow from discovery."""

    # confirm to add the entry
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=MOCK_SSDP_DATA_WRONGMODEL,
    )
    assert result["type"] == "abort"
    assert result["reason"] == RESULT_NOT_SUPPORTED


async def test_ssdp_not_successful(opp: OpenPeerPower, remote: Mock):
    """Test starting a flow from discovery but no device found."""
    with patch(
        "openpeerpower.components.samsungtv.bridge.Remote",
        side_effect=OSError("Boom"),
    ), patch(
        "openpeerpower.components.samsungtv.bridge.SamsungTVWS",
        side_effect=OSError("Boom"),
    ):

        # confirm to add the entry
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_SSDP}, data=MOCK_SSDP_DATA
        )
        assert result["type"] == "form"
        assert result["step_id"] == "confirm"

        # device not found
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], user_input="whatever"
        )
        assert result["type"] == "abort"
        assert result["reason"] == RESULT_CANNOT_CONNECT


async def test_ssdp_not_successful_2(opp: OpenPeerPower, remote: Mock):
    """Test starting a flow from discovery but no device found."""
    with patch(
        "openpeerpower.components.samsungtv.bridge.Remote",
        side_effect=OSError("Boom"),
    ), patch(
        "openpeerpower.components.samsungtv.bridge.SamsungTVWS",
        side_effect=ConnectionFailure("Boom"),
    ):

        # confirm to add the entry
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_SSDP}, data=MOCK_SSDP_DATA
        )
        assert result["type"] == "form"
        assert result["step_id"] == "confirm"

        # device not found
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"], user_input="whatever"
        )
        assert result["type"] == "abort"
        assert result["reason"] == RESULT_CANNOT_CONNECT


async def test_ssdp_already_in_progress(opp: OpenPeerPower, remote: Mock):
    """Test starting a flow from discovery twice."""

    # confirm to add the entry
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_SSDP}, data=MOCK_SSDP_DATA
    )
    assert result["type"] == "form"
    assert result["step_id"] == "confirm"

    # failed as already in progress
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_SSDP}, data=MOCK_SSDP_DATA
    )
    assert result["type"] == "abort"
    assert result["reason"] == RESULT_ALREADY_IN_PROGRESS


async def test_ssdp_already_configured(opp: OpenPeerPower, remote: Mock):
    """Test starting a flow from discovery when already configured."""

    # entry was added
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=MOCK_USER_DATA
    )
    assert result["type"] == "create_entry"
    entry = result["result"]
    assert entry.data[CONF_MANUFACTURER] == DEFAULT_MANUFACTURER
    assert entry.data[CONF_MODEL] is None
    assert entry.unique_id is None

    # failed as already configured
    result2 = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_SSDP}, data=MOCK_SSDP_DATA
    )
    assert result2["type"] == "abort"
    assert result2["reason"] == RESULT_ALREADY_CONFIGURED

    # check updated device info
    assert entry.unique_id == "0d1cef00-00dc-1000-9c80-4844f7b172de"


async def test_import_legacy(opp: OpenPeerPower):
    """Test importing from yaml with hostname."""
    with patch(
        "openpeerpower.components.samsungtv.config_flow.socket.gethostbyname",
        return_value="fake_host",
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=MOCK_IMPORT_DATA,
        )
    await opp.async_block_till_done()
    assert result["type"] == "create_entry"
    assert result["title"] == "fake"
    assert result["data"][CONF_METHOD] == METHOD_LEGACY
    assert result["data"][CONF_HOST] == "fake_host"
    assert result["data"][CONF_NAME] == "fake"
    assert result["data"][CONF_MANUFACTURER] == "Samsung"
    assert result["result"].unique_id is None


async def test_import_legacy_without_name(opp: OpenPeerPower):
    """Test importing from yaml without a name."""
    with patch(
        "openpeerpower.components.samsungtv.config_flow.socket.gethostbyname",
        return_value="fake_host",
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=MOCK_IMPORT_DATA_WITHOUT_NAME,
        )
    await opp.async_block_till_done()
    assert result["type"] == "create_entry"
    assert result["title"] == "fake_host"
    assert result["data"][CONF_METHOD] == METHOD_LEGACY
    assert result["data"][CONF_HOST] == "fake_host"
    assert result["data"][CONF_MANUFACTURER] == "Samsung"
    assert result["result"].unique_id is None


async def test_import_websocket(opp: OpenPeerPower):
    """Test importing from yaml with hostname."""
    with patch(
        "openpeerpower.components.samsungtv.config_flow.socket.gethostbyname",
        return_value="fake_host",
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=MOCK_IMPORT_WSDATA,
        )
    await opp.async_block_till_done()
    assert result["type"] == "create_entry"
    assert result["title"] == "fake"
    assert result["data"][CONF_METHOD] == METHOD_WEBSOCKET
    assert result["data"][CONF_HOST] == "fake_host"
    assert result["data"][CONF_NAME] == "fake"
    assert result["data"][CONF_MANUFACTURER] == "Samsung"
    assert result["result"].unique_id is None


async def test_import_unknown_host(opp: OpenPeerPower, remotews: Mock):
    """Test importing from yaml with hostname that does not resolve."""
    with patch(
        "openpeerpower.components.samsungtv.config_flow.socket.gethostbyname",
        side_effect=socket.gaierror,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=MOCK_IMPORT_DATA,
        )
    await opp.async_block_till_done()
    assert result["type"] == "abort"
    assert result["reason"] == RESULT_UNKNOWN_HOST


async def test_dhcp(opp: OpenPeerPower, remotews: Mock):
    """Test starting a flow from dhcp."""
    # confirm to add the entry
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=MOCK_DHCP_DATA,
    )
    await opp.async_block_till_done()
    assert result["type"] == "form"
    assert result["step_id"] == "confirm"

    # entry was added
    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input="whatever"
    )
    assert result["type"] == "create_entry"
    assert result["title"] == "Living Room (82GXARRS)"
    assert result["data"][CONF_HOST] == "fake_host"
    assert result["data"][CONF_NAME] == "Living Room"
    assert result["data"][CONF_MAC] == "aa:bb:cc:dd:ee:ff"
    assert result["data"][CONF_MANUFACTURER] == "Samsung"
    assert result["data"][CONF_MODEL] == "82GXARRS"
    assert result["result"].unique_id == "be9554b9-c9fb-41f4-8920-22da015376a4"


async def test_zeroconf(opp: OpenPeerPower, remotews: Mock):
    """Test starting a flow from zeroconf."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=MOCK_ZEROCONF_DATA,
    )
    await opp.async_block_till_done()
    assert result["type"] == "form"
    assert result["step_id"] == "confirm"

    # entry was added
    result = await opp.config_entries.flow.async_configure(
        result["flow_id"], user_input="whatever"
    )
    assert result["type"] == "create_entry"
    assert result["title"] == "Living Room (82GXARRS)"
    assert result["data"][CONF_HOST] == "fake_host"
    assert result["data"][CONF_NAME] == "Living Room"
    assert result["data"][CONF_MAC] == "aa:bb:cc:dd:ee:ff"
    assert result["data"][CONF_MANUFACTURER] == "Samsung"
    assert result["data"][CONF_MODEL] == "82GXARRS"
    assert result["result"].unique_id == "be9554b9-c9fb-41f4-8920-22da015376a4"


async def test_zeroconf_ignores_soundbar(opp: OpenPeerPower, remotews_soundbar: Mock):
    """Test starting a flow from zeroconf where the device is actually a soundbar."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=MOCK_ZEROCONF_DATA,
    )
    await opp.async_block_till_done()
    assert result["type"] == "abort"
    assert result["reason"] == "not_supported"


async def test_zeroconf_no_device_info(
    opp: OpenPeerPower, remotews_no_device_info: Mock
):
    """Test starting a flow from zeroconf where device_info returns None."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=MOCK_ZEROCONF_DATA,
    )
    await opp.async_block_till_done()
    assert result["type"] == "abort"
    assert result["reason"] == "not_supported"


async def test_zeroconf_and_dhcp_same_time(opp: OpenPeerPower, remotews: Mock):
    """Test starting a flow from zeroconf and dhcp."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=MOCK_DHCP_DATA,
    )
    await opp.async_block_till_done()
    assert result["type"] == "form"
    assert result["step_id"] == "confirm"

    result2 = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=MOCK_ZEROCONF_DATA,
    )
    await opp.async_block_till_done()
    assert result2["type"] == "abort"
    assert result2["reason"] == "already_in_progress"


async def test_autodetect_websocket(opp: OpenPeerPower, remote: Mock, remotews: Mock):
    """Test for send key with autodetection of protocol."""
    with patch(
        "openpeerpower.components.samsungtv.bridge.Remote",
        side_effect=OSError("Boom"),
    ), patch(
        "openpeerpower.components.samsungtv.config_flow.socket.gethostbyname",
        return_value="fake_host",
    ), patch(
        "openpeerpower.components.samsungtv.bridge.SamsungTVWS"
    ) as remotews:
        enter = Mock()
        type(enter).token = PropertyMock(return_value="123456789")
        remote = Mock()
        remote.__enter__ = Mock(return_value=enter)
        remote.__exit__ = Mock(return_value=False)
        remote.rest_device_info.return_value = {
            "id": "uuid:be9554b9-c9fb-41f4-8920-22da015376a4",
            "device": {
                "modelName": "82GXARRS",
                "wifiMac": "aa:bb:cc:dd:ee:ff",
                "udn": "uuid:be9554b9-c9fb-41f4-8920-22da015376a4",
                "mac": "aa:bb:cc:dd:ee:ff",
                "name": "[TV] Living Room",
                "type": "Samsung SmartTV",
            },
        }
        remotews.return_value = remote

        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=MOCK_USER_DATA
        )
        assert result["type"] == "create_entry"
        assert result["data"][CONF_METHOD] == "websocket"
        assert result["data"][CONF_TOKEN] == "123456789"
        assert remotews.call_count == 2
        assert remotews.call_args_list == [
            call(**AUTODETECT_WEBSOCKET_SSL),
            call(**DEVICEINFO_WEBSOCKET_SSL),
        ]


async def test_autodetect_auth_missing(opp: OpenPeerPower, remote: Mock):
    """Test for send key with autodetection of protocol."""
    with patch(
        "openpeerpower.components.samsungtv.bridge.Remote",
        side_effect=[AccessDenied("Boom")],
    ) as remote, patch(
        "openpeerpower.components.samsungtv.config_flow.socket.gethostbyname",
        return_value="fake_host",
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=MOCK_USER_DATA
        )
        assert result["type"] == "abort"
        assert result["reason"] == RESULT_AUTH_MISSING
        assert remote.call_count == 1
        assert remote.call_args_list == [call(AUTODETECT_LEGACY)]


async def test_autodetect_not_supported(opp: OpenPeerPower, remote: Mock):
    """Test for send key with autodetection of protocol."""
    with patch(
        "openpeerpower.components.samsungtv.bridge.Remote",
        side_effect=[UnhandledResponse("Boom")],
    ) as remote, patch(
        "openpeerpower.components.samsungtv.config_flow.socket.gethostbyname",
        return_value="fake_host",
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=MOCK_USER_DATA
        )
        assert result["type"] == "abort"
        assert result["reason"] == RESULT_NOT_SUPPORTED
        assert remote.call_count == 1
        assert remote.call_args_list == [call(AUTODETECT_LEGACY)]


async def test_autodetect_legacy(opp: OpenPeerPower, remote: Mock):
    """Test for send key with autodetection of protocol."""
    with patch("openpeerpower.components.samsungtv.bridge.Remote") as remote:
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=MOCK_USER_DATA
        )
        assert result["type"] == "create_entry"
        assert result["data"][CONF_METHOD] == "legacy"
        assert remote.call_count == 1
        assert remote.call_args_list == [call(AUTODETECT_LEGACY)]


async def test_autodetect_none(opp: OpenPeerPower, remote: Mock, remotews: Mock):
    """Test for send key with autodetection of protocol."""
    with patch(
        "openpeerpower.components.samsungtv.bridge.Remote",
        side_effect=OSError("Boom"),
    ) as remote, patch(
        "openpeerpower.components.samsungtv.bridge.SamsungTVWS",
        side_effect=OSError("Boom"),
    ) as remotews, patch(
        "openpeerpower.components.samsungtv.config_flow.socket.gethostbyname",
        return_value="fake_host",
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=MOCK_USER_DATA
        )
        assert result["type"] == "abort"
        assert result["reason"] == RESULT_CANNOT_CONNECT
        assert remote.call_count == 1
        assert remote.call_args_list == [
            call(AUTODETECT_LEGACY),
        ]
        assert remotews.call_count == 2
        assert remotews.call_args_list == [
            call(**AUTODETECT_WEBSOCKET_SSL),
            call(**AUTODETECT_WEBSOCKET_PLAIN),
        ]


async def test_update_old_entry(opp: OpenPeerPower, remote: Mock):
    """Test update of old entry."""
    with patch("openpeerpower.components.samsungtv.bridge.Remote") as remote:
        remote().rest_device_info.return_value = {
            "device": {
                "modelName": "fake_model2",
                "name": "[TV] Fake Name",
                "udn": "uuid:fake_serial",
            }
        }

        entry = MockConfigEntry(domain=DOMAIN, data=MOCK_OLD_ENTRY)
        entry.add_to_opp(opp)

        config_entries_domain = opp.config_entries.async_entries(DOMAIN)
        assert len(config_entries_domain) == 1
        assert entry is config_entries_domain[0]
        assert entry.data[CONF_ID] == "0d1cef00-00dc-1000-9c80-4844f7b172de_old"
        assert entry.data[CONF_IP_ADDRESS] == "fake_ip_old"
        assert not entry.unique_id

        assert await async_setup_component(opp, DOMAIN, {}) is True
        await opp.async_block_till_done()

        # failed as already configured
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_SSDP}, data=MOCK_SSDP_DATA
        )
        assert result["type"] == "abort"
        assert result["reason"] == RESULT_ALREADY_CONFIGURED

        config_entries_domain = opp.config_entries.async_entries(DOMAIN)
        assert len(config_entries_domain) == 1
        entry2 = config_entries_domain[0]

        # check updated device info
        assert entry2.data.get(CONF_ID) is not None
        assert entry2.data.get(CONF_IP_ADDRESS) is not None
        assert entry2.unique_id == "0d1cef00-00dc-1000-9c80-4844f7b172de"


async def test_update_missing_mac_unique_id_added_from_dhcp(opp, remotews: Mock):
    """Test missing mac and unique id added."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_OLD_ENTRY, unique_id=None)
    entry.add_to_opp(opp)
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_DHCP},
        data=MOCK_DHCP_DATA,
    )
    await opp.async_block_till_done()
    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"
    assert entry.data[CONF_MAC] == "aa:bb:cc:dd:ee:ff"
    assert entry.unique_id == "be9554b9-c9fb-41f4-8920-22da015376a4"


async def test_update_missing_mac_unique_id_added_from_zeroconf(opp, remotews: Mock):
    """Test missing mac and unique id added."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_OLD_ENTRY, unique_id=None)
    entry.add_to_opp(opp)
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=MOCK_ZEROCONF_DATA,
    )
    await opp.async_block_till_done()
    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"
    assert entry.data[CONF_MAC] == "aa:bb:cc:dd:ee:ff"
    assert entry.unique_id == "be9554b9-c9fb-41f4-8920-22da015376a4"


async def test_update_missing_mac_added_unique_id_preserved_from_zeroconf(
    opp, remotews: Mock
):
    """Test missing mac and unique id added."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_OLD_ENTRY,
        unique_id="0d1cef00-00dc-1000-9c80-4844f7b172de",
    )
    entry.add_to_opp(opp)
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=MOCK_ZEROCONF_DATA,
    )
    await opp.async_block_till_done()
    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"
    assert entry.data[CONF_MAC] == "aa:bb:cc:dd:ee:ff"
    assert entry.unique_id == "0d1cef00-00dc-1000-9c80-4844f7b172de"


async def test_form_reauth_legacy(opp, remote: Mock):
    """Test reauthenticate legacy."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_OLD_ENTRY)
    entry.add_to_opp(opp)
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"entry_id": entry.entry_id, "source": config_entries.SOURCE_REAUTH},
        data=entry.data,
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    result2 = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    await opp.async_block_till_done()
    assert result2["type"] == "abort"
    assert result2["reason"] == "reauth_successful"


async def test_form_reauth_websocket(opp, remotews: Mock):
    """Test reauthenticate websocket."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_WS_ENTRY)
    entry.add_to_opp(opp)
    assert entry.state == config_entries.ConfigEntryState.NOT_LOADED

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"entry_id": entry.entry_id, "source": config_entries.SOURCE_REAUTH},
        data=entry.data,
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    result2 = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    await opp.async_block_till_done()
    assert result2["type"] == "abort"
    assert result2["reason"] == "reauth_successful"
    assert entry.state == config_entries.ConfigEntryState.LOADED


async def test_form_reauth_websocket_cannot_connect(opp, remotews: Mock):
    """Test reauthenticate websocket when we cannot connect on the first attempt."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_WS_ENTRY)
    entry.add_to_opp(opp)
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"entry_id": entry.entry_id, "source": config_entries.SOURCE_REAUTH},
        data=entry.data,
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.samsungtv.bridge.SamsungTVWS",
        side_effect=ConnectionFailure,
    ), patch(
        "openpeerpower.components.samsungtv.config_flow.socket.gethostbyname",
        return_value="fake_host",
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await opp.async_block_till_done()

    import pprint

    pprint.pprint(result2)
    assert result2["type"] == "form"
    assert result2["errors"] == {"base": RESULT_AUTH_MISSING}

    result3 = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    await opp.async_block_till_done()

    assert result3["type"] == "abort"
    assert result3["reason"] == "reauth_successful"


async def test_form_reauth_websocket_not_supported(opp, remotews: Mock):
    """Test reauthenticate websocket when the device is not supported."""
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_WS_ENTRY)
    entry.add_to_opp(opp)
    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"entry_id": entry.entry_id, "source": config_entries.SOURCE_REAUTH},
        data=entry.data,
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.samsungtv.bridge.SamsungTVWS",
        side_effect=WebSocketException,
    ), patch(
        "openpeerpower.components.samsungtv.config_flow.socket.gethostbyname",
        return_value="fake_host",
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await opp.async_block_till_done()

    assert result2["type"] == "abort"
    assert result2["reason"] == "not_supported"
