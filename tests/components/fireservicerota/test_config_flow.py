"""Test the FireServiceRota config flow."""
from unittest.mock import patch

from pyfireservicerota import InvalidAuthError

from openpeerpower import data_entry_flow
from openpeerpower.components.fireservicerota.const import DOMAIN
from openpeerpower.const import CONF_PASSWORD, CONF_URL, CONF_USERNAME

from tests.common import MockConfigEntry

MOCK_CONF = {
    CONF_USERNAME: "my@email.address",
    CONF_PASSWORD: "mypassw0rd",
    CONF_URL: "www.brandweerrooster.nl",
}

MOCK_DATA = {
    "auth_implementation": DOMAIN,
    CONF_URL: MOCK_CONF[CONF_URL],
    CONF_USERNAME: MOCK_CONF[CONF_USERNAME],
    "token": {
        "access_token": "test-access-token",
        "token_type": "Bearer",
        "expires_in": 1234,
        "refresh_token": "test-refresh-token",
        "created_at": 4321,
    },
}

MOCK_TOKEN_INFO = {
    "access_token": "test-access-token",
    "token_type": "Bearer",
    "expires_in": 1234,
    "refresh_token": "test-refresh-token",
    "created_at": 4321,
}


async def test_show_form.opp):
    """Test that the form is served with no input."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"


async def test_abort_if_already_setup_opp):
    """Test abort if already setup."""
    entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONF, unique_id=MOCK_CONF[CONF_USERNAME]
    )
    entry.add_to_opp(opp)
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}, data=MOCK_CONF
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_invalid_credentials.opp):
    """Test that invalid credentials throws an error."""

    with patch(
        "openpeerpower.components.fireservicerota.FireServiceRota.request_tokens",
        side_effect=InvalidAuthError,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}, data=MOCK_CONF
        )
        assert result["errors"] == {"base": "invalid_auth"}


async def test_step_user.opp):
    """Test the start of the config flow."""

    with patch(
        "openpeerpower.components.fireservicerota.config_flow.FireServiceRota"
    ) as mock_fsr, patch(
        "openpeerpower.components.fireservicerota.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.fireservicerota.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:

        mock_fireservicerota = mock_fsr.return_value
        mock_fireservicerota.request_tokens.return_value = MOCK_TOKEN_INFO

        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}, data=MOCK_CONF
        )

        await opp.async_block_till_done()

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == MOCK_CONF[CONF_USERNAME]
        assert result["data"] == {
            "auth_implementation": "fireservicerota",
            CONF_URL: "www.brandweerrooster.nl",
            CONF_USERNAME: "my@email.address",
            "token": {
                "access_token": "test-access-token",
                "token_type": "Bearer",
                "expires_in": 1234,
                "refresh_token": "test-refresh-token",
                "created_at": 4321,
            },
        }

        assert len(mock_setup.mock_calls) == 1
        assert len(mock_setup_entry.mock_calls) == 1
