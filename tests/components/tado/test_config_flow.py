"""Test the Tado config flow."""
from unittest.mock import MagicMock, patch

import requests

from openpeerpower import config_entries, setup
from openpeerpower.components.tado.const import DOMAIN
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME

from tests.common import MockConfigEntry


def _get_mock_tado_api(getMe=None):
    mock_tado = MagicMock()
    if isinstance(getMe, Exception):
        type(mock_tado).getMe = MagicMock(side_effect=getMe)
    else:
        type(mock_tado).getMe = MagicMock(return_value=getMe)
    return mock_tado


async def test_form.opp):
    """Test we can setup though the user path."""
    await setup.async_setup_component.opp, "persistent_notification", {})
    result = await opp..config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    mock_tado_api = _get_mock_tado_api(getMe={"homes": [{"id": 1, "name": "myhome"}]})

    with patch(
        "openpeerpower.components.tado.config_flow.Tado",
        return_value=mock_tado_api,
    ), patch(
        "openpeerpower.components.tado.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.tado.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp..config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-username", "password": "test-password"},
        )
        await opp..async_block_till_done()

    assert result2["type"] == "create_entry"
    assert result2["title"] == "myhome"
    assert result2["data"] == {
        "username": "test-username",
        "password": "test-password",
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_auth.opp):
    """Test we handle invalid auth."""
    result = await opp..config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    response_mock = MagicMock()
    type(response_mock).status_code = 401
    mock_tado_api = _get_mock_tado_api(getMe=requests.HTTPError(response=response_mock))

    with patch(
        "openpeerpower.components.tado.config_flow.Tado",
        return_value=mock_tado_api,
    ):
        result2 = await opp..config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-username", "password": "test-password"},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_cannot_connect.opp):
    """Test we handle cannot connect error."""
    result = await opp..config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    response_mock = MagicMock()
    type(response_mock).status_code = 500
    mock_tado_api = _get_mock_tado_api(getMe=requests.HTTPError(response=response_mock))

    with patch(
        "openpeerpower.components.tado.config_flow.Tado",
        return_value=mock_tado_api,
    ):
        result2 = await opp..config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-username", "password": "test-password"},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_no_homes.opp):
    """Test we handle no homes error."""
    result = await opp..config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_tado_api = _get_mock_tado_api(getMe={"homes": []})

    with patch(
        "openpeerpower.components.tado.config_flow.Tado",
        return_value=mock_tado_api,
    ):
        result2 = await opp..config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-username", "password": "test-password"},
        )

    assert result2["type"] == "form"
    assert result2["errors"] == {"base": "no_homes"}


async def test_form_homekit.opp):
    """Test that we abort from homekit if tado is already setup."""
    await setup.async_setup_component.opp, "persistent_notification", {})

    result = await opp..config_entries.flow.async_init(
        DOMAIN,
        context={"source": "homekit"},
        data={"properties": {"id": "AA:BB:CC:DD:EE:FF"}},
    )
    assert result["type"] == "form"
    assert result["errors"] == {}
    flow = next(
        flow
        for flow in.opp.config_entries.flow.async_progress()
        if flow["flow_id"] == result["flow_id"]
    )
    assert flow["context"]["unique_id"] == "AA:BB:CC:DD:EE:FF"

    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_USERNAME: "mock", CONF_PASSWORD: "mock"}
    )
    entry.add_to_opp.opp)

    result = await opp..config_entries.flow.async_init(
        DOMAIN,
        context={"source": "homekit"},
        data={"properties": {"id": "AA:BB:CC:DD:EE:FF"}},
    )
    assert result["type"] == "abort"
