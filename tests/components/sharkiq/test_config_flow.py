"""Test the Shark IQ config flow."""
from unittest.mock import patch

import aiohttp
import pytest
from sharkiqpy import AylaApi, SharkIqAuthError

from openpeerpower import config_entries, setup
from openpeerpower.components.sharkiq.const import DOMAIN
from openpeerpower.core import OpenPeerPower

from .const import CONFIG, TEST_PASSWORD, TEST_USERNAME, UNIQUE_ID

from tests.common import MockConfigEntry


async def test_form.opp):
    """Test we get the form."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch("sharkiqpy.AylaApi.async_sign_in", return_value=True), patch(
        "openpeerpower.components.sharkiq.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.sharkiq.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG,
        )

    assert result2["type"] == "create_entry"
    assert result2["title"] == f"{TEST_USERNAME:s}"
    assert result2["data"] == {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD,
    }
    await opp.async_block_till_done()
    mock_setup.assert_called_once()
    mock_setup_entry.assert_called_once()


@pytest.mark.parametrize(
    "exc,base_error",
    [
        (SharkIqAuthError, "invalid_auth"),
        (aiohttp.ClientError, "cannot_connect"),
        (TypeError, "unknown"),
    ],
)
async def test_form_error(opp: OpenPeerPower, exc: Exception, base_error: str):
    """Test form errors."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch.object(AylaApi, "async_sign_in", side_effect=exc):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            CONFIG,
        )

    assert result2["type"] == "form"
    assert result2["errors"].get("base") == base_error


async def test_reauth_success.opp: OpenPeerPower):
    """Test reauth flow."""
    with patch("sharkiqpy.AylaApi.async_sign_in", return_value=True):
        mock_config = MockConfigEntry(domain=DOMAIN, unique_id=UNIQUE_ID, data=CONFIG)
        mock_config.add_to_opp(opp)

        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": "reauth", "unique_id": UNIQUE_ID}, data=CONFIG
        )

        assert result["type"] == "abort"
        assert result["reason"] == "reauth_successful"


@pytest.mark.parametrize(
    "side_effect,result_type,msg_field,msg",
    [
        (SharkIqAuthError, "form", "errors", "invalid_auth"),
        (aiohttp.ClientError, "abort", "reason", "cannot_connect"),
        (TypeError, "abort", "reason", "unknown"),
    ],
)
async def test_reauth(
    opp: OpenPeerPower,
    side_effect: Exception,
    result_type: str,
    msg_field: str,
    msg: str,
):
    """Test reauth failures."""
    with patch("sharkiqpy.AylaApi.async_sign_in", side_effect=side_effect):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "reauth", "unique_id": UNIQUE_ID},
            data=CONFIG,
        )

        msg_value = result[msg_field]
        if msg_field == "errors":
            msg_value = msg_value.get("base")

        assert result["type"] == result_type
        assert msg_value == msg
