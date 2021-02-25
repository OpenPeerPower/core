"""Test the Rachio config flow."""
from unittest.mock import MagicMock, patch

from openpeerpower import config_entries, setup
from openpeerpower.components.rachio.const import (
    CONF_CUSTOM_URL,
    CONF_MANUAL_RUN_MINS,
    DOMAIN,
)
from openpeerpower.const import CONF_API_KEY

from tests.common import MockConfigEntry


def _mock_rachio_return_value(get=None, info=None):
    rachio_mock = MagicMock()
    person_mock = MagicMock()
    type(person_mock).get = MagicMock(return_value=get)
    type(person_mock).info = MagicMock(return_value=info)
    type(rachio_mock).person = person_mock
    return rachio_mock


async def test_form.opp):
    """Test we get the form."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    rachio_mock = _mock_rachio_return_value(
        get=({"status": 200}, {"username": "myusername"}),
        info=({"status": 200}, {"id": "myid"}),
    )

    with patch(
        "openpeerpower.components.rachio.config_flow.Rachio", return_value=rachio_mock
    ), patch(
        "openpeerpower.components.rachio.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.rachio.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "api_key",
                CONF_CUSTOM_URL: "http://custom.url",
                CONF_MANUAL_RUN_MINS: 5,
            },
        )
        await opp.async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "myusername"
    assert result2["data"] == {
        CONF_API_KEY: "api_key",
        CONF_CUSTOM_URL: "http://custom.url",
        CONF_MANUAL_RUN_MINS: 5,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_auth.opp):
    """Test we handle invalid auth."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    rachio_mock = _mock_rachio_return_value(
        get=({"status": 200}, {"username": "myusername"}),
        info=({"status": 412}, {"error": "auth fail"}),
    )
    with patch(
        "openpeerpower.components.rachio.config_flow.Rachio", return_value=rachio_mock
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "api_key"},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_cannot_connect.opp):
    """Test we handle cannot connect error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    rachio_mock = _mock_rachio_return_value(
        get=({"status": 599}, {"username": "myusername"}),
        info=({"status": 200}, {"id": "myid"}),
    )
    with patch(
        "openpeerpower.components.rachio.config_flow.Rachio", return_value=rachio_mock
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "api_key"},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_homekit.opp):
    """Test that we abort from homekit if rachio is already setup."""
    await setup.async_setup_component(opp, "persistent_notification", {})

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "homekit"},
        data={"properties": {"id": "AA:BB:CC:DD:EE:FF"}},
    )
    assert result["type"] == "form"
    assert result["errors"] == {}
    flow = next(
        flow
        for flow in opp.config_entries.flow.async_progress()
        if flow["flow_id"] == result["flow_id"]
    )
    assert flow["context"]["unique_id"] == "AA:BB:CC:DD:EE:FF"

    entry = MockConfigEntry(domain=DOMAIN, data={CONF_API_KEY: "api_key"})
    entry.add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "homekit"},
        data={"properties": {"id": "AA:BB:CC:DD:EE:FF"}},
    )
    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"
