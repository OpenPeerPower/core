"""Tests for HomematicIP Cloud config flow."""
from unittest.mock import patch

from openpeerpower.components.homematicip_cloud.const import (
    DOMAIN as HMIPC_DOMAIN,
    HMIPC_AUTHTOKEN,
    HMIPC_HAPID,
    HMIPC_NAME,
    HMIPC_PIN,
)

from tests.common import MockConfigEntry

DEFAULT_CONFIG = {HMIPC_HAPID: "ABC123", HMIPC_PIN: "123", HMIPC_NAME: "hmip"}

IMPORT_CONFIG = {HMIPC_HAPID: "ABC123", HMIPC_AUTHTOKEN: "123", HMIPC_NAME: "hmip"}


async def test_flow_works.opp, simple_mock_home):
    """Test config flow."""

    with patch(
        "openpeerpower.components.homematicip_cloud.hap.HomematicipAuth.async_checkbutton",
        return_value=False,
    ), patch(
        "openpeerpower.components.homematicip_cloud.hap.HomematicipAuth.get_auth",
        return_value=True,
    ):
        result = await.opp.config_entries.flow.async_init(
            HMIPC_DOMAIN, context={"source": "user"}, data=DEFAULT_CONFIG
        )

    assert result["type"] == "form"
    assert result["step_id"] == "link"
    assert result["errors"] == {"base": "press_the_button"}

    flow = next(
        flow
        for flow in.opp.config_entries.flow.async_progress()
        if flow["flow_id"] == result["flow_id"]
    )
    assert flow["context"]["unique_id"] == "ABC123"

    with patch(
        "openpeerpower.components.homematicip_cloud.hap.HomematicipAuth.async_checkbutton",
        return_value=True,
    ), patch(
        "openpeerpower.components.homematicip_cloud.hap.HomematicipAuth.async_setup",
        return_value=True,
    ), patch(
        "openpeerpower.components.homematicip_cloud.hap.HomematicipAuth.async_register",
        return_value=True,
    ), patch(
        "openpeerpower.components.homematicip_cloud.hap.HomematicipHAP.async_connect",
    ):
        result = await.opp.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )

    assert result["type"] == "create_entry"
    assert result["title"] == "ABC123"
    assert result["data"] == {"hapid": "ABC123", "authtoken": True, "name": "hmip"}
    assert result["result"].unique_id == "ABC123"


async def test_flow_init_connection_error.opp):
    """Test config flow with accesspoint connection error."""
    with patch(
        "openpeerpower.components.homematicip_cloud.hap.HomematicipAuth.async_setup",
        return_value=False,
    ):
        result = await.opp.config_entries.flow.async_init(
            HMIPC_DOMAIN, context={"source": "user"}, data=DEFAULT_CONFIG
        )

    assert result["type"] == "form"
    assert result["step_id"] == "init"


async def test_flow_link_connection_error.opp):
    """Test config flow client registration connection error."""
    with patch(
        "openpeerpower.components.homematicip_cloud.hap.HomematicipAuth.async_checkbutton",
        return_value=True,
    ), patch(
        "openpeerpower.components.homematicip_cloud.hap.HomematicipAuth.async_setup",
        return_value=True,
    ), patch(
        "openpeerpower.components.homematicip_cloud.hap.HomematicipAuth.async_register",
        return_value=False,
    ):
        result = await.opp.config_entries.flow.async_init(
            HMIPC_DOMAIN, context={"source": "user"}, data=DEFAULT_CONFIG
        )

    assert result["type"] == "abort"
    assert result["reason"] == "connection_aborted"


async def test_flow_link_press_button.opp):
    """Test config flow ask for pressing the blue button."""
    with patch(
        "openpeerpower.components.homematicip_cloud.hap.HomematicipAuth.async_checkbutton",
        return_value=False,
    ), patch(
        "openpeerpower.components.homematicip_cloud.hap.HomematicipAuth.async_setup",
        return_value=True,
    ):
        result = await.opp.config_entries.flow.async_init(
            HMIPC_DOMAIN, context={"source": "user"}, data=DEFAULT_CONFIG
        )

    assert result["type"] == "form"
    assert result["step_id"] == "link"
    assert result["errors"] == {"base": "press_the_button"}


async def test_init_flow_show_form.opp):
    """Test config flow shows up with a form."""

    result = await.opp.config_entries.flow.async_init(
        HMIPC_DOMAIN, context={"source": "user"}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "init"


async def test_init_already_configured.opp):
    """Test accesspoint is already configured."""
    MockConfigEntry(domain=HMIPC_DOMAIN, unique_id="ABC123").add_to.opp.opp)
    with patch(
        "openpeerpower.components.homematicip_cloud.hap.HomematicipAuth.async_checkbutton",
        return_value=True,
    ):
        result = await.opp.config_entries.flow.async_init(
            HMIPC_DOMAIN, context={"source": "user"}, data=DEFAULT_CONFIG
        )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


async def test_import_config(opp, simple_mock_home):
    """Test importing a host with an existing config file."""
    with patch(
        "openpeerpower.components.homematicip_cloud.hap.HomematicipAuth.async_checkbutton",
        return_value=True,
    ), patch(
        "openpeerpower.components.homematicip_cloud.hap.HomematicipAuth.async_setup",
        return_value=True,
    ), patch(
        "openpeerpower.components.homematicip_cloud.hap.HomematicipAuth.async_register",
        return_value=True,
    ), patch(
        "openpeerpower.components.homematicip_cloud.hap.HomematicipHAP.async_connect",
    ):
        result = await.opp.config_entries.flow.async_init(
            HMIPC_DOMAIN, context={"source": "import"}, data=IMPORT_CONFIG
        )

    assert result["type"] == "create_entry"
    assert result["title"] == "ABC123"
    assert result["data"] == {"authtoken": "123", "hapid": "ABC123", "name": "hmip"}
    assert result["result"].unique_id == "ABC123"


async def test_import_existing_config(opp):
    """Test abort of an existing accesspoint from config."""
    MockConfigEntry(domain=HMIPC_DOMAIN, unique_id="ABC123").add_to.opp.opp)
    with patch(
        "openpeerpower.components.homematicip_cloud.hap.HomematicipAuth.async_checkbutton",
        return_value=True,
    ), patch(
        "openpeerpower.components.homematicip_cloud.hap.HomematicipAuth.async_setup",
        return_value=True,
    ), patch(
        "openpeerpower.components.homematicip_cloud.hap.HomematicipAuth.async_register",
        return_value=True,
    ):
        result = await.opp.config_entries.flow.async_init(
            HMIPC_DOMAIN, context={"source": "import"}, data=IMPORT_CONFIG
        )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"
