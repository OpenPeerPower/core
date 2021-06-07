"""Test the Broadlink config flow."""
import errno
import socket
from unittest.mock import call, patch

import broadlink.exceptions as blke
import pytest

from openpeerpower import config_entries, setup
from openpeerpower.components.broadlink.const import DOMAIN
from openpeerpower.components.dhcp import HOSTNAME, IP_ADDRESS, MAC_ADDRESS
from openpeerpower.helpers import device_registry

from . import get_device

DEVICE_HELLO = "openpeerpower.components.broadlink.config_flow.blk.hello"
DEVICE_FACTORY = "openpeerpower.components.broadlink.config_flow.blk.gendevice"


@pytest.fixture(autouse=True)
def broadlink_setup_fixture():
    """Mock broadlink entry setup."""
    with patch(
        "openpeerpower.components.broadlink.async_setup", return_value=True
    ), patch("openpeerpower.components.broadlink.async_setup_entry", return_value=True):
        yield


async def test_flow_user_works(opp):
    """Test a config flow initiated by the user.

    Best case scenario with no errors or locks.
    """
    device = get_device("Living Room")
    mock_api = device.get_mock_api()

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(DEVICE_HELLO, return_value=mock_api) as mock_hello:
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": device.host, "timeout": device.timeout},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "finish"
    assert result["errors"] == {}

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": device.name},
    )

    assert result["type"] == "create_entry"
    assert result["title"] == device.name
    assert result["data"] == device.get_entry_data()

    assert mock_hello.call_count == 1
    assert mock_api.auth.call_count == 1


async def test_flow_user_already_in_progress(opp):
    """Test we do not accept more than one config flow per device."""
    device = get_device("Living Room")

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(DEVICE_HELLO, return_value=device.get_mock_api()):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": device.host, "timeout": device.timeout},
        )

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(DEVICE_HELLO, return_value=device.get_mock_api()):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": device.host, "timeout": device.timeout},
        )

    assert result["type"] == "abort"
    assert result["reason"] == "already_in_progress"


async def test_flow_user_mac_already_configured(opp):
    """Test we do not accept more than one config entry per device.

    We need to abort the flow and update the existing entry.
    """
    device = get_device("Living Room")
    mock_entry = device.get_mock_entry()
    mock_entry.add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    device.host = "192.168.1.64"
    device.timeout = 20
    mock_api = device.get_mock_api()

    with patch(DEVICE_HELLO, return_value=mock_api):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": device.host, "timeout": device.timeout},
        )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"

    assert dict(mock_entry.data) == device.get_entry_data()
    assert mock_api.auth.call_count == 0


async def test_flow_user_invalid_ip_address(opp):
    """Test we handle an invalid IP address in the user step."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(DEVICE_HELLO, side_effect=OSError(errno.EINVAL, None)):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "0.0.0.1"},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_host"}


async def test_flow_user_invalid_hostname(opp):
    """Test we handle an invalid hostname in the user step."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(DEVICE_HELLO, side_effect=OSError(socket.EAI_NONAME, None)):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "pancakemaster.local"},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_host"}


async def test_flow_user_device_not_found(opp):
    """Test we handle a device not found in the user step."""
    device = get_device("Living Room")

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(DEVICE_HELLO, side_effect=blke.NetworkTimeoutError()):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": device.host},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_flow_user_device_not_supported(opp):
    """Test we handle a device not supported in the user step."""
    device = get_device("Kitchen")
    mock_api = device.get_mock_api()

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(DEVICE_HELLO, return_value=mock_api):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": device.host},
        )

    assert result["type"] == "abort"
    assert result["reason"] == "not_supported"


async def test_flow_user_network_unreachable(opp):
    """Test we handle a network unreachable in the user step."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(DEVICE_HELLO, side_effect=OSError(errno.ENETUNREACH, None)):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "192.168.1.32"},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_flow_user_os_error(opp):
    """Test we handle an OS error in the user step."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(DEVICE_HELLO, side_effect=OSError()):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "192.168.1.32"},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "unknown"}


