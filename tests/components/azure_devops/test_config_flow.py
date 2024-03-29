"""Test the Azure DevOps config flow."""
from unittest.mock import patch

from aioazuredevops.core import DevOpsProject
import aiohttp

from openpeerpower import config_entries, data_entry_flow
from openpeerpower.components.azure_devops.const import (
    CONF_ORG,
    CONF_PAT,
    CONF_PROJECT,
    DOMAIN,
)
from openpeerpower.core import OpenPeerPower

from tests.common import MockConfigEntry

FIXTURE_REAUTH_INPUT = {CONF_PAT: "abc123"}
FIXTURE_USER_INPUT = {CONF_ORG: "random", CONF_PROJECT: "project", CONF_PAT: "abc123"}

UNIQUE_ID = "random_project"


async def test_show_user_form(opp: OpenPeerPower) -> None:
    """Test that the setup form is served."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"


async def test_authorization_error(opp: OpenPeerPower) -> None:
    """Test we show user form on Azure DevOps authorization error."""
    with patch(
        "openpeerpower.components.azure_devops.config_flow.DevOpsClient.authorize",
        return_value=False,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "user"

        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )
        await opp.async_block_till_done()

        assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result2["step_id"] == "user"
        assert result2["errors"] == {"base": "invalid_auth"}


async def test_reauth_authorization_error(opp: OpenPeerPower) -> None:
    """Test we show user form on Azure DevOps authorization error."""
    with patch(
        "openpeerpower.components.azure_devops.config_flow.DevOpsClient.authorize",
        return_value=False,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_REAUTH},
            data=FIXTURE_USER_INPUT,
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
        assert result2["errors"] == {"base": "invalid_auth"}


async def test_connection_error(opp: OpenPeerPower) -> None:
    """Test we show user form on Azure DevOps connection error."""
    with patch(
        "openpeerpower.components.azure_devops.config_flow.DevOpsClient.authorize",
        side_effect=aiohttp.ClientError,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "user"

        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )
        await opp.async_block_till_done()

        assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result2["step_id"] == "user"
        assert result2["errors"] == {"base": "cannot_connect"}


async def test_reauth_connection_error(opp: OpenPeerPower) -> None:
    """Test we show user form on Azure DevOps connection error."""
    with patch(
        "openpeerpower.components.azure_devops.config_flow.DevOpsClient.authorize",
        side_effect=aiohttp.ClientError,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_REAUTH},
            data=FIXTURE_USER_INPUT,
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
        assert result2["errors"] == {"base": "cannot_connect"}


async def test_project_error(opp: OpenPeerPower) -> None:
    """Test we show user form on Azure DevOps connection error."""
    with patch(
        "openpeerpower.components.azure_devops.config_flow.DevOpsClient.authorized",
        return_value=True,
    ), patch(
        "openpeerpower.components.azure_devops.config_flow.DevOpsClient.authorize",
    ), patch(
        "openpeerpower.components.azure_devops.config_flow.DevOpsClient.get_project",
        return_value=None,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "user"

        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )
        await opp.async_block_till_done()

        assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result2["step_id"] == "user"
        assert result2["errors"] == {"base": "project_error"}


async def test_reauth_project_error(opp: OpenPeerPower) -> None:
    """Test we show user form on Azure DevOps project error."""
    with patch(
        "openpeerpower.components.azure_devops.config_flow.DevOpsClient.authorize",
    ), patch(
        "openpeerpower.components.azure_devops.config_flow.DevOpsClient.authorized",
        return_value=True,
    ), patch(
        "openpeerpower.components.azure_devops.config_flow.DevOpsClient.get_project",
        return_value=None,
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_REAUTH},
            data=FIXTURE_USER_INPUT,
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
        assert result2["errors"] == {"base": "project_error"}


async def test_reauth_flow(opp: OpenPeerPower) -> None:
    """Test reauth works."""
    with patch(
        "openpeerpower.components.azure_devops.config_flow.DevOpsClient.authorize",
        return_value=False,
    ):
        mock_config = MockConfigEntry(
            domain=DOMAIN, unique_id=UNIQUE_ID, data=FIXTURE_USER_INPUT
        )
        mock_config.add_to_opp(opp)

        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_REAUTH},
            data=FIXTURE_USER_INPUT,
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "reauth"
        assert result["errors"] == {"base": "invalid_auth"}

    with patch(
        "openpeerpower.components.azure_devops.config_flow.DevOpsClient.authorize",
    ), patch(
        "openpeerpower.components.azure_devops.config_flow.DevOpsClient.authorized",
        return_value=True,
    ), patch(
        "openpeerpower.components.azure_devops.config_flow.DevOpsClient.get_project",
        return_value=DevOpsProject(
            "abcd-abcd-abcd-abcd", FIXTURE_USER_INPUT[CONF_PROJECT]
        ),
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_REAUTH_INPUT,
        )
        await opp.async_block_till_done()

        assert result2["type"] == data_entry_flow.RESULT_TYPE_ABORT
        assert result2["reason"] == "reauth_successful"


async def test_full_flow_implementation(opp: OpenPeerPower) -> None:
    """Test registering an integration and finishing flow works."""
    with patch(
        "openpeerpower.components.azure_devops.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry, patch(
        "openpeerpower.components.azure_devops.config_flow.DevOpsClient.authorized",
        return_value=True,
    ), patch(
        "openpeerpower.components.azure_devops.config_flow.DevOpsClient.authorize",
    ), patch(
        "openpeerpower.components.azure_devops.config_flow.DevOpsClient.get_project",
        return_value=DevOpsProject(
            "abcd-abcd-abcd-abcd", FIXTURE_USER_INPUT[CONF_PROJECT]
        ),
    ):
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "user"

        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )
        await opp.async_block_till_done()
        assert len(mock_setup_entry.mock_calls) == 1

        assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert (
            result2["title"]
            == f"{FIXTURE_USER_INPUT[CONF_ORG]}/{FIXTURE_USER_INPUT[CONF_PROJECT]}"
        )
        assert result2["data"][CONF_ORG] == FIXTURE_USER_INPUT[CONF_ORG]
        assert result2["data"][CONF_PROJECT] == FIXTURE_USER_INPUT[CONF_PROJECT]
