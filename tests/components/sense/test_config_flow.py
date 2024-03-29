"""Test the Sense config flow."""
from unittest.mock import patch

from sense_energy import SenseAPITimeoutException, SenseAuthenticationException

from openpeerpower import config_entries, setup
from openpeerpower.components.sense.const import DOMAIN


async def test_form(opp):
    """Test we get the form."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch("sense_energy.ASyncSenseable.authenticate", return_value=True,), patch(
        "openpeerpower.components.sense.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"timeout": "6", "email": "test-email", "password": "test-password"},
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "test-email"
    assert result2["data"] == {
        "timeout": 6,
        "email": "test-email",
        "password": "test-password",
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_auth(opp):
    """Test we handle invalid auth."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "sense_energy.ASyncSenseable.authenticate",
        side_effect=SenseAuthenticationException,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"timeout": "6", "email": "test-email", "password": "test-password"},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_cannot_connect(opp):
    """Test we handle cannot connect error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "sense_energy.ASyncSenseable.authenticate",
        side_effect=SenseAPITimeoutException,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"timeout": "6", "email": "test-email", "password": "test-password"},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}