async def test_flow_auth_authentication_error(opp):
    """Test we handle an authentication error in the auth step."""
    device = get_device("Living Room")
    mock_api = device.get_mock_api()
    mock_api.auth.side_effect = blke.AuthenticationError()

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(DEVICE_HELLO, return_value=mock_api):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": device.host, "timeout": device.timeout},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "reset"
    assert result["errors"] == {"base": "invalid_auth"}


async def test_flow_auth_network_timeout(opp):
    """Test we handle a network timeout in the auth step."""
    device = get_device("Living Room")
    mock_api = device.get_mock_api()
    mock_api.auth.side_effect = blke.NetworkTimeoutError()

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(DEVICE_HELLO, return_value=mock_api):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": device.host},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "auth"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_flow_auth_firmware_error(opp):
    """Test we handle a firmware error in the auth step."""
    device = get_device("Living Room")
    mock_api = device.get_mock_api()
    mock_api.auth.side_effect = blke.BroadlinkException()

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(DEVICE_HELLO, return_value=mock_api):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": device.host},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "auth"
    assert result["errors"] == {"base": "unknown"}


async def test_flow_auth_network_unreachable(opp):
    """Test we handle a network unreachable in the auth step."""
    device = get_device("Living Room")
    mock_api = device.get_mock_api()
    mock_api.auth.side_effect = OSError(errno.ENETUNREACH, None)

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(DEVICE_HELLO, return_value=mock_api):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": device.host},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "auth"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_flow_auth_os_error(opp):
    """Test we handle an OS error in the auth step."""
    device = get_device("Living Room")
    mock_api = device.get_mock_api()
    mock_api.auth.side_effect = OSError()

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(DEVICE_HELLO, return_value=mock_api):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": device.host},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "auth"
    assert result["errors"] == {"base": "unknown"}


async def test_flow_reset_works(opp):
    """Test we finish a config flow after a manual unlock."""
    device = get_device("Living Room")
    mock_api = device.get_mock_api()
    mock_api.auth.side_effect = blke.AuthenticationError()

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(DEVICE_HELLO, return_value=mock_api):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": device.host, "timeout": device.timeout},
        )

    with patch(DEVICE_HELLO, return_value=device.get_mock_api()):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": device.host, "timeout": device.timeout},
        )

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": device.name},
    )

    assert result["type"] == "create_entry"
    assert result["title"] == device.name
    assert result["data"] == device.get_entry_data()


async def test_flow_unlock_works(opp):
    """Test we finish a config flow with an unlock request."""
    device = get_device("Living Room")
    mock_api = device.get_mock_api()
    mock_api.is_locked = True

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(DEVICE_HELLO, return_value=mock_api):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": device.host, "timeout": device.timeout},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "unlock"
    assert result["errors"] == {}

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {"unlock": True},
    )

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": device.name},
    )

    assert result["type"] == "create_entry"
    assert result["title"] == device.name
    assert result["data"] == device.get_entry_data()

    assert mock_api.set_lock.call_args == call(False)
    assert mock_api.set_lock.call_count == 1


async def test_flow_unlock_network_timeout(opp):
    """Test we handle a network timeout in the unlock step."""
    device = get_device("Living Room")
    mock_api = device.get_mock_api()
    mock_api.is_locked = True
    mock_api.set_lock.side_effect = blke.NetworkTimeoutError()

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(DEVICE_HELLO, return_value=mock_api):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": device.host, "timeout": device.timeout},
        )

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {"unlock": True},
    )

    assert result["type"] == "form"
    assert result["step_id"] == "unlock"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_flow_unlock_firmware_error(opp):
    """Test we handle a firmware error in the unlock step."""
    device = get_device("Living Room")
    mock_api = device.get_mock_api()
    mock_api.is_locked = True
    mock_api.set_lock.side_effect = blke.BroadlinkException

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(DEVICE_HELLO, return_value=mock_api):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": device.host, "timeout": device.timeout},
        )

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {"unlock": True},
    )

    assert result["type"] == "form"
    assert result["step_id"] == "unlock"
    assert result["errors"] == {"base": "unknown"}


