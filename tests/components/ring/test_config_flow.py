"""Test the Ring config flow."""
from unittest.mock import Mock, patch

from openpeerpower import config_entries, setup
from openpeerpower.components.ring import DOMAIN
from openpeerpower.components.ring.config_flow import InvalidAuth


async def test_form.opp):
    """Test we get the form."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch(
        "openpeerpower.components.ring.config_flow.Auth",
        return_value=Mock(
            fetch_token=Mock(return_value={"access_token": "mock-token"})
        ),
    ), patch(
        "openpeerpower.components.ring.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.ring.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "hello@open-peer-power.io", "password": "test-password"},
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "hello@open-peer-power.io"
    assert result2["data"] == {
        "username": "hello@open-peer-power.io",
        "token": {"access_token": "mock-token"},
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_auth.opp):
    """Test we handle invalid auth."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.ring.config_flow.Auth.fetch_token",
        side_effect=InvalidAuth,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "hello@open-peer-power.io", "password": "test-password"},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "invalid_auth"}
