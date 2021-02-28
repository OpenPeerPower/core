"""Test Goal Zero Yeti config flow."""
from unittest.mock import patch

from goalzero import exceptions

from openpeerpower.components.goalzero.const import DOMAIN
from openpeerpower.config_entries import SOURCE_USER
from openpeerpower.data_entry_flow import (
    RESULT_TYPE_ABORT,
    RESULT_TYPE_CREATE_ENTRY,
    RESULT_TYPE_FORM,
)

from . import (
    CONF_CONFIG_FLOW,
    CONF_DATA,
    CONF_HOST,
    CONF_NAME,
    NAME,
    _create_mocked_yeti,
    _patch_config_flow_yeti,
)

from tests.common import MockConfigEntry


def _flow_next(opp, flow_id):
    return next(
        flow
        for flow in opp.config_entries.flow.async_progress()
        if flow["flow_id"] == flow_id
    )


def _patch_setup():
    return patch(
        "openpeerpower.components.goalzero.async_setup_entry",
        return_value=True,
    )


async def test_flow_user(opp):
    """Test user initialized flow."""
    mocked_yeti = await _create_mocked_yeti()
    with _patch_config_flow_yeti(mocked_yeti), _patch_setup():
        result = await opp.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        result = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_CONFIG_FLOW,
        )
        assert result["type"] == RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == NAME
        assert result["data"] == CONF_DATA


async def test_flow_user_already_configured(opp):
    """Test user initialized flow with duplicate server."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "1.2.3.4", CONF_NAME: "Yeti"},
    )

    entry.add_to_opp(opp)

    service_info = {
        "host": "1.2.3.4",
        "name": "Yeti",
    }
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=service_info
    )

    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_flow_user_cannot_connect(opp):
    """Test user initialized flow with unreachable server."""
    mocked_yeti = await _create_mocked_yeti(True)
    with _patch_config_flow_yeti(mocked_yeti) as yetimock:
        yetimock.side_effect = exceptions.ConnectError
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONF_CONFIG_FLOW
        )
        assert result["type"] == RESULT_TYPE_FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {"base": "cannot_connect"}


async def test_flow_user_invalid_host(opp):
    """Test user initialized flow with invalid server."""
    mocked_yeti = await _create_mocked_yeti(True)
    with _patch_config_flow_yeti(mocked_yeti) as yetimock:
        yetimock.side_effect = exceptions.InvalidHost
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONF_CONFIG_FLOW
        )
        assert result["type"] == RESULT_TYPE_FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {"base": "invalid_host"}


async def test_flow_user_unknown_error(opp):
    """Test user initialized flow with unreachable server."""
    mocked_yeti = await _create_mocked_yeti(True)
    with _patch_config_flow_yeti(mocked_yeti) as yetimock:
        yetimock.side_effect = Exception
        result = await opp.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONF_CONFIG_FLOW
        )
        assert result["type"] == RESULT_TYPE_FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {"base": "unknown"}