async def test_flow_unlock_network_unreachable(opp):
    """Test we handle a network unreachable in the unlock step."""
    device = get_device("Living Room")
    mock_api = device.get_mock_api()
    mock_api.is_locked = True
    mock_api.set_lock.side_effect = OSError(errno.ENETUNREACH, None)

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(DEVICE_HELLO, return_value=mock_api):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": device.host, "timeout": device.timeout},
        )

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {"unlock": True},
    )

    assert result["type"] == "form"
    assert result["step_id"] == "unlock"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_flow_unlock_os_error(opp):
    """Test we handle an OS error in the unlock step."""
    device = get_device("Living Room")
    mock_api = device.get_mock_api()
    mock_api.is_locked = True
    mock_api.set_lock.side_effect = OSError()

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(DEVICE_HELLO, return_value=mock_api):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": device.host, "timeout": device.timeout},
        )

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {"unlock": True},
    )

    assert result["type"] == "form"
    assert result["step_id"] == "unlock"
    assert result["errors"] == {"base": "unknown"}


async def test_flow_do_not_unlock(opp):
    """Test we do not unlock the device if the user does not want to."""
    device = get_device("Living Room")
    mock_api = device.get_mock_api()
    mock_api.is_locked = True

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(DEVICE_HELLO, return_value=mock_api):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": device.host, "timeout": device.timeout},
        )

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {"unlock": False},
    )

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": device.name},
    )

    assert result["type"] == "create_entry"
    assert result["title"] == device.name
    assert result["data"] == device.get_entry_data()

    assert mock_api.set_lock.call_count == 0


async def test_flow_import_works(opp):
    """Test an import flow."""
    device = get_device("Living Room")
    mock_api = device.get_mock_api()

    with patch(DEVICE_HELLO, return_value=mock_api) as mock_hello:
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={"host": device.host},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "finish"
    assert result["errors"] == {}

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": device.name},
    )

    assert result["type"] == "create_entry"
    assert result["title"] == device.name
    assert result["data"]["host"] == device.host
    assert result["data"]["mac"] == device.mac
    assert result["data"]["type"] == device.devtype

    assert mock_api.auth.call_count == 1
    assert mock_hello.call_count == 1


async def test_flow_import_already_in_progress(opp):
    """Test we do not import more than one flow per device."""
    device = get_device("Living Room")
    data = {"host": device.host}

    with patch(DEVICE_HELLO, return_value=device.get_mock_api()):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data=data
        )

    with patch(DEVICE_HELLO, return_value=device.get_mock_api()):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data=data
        )

    assert result["type"] == "abort"
    assert result["reason"] == "already_in_progress"


async def test_flow_import_host_already_configured(opp):
    """Test we do not import a host that is already configured."""
    device = get_device("Living Room")
    mock_entry = device.get_mock_entry()
    mock_entry.add_to_opp(opp)
    mock_api = device.get_mock_api()

    with patch(DEVICE_HELLO, return_value=mock_api):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={"host": device.host},
        )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


async def test_flow_import_mac_already_configured(opp):
    """Test we do not import more than one config entry per device.

    We need to abort the flow and update the existing entry.
    """
    device = get_device("Living Room")
    mock_entry = device.get_mock_entry()
    mock_entry.add_to_opp(opp)

    device.host = "192.168.1.16"
    mock_api = device.get_mock_api()

    with patch(DEVICE_HELLO, return_value=mock_api):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={"host": device.host},
        )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"

    assert mock_entry.data["host"] == device.host
    assert mock_entry.data["mac"] == device.mac
    assert mock_entry.data["type"] == device.devtype
    assert mock_api.auth.call_count == 0


async def test_flow_import_device_not_found(opp):
    """Test we handle a device not found in the import step."""
    with patch(DEVICE_HELLO, side_effect=blke.NetworkTimeoutError()):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={"host": "192.168.1.32"},
        )

    assert result["type"] == "abort"
    assert result["reason"] == "cannot_connect"


