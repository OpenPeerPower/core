"""Test the Panasonic Viera config flow."""
from unittest.mock import patch

from panasonic_viera import SOAPError

from openpeerpower import config_entries
from openpeerpower.components.panasonic_viera.const import (
    ATTR_DEVICE_INFO,
    DEFAULT_NAME,
    DOMAIN,
    ERROR_INVALID_PIN_CODE,
)
from openpeerpower.const import CONF_PIN

from .conftest import (
    MOCK_BASIC_DATA,
    MOCK_CONFIG_DATA,
    MOCK_DEVICE_INFO,
    MOCK_ENCRYPTION_DATA,
    get_mock_remote,
)

from tests.common import MockConfigEntry


async def test_flow_non_encrypted(opp):
    """Test flow without encryption."""

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"

    mock_remote = get_mock_remote(encrypted=False)

    with patch(
        "openpeerpower.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_BASIC_DATA,
        )

    assert result["type"] == "create_entry"
    assert result["title"] == DEFAULT_NAME
    assert result["data"] == {**MOCK_CONFIG_DATA, ATTR_DEVICE_INFO: MOCK_DEVICE_INFO}


async def test_flow_not_connected_error(opp):
    """Test flow with connection error."""

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"

    with patch(
        "openpeerpower.components.panasonic_viera.config_flow.RemoteControl",
        side_effect=TimeoutError,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_BASIC_DATA,
        )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_flow_unknown_abort(opp):
    """Test flow with unknown error abortion."""

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"

    with patch(
        "openpeerpower.components.panasonic_viera.config_flow.RemoteControl",
        side_effect=Exception,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_BASIC_DATA,
        )

    assert result["type"] == "abort"
    assert result["reason"] == "unknown"


async def test_flow_encrypted_not_connected_pin_code_request(opp):
    """Test flow with encryption and PIN code request connection error abortion during pairing request step."""

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"

    mock_remote = get_mock_remote(encrypted=True, request_error=TimeoutError)

    with patch(
        "openpeerpower.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_BASIC_DATA,
        )

    assert result["type"] == "abort"
    assert result["reason"] == "cannot_connect"


async def test_flow_encrypted_unknown_pin_code_request(opp):
    """Test flow with encryption and PIN code request unknown error abortion during pairing request step."""

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"

    mock_remote = get_mock_remote(encrypted=True, request_error=Exception)

    with patch(
        "openpeerpower.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_BASIC_DATA,
        )

    assert result["type"] == "abort"
    assert result["reason"] == "unknown"


async def test_flow_encrypted_valid_pin_code(opp):
    """Test flow with encryption and valid PIN code."""

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"

    mock_remote = get_mock_remote(
        encrypted=True,
        app_id="mock-app-id",
        encryption_key="mock-encryption-key",
    )

    with patch(
        "openpeerpower.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_BASIC_DATA,
        )

    assert result["type"] == "form"
    assert result["step_id"] == "pairing"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PIN: "1234"},
    )

    assert result["type"] == "create_entry"
    assert result["title"] == DEFAULT_NAME
    assert result["data"] == {
        **MOCK_CONFIG_DATA,
        **MOCK_ENCRYPTION_DATA,
        ATTR_DEVICE_INFO: MOCK_DEVICE_INFO,
    }


async def test_flow_encrypted_invalid_pin_code_error(opp):
    """Test flow with encryption and invalid PIN code error during pairing step."""

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"

    mock_remote = get_mock_remote(encrypted=True, authorize_error=SOAPError)

    with patch(
        "openpeerpower.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_BASIC_DATA,
        )

    assert result["type"] == "form"
    assert result["step_id"] == "pairing"

    with patch(
        "openpeerpower.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PIN: "0000"},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "pairing"
    assert result["errors"] == {"base": ERROR_INVALID_PIN_CODE}


async def test_flow_encrypted_not_connected_abort(opp):
    """Test flow with encryption and PIN code connection error abortion during pairing step."""

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"

    mock_remote = get_mock_remote(encrypted=True, authorize_error=TimeoutError)

    with patch(
        "openpeerpower.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_BASIC_DATA,
        )

    assert result["type"] == "form"
    assert result["step_id"] == "pairing"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PIN: "0000"},
    )

    assert result["type"] == "abort"
    assert result["reason"] == "cannot_connect"


async def test_flow_encrypted_unknown_abort(opp):
    """Test flow with encryption and PIN code unknown error abortion during pairing step."""

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"

    mock_remote = get_mock_remote(encrypted=True, authorize_error=Exception)

    with patch(
        "openpeerpower.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_BASIC_DATA,
        )

    assert result["type"] == "form"
    assert result["step_id"] == "pairing"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PIN: "0000"},
    )

    assert result["type"] == "abort"
    assert result["reason"] == "unknown"


