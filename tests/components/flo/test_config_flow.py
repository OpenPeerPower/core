"""Test the flo config flow."""
import json
import time
from unittest.mock import patch

from openpeerpower import config_entries, setup
from openpeerpower.components.flo.const import DOMAIN
from openpeerpower.const import CONTENT_TYPE_JSON

from .common import TEST_EMAIL_ADDRESS, TEST_PASSWORD, TEST_TOKEN, TEST_USER_ID


async def test_form.opp, aioclient_mock_fixture):
    """Test we get the form."""
    await setup.async_setup_component.opp, "persistent_notification", {})
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.flo.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.flo.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result2 = await.opp.config_entries.flow.async_configure(
            result["flow_id"], {"username": TEST_USER_ID, "password": TEST_PASSWORD}
        )

        assert result2["type"] == "create_entry"
        assert result2["title"] == "Home"
        assert result2["data"] == {"username": TEST_USER_ID, "password": TEST_PASSWORD}
        await opp.async_block_till_done()
        assert len(mock_setup.mock_calls) == 1
        assert len(mock_setup_entry.mock_calls) == 1


async def test_form_cannot_connect.opp, aioclient_mock):
    """Test we handle cannot connect error."""
    now = round(time.time())
    # Mocks a failed login response for flo.
    aioclient_mock.post(
        "https://api.meetflo.com/api/v1/users/auth",
        json=json.dumps(
            {
                "token": TEST_TOKEN,
                "tokenPayload": {
                    "user": {"user_id": TEST_USER_ID, "email": TEST_EMAIL_ADDRESS},
                    "timestamp": now,
                },
                "tokenExpiration": 86400,
                "timeNow": now,
            }
        ),
        headers={"Content-Type": CONTENT_TYPE_JSON},
        status=400,
    )
    result = await.opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await.opp.config_entries.flow.async_configure(
        result["flow_id"], {"username": "test-username", "password": "test-password"}
    )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}