async def test_flow_import_device_not_supported(opp):
    """Test we handle a device not supported in the import step."""
    device = get_device("Kitchen")
    mock_api = device.get_mock_api()

    with patch(DEVICE_HELLO, return_value=mock_api):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={"host": device.host},
        )

    assert result["type"] == "abort"
    assert result["reason"] == "not_supported"


async def test_flow_import_invalid_ip_address(opp):
    """Test we handle an invalid IP address in the import step."""
    with patch(DEVICE_HELLO, side_effect=OSError(errno.EINVAL, None)):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={"host": "0.0.0.1"},
        )

    assert result["type"] == "abort"
    assert result["reason"] == "invalid_host"


async def test_flow_import_invalid_hostname(opp):
    """Test we handle an invalid hostname in the import step."""
    with patch(DEVICE_HELLO, side_effect=OSError(socket.EAI_NONAME, None)):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={"host": "hotdog.local"},
        )

    assert result["type"] == "abort"
    assert result["reason"] == "invalid_host"


async def test_flow_import_network_unreachable(opp):
    """Test we handle a network unreachable in the import step."""
    with patch(DEVICE_HELLO, side_effect=OSError(errno.ENETUNREACH, None)):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={"host": "192.168.1.64"},
        )

    assert result["type"] == "abort"
    assert result["reason"] == "cannot_connect"


async def test_flow_import_os_error(opp):
    """Test we handle an OS error in the import step."""
    with patch(DEVICE_HELLO, side_effect=OSError()):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={"host": "192.168.1.64"},
        )

    assert result["type"] == "abort"
    assert result["reason"] == "unknown"


async def test_flow_reauth_works(opp):
    """Test a reauthentication flow."""
    device = get_device("Living Room")
    mock_entry = device.get_mock_entry()
    mock_entry.add_to_opp(opp)
    mock_api = device.get_mock_api()
    mock_api.auth.side_effect = blke.AuthenticationError()
    data = {"name": device.name, **device.get_entry_data()}

    with patch(DEVICE_FACTORY, return_value=mock_api):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_REAUTH}, data=data
        )

    assert result["type"] == "form"
    assert result["step_id"] == "reset"

    mock_api = device.get_mock_api()

    with patch(DEVICE_HELLO, return_value=mock_api) as mock_hello:
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": device.host, "timeout": device.timeout},
        )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"

    assert dict(mock_entry.data) == device.get_entry_data()
    assert mock_api.auth.call_count == 1
    assert mock_hello.call_count == 1


async def test_flow_reauth_invalid_host(opp):
    """Test we do not accept an invalid host for reauthentication.

    The MAC address cannot change.
    """
    device = get_device("Living Room")
    mock_entry = device.get_mock_entry()
    mock_entry.add_to_opp(opp)
    mock_api = device.get_mock_api()
    mock_api.auth.side_effect = blke.AuthenticationError()
    data = {"name": device.name, **device.get_entry_data()}

    with patch(DEVICE_FACTORY, return_value=mock_api):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_REAUTH}, data=data
        )

    device.mac = get_device("Office").mac
    mock_api = device.get_mock_api()

    with patch(DEVICE_HELLO, return_value=mock_api) as mock_hello:
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": device.host, "timeout": device.timeout},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_host"}

    assert mock_hello.call_count == 1
    assert mock_api.auth.call_count == 0


async def test_flow_reauth_valid_host(opp):
    """Test we accept a valid host for reauthentication.

    The hostname/IP address may change. We need to update the entry.
    """
    device = get_device("Living Room")
    mock_entry = device.get_mock_entry()
    mock_entry.add_to_opp(opp)
    mock_api = device.get_mock_api()
    mock_api.auth.side_effect = blke.AuthenticationError()
    data = {"name": device.name, **device.get_entry_data()}

    with patch(DEVICE_FACTORY, return_value=mock_api):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_REAUTH}, data=data
        )

    device.host = "192.168.1.128"
    mock_api = device.get_mock_api()

    with patch(DEVICE_HELLO, return_value=mock_api) as mock_hello:
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": device.host, "timeout": device.timeout},
        )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"

    assert mock_entry.data["host"] == device.host
    assert mock_hello.call_count == 1
    assert mock_api.auth.call_count == 1