async def test_flow_non_encrypted_already_configured_abort(opp):
    """Test flow without encryption and existing config entry abortion."""

    MockConfigEntry(
        domain=DOMAIN,
        unique_id="0.0.0.0",
        data=MOCK_CONFIG_DATA,
    ).add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=MOCK_BASIC_DATA,
    )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


async def test_flow_encrypted_already_configured_abort(opp):
    """Test flow with encryption and existing config entry abortion."""

    MockConfigEntry(
        domain=DOMAIN,
        unique_id="0.0.0.0",
        data={**MOCK_CONFIG_DATA, **MOCK_ENCRYPTION_DATA},
    ).add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=MOCK_BASIC_DATA,
    )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


async def test_imported_flow_non_encrypted(opp):
    """Test imported flow without encryption."""

    mock_remote = get_mock_remote(encrypted=False)

    with patch(
        "openpeerpower.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=MOCK_CONFIG_DATA,
        )

    assert result["type"] == "create_entry"
    assert result["title"] == DEFAULT_NAME
    assert result["data"] == {**MOCK_CONFIG_DATA, ATTR_DEVICE_INFO: MOCK_DEVICE_INFO}


async def test_imported_flow_encrypted_valid_pin_code(opp):
    """Test imported flow with encryption and valid PIN code."""

    mock_remote = get_mock_remote(
        encrypted=True,
        app_id="mock-app-id",
        encryption_key="mock-encryption-key",
    )

    with patch(
        "openpeerpower.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=MOCK_CONFIG_DATA,
        )

    assert result["type"] == "form"
    assert result["step_id"] == "pairing"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PIN: "1234"},
    )

    assert result["type"] == "create_entry"
    assert result["title"] == DEFAULT_NAME
    assert result["data"] == {
        **MOCK_CONFIG_DATA,
        **MOCK_ENCRYPTION_DATA,
        ATTR_DEVICE_INFO: MOCK_DEVICE_INFO,
    }


async def test_imported_flow_encrypted_invalid_pin_code_error(opp):
    """Test imported flow with encryption and invalid PIN code error during pairing step."""

    mock_remote = get_mock_remote(encrypted=True, authorize_error=SOAPError)

    with patch(
        "openpeerpower.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=MOCK_CONFIG_DATA,
        )

    assert result["type"] == "form"
    assert result["step_id"] == "pairing"

    with patch(
        "openpeerpower.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PIN: "0000"},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "pairing"
    assert result["errors"] == {"base": ERROR_INVALID_PIN_CODE}


async def test_imported_flow_encrypted_not_connected_abort(opp):
    """Test imported flow with encryption and PIN code connection error abortion during pairing step."""

    mock_remote = get_mock_remote(encrypted=True, authorize_error=TimeoutError)

    with patch(
        "openpeerpower.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=MOCK_CONFIG_DATA,
        )

    assert result["type"] == "form"
    assert result["step_id"] == "pairing"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PIN: "0000"},
    )

    assert result["type"] == "abort"
    assert result["reason"] == "cannot_connect"


async def test_imported_flow_encrypted_unknown_abort(opp):
    """Test imported flow with encryption and PIN code unknown error abortion during pairing step."""

    mock_remote = get_mock_remote(encrypted=True, authorize_error=Exception)

    with patch(
        "openpeerpower.components.panasonic_viera.config_flow.RemoteControl",
        return_value=mock_remote,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=MOCK_CONFIG_DATA,
        )

    assert result["type"] == "form"
    assert result["step_id"] == "pairing"

    result = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PIN: "0000"},
    )

    assert result["type"] == "abort"
    assert result["reason"] == "unknown"


async def test_imported_flow_not_connected_error(opp):
    """Test imported flow with connection error abortion."""

    with patch(
        "openpeerpower.components.panasonic_viera.config_flow.RemoteControl",
        side_effect=TimeoutError,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=MOCK_CONFIG_DATA,
        )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_imported_flow_unknown_abort(opp):
    """Test imported flow with unknown error abortion."""

    with patch(
        "openpeerpower.components.panasonic_viera.config_flow.RemoteControl",
        side_effect=Exception,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=MOCK_CONFIG_DATA,
        )

    assert result["type"] == "abort"
    assert result["reason"] == "unknown"


async def test_imported_flow_non_encrypted_already_configured_abort(opp):
    """Test imported flow without encryption and existing config entry abortion."""

    MockConfigEntry(
        domain=DOMAIN,
        unique_id="0.0.0.0",
        data=MOCK_CONFIG_DATA,
    ).add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data=MOCK_BASIC_DATA,
    )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


async def test_imported_flow_encrypted_already_configured_abort(opp):
    """Test imported flow with encryption and existing config entry abortion."""

    MockConfigEntry(
        domain=DOMAIN,
        unique_id="0.0.0.0",
        data={**MOCK_CONFIG_DATA, **MOCK_ENCRYPTION_DATA},
    ).add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data=MOCK_BASIC_DATA,
    )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"
