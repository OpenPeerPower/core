"""Test helpers for Panasonic Viera."""

from unittest.mock import Mock, patch

from panasonic_viera import TV_TYPE_ENCRYPTED, TV_TYPE_NONENCRYPTED
import pytest

from openpeerpower.components.panasonic_viera.const import (
    ATTR_FRIENDLY_NAME,
    ATTR_MANUFACTURER,
    ATTR_MODEL_NUMBER,
    ATTR_UDN,
    CONF_APP_ID,
    CONF_ENCRYPTION_KEY,
    CONF_ON_ACTION,
    DEFAULT_MANUFACTURER,
    DEFAULT_MODEL_NUMBER,
    DEFAULT_NAME,
    DEFAULT_PORT,
)
from openpeerpower.const import CONF_HOST, CONF_NAME, CONF_PORT

MOCK_BASIC_DATA = {
    CONF_HOST: "0.0.0.0",
    CONF_NAME: DEFAULT_NAME,
}

MOCK_CONFIG_DATA = {
    **MOCK_BASIC_DATA,
    CONF_PORT: DEFAULT_PORT,
    CONF_ON_ACTION: None,
}

MOCK_ENCRYPTION_DATA = {
    CONF_APP_ID: "mock-app-id",
    CONF_ENCRYPTION_KEY: "mock-encryption-key",
}

MOCK_DEVICE_INFO = {
    ATTR_FRIENDLY_NAME: DEFAULT_NAME,
    ATTR_MANUFACTURER: DEFAULT_MANUFACTURER,
    ATTR_MODEL_NUMBER: DEFAULT_MODEL_NUMBER,
    ATTR_UDN: "mock-unique-id",
}


def get_mock_remote(
    request_error=None,
    authorize_error=None,
    encrypted=False,
    app_id=None,
    encryption_key=None,
    device_info=MOCK_DEVICE_INFO,
):
    """Return a mock remote."""
    mock_remote = Mock()

    mock_remote.type = TV_TYPE_ENCRYPTED if encrypted else TV_TYPE_NONENCRYPTED
    mock_remote.app_id = app_id
    mock_remote.enc_key = encryption_key

    def request_pin_code(name=None):
        if request_error is not None:
            raise request_error

    mock_remote.request_pin_code = request_pin_code

    def authorize_pin_code(pincode):
        if pincode == "1234":
            return

        if authorize_error is not None:
            raise authorize_error

    mock_remote.authorize_pin_code = authorize_pin_code

    def get_device_info():
        return device_info

    mock_remote.get_device_info = get_device_info

    def send_key(key):
        return

    mock_remote.send_key = Mock(send_key)

    def get_volume(key):
        return 100

    mock_remote.get_volume = Mock(get_volume)

    return mock_remote


@pytest.fixture(name="mock_remote")
def mock_remote_fixture():
    """Patch the library remote."""
    mock_remote = get_mock_remote()

    with patch(
        "openpeerpower.components.panasonic_viera.RemoteControl",
        return_value=mock_remote,
    ):
        yield mock_remote