async def test_dhcp_can_finish(opp):
    """Test DHCP discovery flow can finish right away."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    device = get_device("Living Room")
    device.host = "1.2.3.4"
    mock_api = device.get_mock_api()

    with patch(DEVICE_HELLO, return_value=mock_api):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data={
                HOSTNAME: "broadlink",
                IP_ADDRESS: "1.2.3.4",
                MAC_ADDRESS: device_registry.format_mac(device.mac),
            },
        )
        await opp.async_block_till_done()

    assert result["type"] == "form"
    assert result["step_id"] == "finish"

    result2 = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "Living Room"
    assert result2["data"] == {
        "host": "1.2.3.4",
        "mac": "34ea34b43b5a",
        "timeout": 10,
        "type": 24374,
    }


async def test_dhcp_fails_to_connect(opp):
    """Test DHCP discovery flow that fails to connect."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    with patch(DEVICE_HELLO, side_effect=blke.NetworkTimeoutError()):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data={
                HOSTNAME: "broadlink",
                IP_ADDRESS: "1.2.3.4",
                MAC_ADDRESS: "34:ea:34:b4:3b:5a",
            },
        )
        await opp.async_block_till_done()

    assert result["type"] == "abort"
    assert result["reason"] == "cannot_connect"


async def test_dhcp_unreachable(opp):
    """Test DHCP discovery flow that fails to connect."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    with patch(DEVICE_HELLO, side_effect=OSError(errno.ENETUNREACH, None)):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data={
                HOSTNAME: "broadlink",
                IP_ADDRESS: "1.2.3.4",
                MAC_ADDRESS: "34:ea:34:b4:3b:5a",
            },
        )
        await opp.async_block_till_done()

    assert result["type"] == "abort"
    assert result["reason"] == "cannot_connect"


async def test_dhcp_connect_unknown_error(opp):
    """Test DHCP discovery flow that fails to connect with an OSError."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    with patch(DEVICE_HELLO, side_effect=OSError()):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data={
                HOSTNAME: "broadlink",
                IP_ADDRESS: "1.2.3.4",
                MAC_ADDRESS: "34:ea:34:b4:3b:5a",
            },
        )
        await opp.async_block_till_done()

    assert result["type"] == "abort"
    assert result["reason"] == "unknown"


async def test_dhcp_device_not_supported(opp):
    """Test DHCP discovery flow that fails because the device is not supported."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    device = get_device("Kitchen")
    mock_api = device.get_mock_api()

    with patch(DEVICE_HELLO, return_value=mock_api):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data={
                HOSTNAME: "broadlink",
                IP_ADDRESS: device.host,
                MAC_ADDRESS: device_registry.format_mac(device.mac),
            },
        )

    assert result["type"] == "abort"
    assert result["reason"] == "not_supported"


async def test_dhcp_already_exists(opp):
    """Test DHCP discovery flow that fails to connect."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    device = get_device("Living Room")
    mock_entry = device.get_mock_entry()
    mock_entry.add_to_opp(opp)
    device.host = "1.2.3.4"
    mock_api = device.get_mock_api()

    with patch(DEVICE_HELLO, return_value=mock_api):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data={
                HOSTNAME: "broadlink",
                IP_ADDRESS: "1.2.3.4",
                MAC_ADDRESS: "34:ea:34:b4:3b:5a",
            },
        )
        await opp.async_block_till_done()

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


async def test_dhcp_updates_host(opp):
    """Test DHCP updates host."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    device = get_device("Living Room")
    device.host = "1.2.3.4"
    mock_entry = device.get_mock_entry()
    mock_entry.add_to_opp(opp)
    mock_api = device.get_mock_api()

    with patch(DEVICE_HELLO, return_value=mock_api):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data={
                HOSTNAME: "broadlink",
                IP_ADDRESS: "4.5.6.7",
                MAC_ADDRESS: "34:ea:34:b4:3b:5a",
            },
        )
        await opp.async_block_till_done()

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"
    assert mock_entry.data["host"] == "4.5.6.7"
