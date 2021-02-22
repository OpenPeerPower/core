"""Test the OVO Energy config flow."""
from unittest.mock import patch

import aiohttp

from openpeerpower import config_entries, data_entry_flow
from openpeerpower.components.ovo_energy.const import DOMAIN
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME
from openpeerpower.core import OpenPeerPower

from tests.common import MockConfigEntry

FIXTURE_REAUTH_INPUT = {CONF_PASSWORD: "something1"}
FIXTURE_USER_INPUT = {CONF_USERNAME: "example@example.com", CONF_PASSWORD: "something"}

UNIQUE_ID = "example@example.com"


async def test_show_form.opp: OpenPeerPower) -> None:
    """Test that the setup form is served."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"


async def test_authorization_error(opp: OpenPeerPower) -> None:
    """Test we show user form on connection error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    with patch(
        "openpeerpower.components.ovo_energy.config_flow.OVOEnergy.authenticate",
        return_value=False,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )

    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["step_id"] == "user"
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_connection_error(opp: OpenPeerPower) -> None:
    """Test we show user form on connection error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    with patch(
        "openpeerpower.components.ovo_energy.config_flow.OVOEnergy.authenticate",
        side_effect=aiohttp.ClientError,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )

    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["step_id"] == "user"
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_full_flow_implementation.opp: OpenPeerPower) -> None:
    """Test registering an integration and finishing flow works."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    with patch(
        "openpeerpower.components.ovo_energy.config_flow.OVOEnergy.authenticate",
        return_value=True,
    ), patch(
        "openpeerpower.components.ovo_energy.async_setup",
        return_value=True,
    ), patch(
        "openpeerpower.components.ovo_energy.async_setup_entry",
        return_value=True,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )

    assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result2["data"][CONF_USERNAME] == FIXTURE_USER_INPUT[CONF_USERNAME]
    assert result2["data"][CONF_PASSWORD] == FIXTURE_USER_INPUT[CONF_PASSWORD]


async def test_reauth_authorization_error(opp: OpenPeerPower) -> None:
    """Test we show user form on authorization error."""
    with patch(
        "openpeerpower.components.ovo_energy.config_flow.OVOEnergy.authenticate",
        return_value=False,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": "reauth"}, data=FIXTURE_USER_INPUT
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "reauth"

        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_REAUTH_INPUT,
        )
        await opp.async_block_till_done()

        assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result2["step_id"] == "reauth"
        assert result2["errors"] == {"base": "authorization_error"}


async def test_reauth_connection_error(opp: OpenPeerPower) -> None:
    """Test we show user form on connection error."""
    with patch(
        "openpeerpower.components.ovo_energy.config_flow.OVOEnergy.authenticate",
        side_effect=aiohttp.ClientError,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": "reauth"}, data=FIXTURE_USER_INPUT
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "reauth"

        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_REAUTH_INPUT,
        )
        await opp.async_block_till_done()

        assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result2["step_id"] == "reauth"
        assert result2["errors"] == {"base": "connection_error"}


async def test_reauth_flow.opp: OpenPeerPower) -> None:
    """Test reauth works."""
    with patch(
        "openpeerpower.components.ovo_energy.config_flow.OVOEnergy.authenticate",
        return_value=False,
    ):
        mock_config = MockConfigEntry(
            domain=DOMAIN, unique_id=UNIQUE_ID, data=FIXTURE_USER_INPUT
        )
        mock_config.add_to.opp.opp)

        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": "reauth"}, data=FIXTURE_USER_INPUT
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "reauth"
        assert result["errors"] == {"base": "authorization_error"}

    with patch(
        "openpeerpower.components.ovo_energy.config_flow.OVOEnergy.authenticate",
        return_value=True,
    ), patch(
        "openpeerpower.components.ovo_energy.config_flow.OVOEnergy.username",
        return_value=FIXTURE_USER_INPUT[CONF_USERNAME],
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_REAUTH_INPUT,
        )
        await opp.async_block_till_done()

        assert result2["type"] == data_entry_flow.RESULT_TYPE_ABORT
        assert result2["reason"] == "reauth_successful"
