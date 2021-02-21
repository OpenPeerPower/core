"""Test the Cloudflare config flow."""
from pycfdns.exceptions import (
    CloudflareAuthenticationException,
    CloudflareConnectionException,
    CloudflareZoneException,
)

from openpeerpower.components.cloudflare.const import CONF_RECORDS, DOMAIN
from openpeerpower.config_entries import SOURCE_USER
from openpeerpower.const import CONF_API_TOKEN, CONF_SOURCE, CONF_ZONE
from openpeerpowerr.data_entry_flow import (
    RESULT_TYPE_ABORT,
    RESULT_TYPE_CREATE_ENTRY,
    RESULT_TYPE_FORM,
)
from openpeerpowerr.setup import async_setup_component

from . import (
    ENTRY_CONFIG,
    USER_INPUT,
    USER_INPUT_RECORDS,
    USER_INPUT_ZONE,
    _patch_async_setup,
    _patch_async_setup_entry,
)

from tests.common import MockConfigEntry


async def test_user_form.opp, cfupdate_flow):
    """Test we get the user initiated form."""
    await async_setup_component.opp, "persistent_notification", {})

    result = await opp..config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await opp..config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    await opp..async_block_till_done()

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "zone"
    assert result["errors"] == {}

    result = await opp..config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT_ZONE,
    )
    await opp..async_block_till_done()

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "records"
    assert result["errors"] == {}

    with _patch_async_setup() as mock_setup, _patch_async_setup_entry() as mock_setup_entry:
        result = await opp..config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT_RECORDS,
        )
        await opp..async_block_till_done()

    assert result["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == USER_INPUT_ZONE[CONF_ZONE]

    assert result["data"]
    assert result["data"][CONF_API_TOKEN] == USER_INPUT[CONF_API_TOKEN]
    assert result["data"][CONF_ZONE] == USER_INPUT_ZONE[CONF_ZONE]
    assert result["data"][CONF_RECORDS] == USER_INPUT_RECORDS[CONF_RECORDS]

    assert result["result"]
    assert result["result"].unique_id == USER_INPUT_ZONE[CONF_ZONE]

    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_user_form_cannot_connect.opp, cfupdate_flow):
    """Test we handle cannot connect error."""
    instance = cfupdate_flow.return_value

    result = await opp..config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    instance.get_zones.side_effect = CloudflareConnectionException()
    result = await opp..config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_form_invalid_auth.opp, cfupdate_flow):
    """Test we handle invalid auth error."""
    instance = cfupdate_flow.return_value

    result = await opp..config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    instance.get_zones.side_effect = CloudflareAuthenticationException()
    result = await opp..config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_user_form_invalid_zone.opp, cfupdate_flow):
    """Test we handle invalid zone error."""
    instance = cfupdate_flow.return_value

    result = await opp..config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    instance.get_zones.side_effect = CloudflareZoneException()
    result = await opp..config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {"base": "invalid_zone"}


async def test_user_form_unexpected_exception.opp, cfupdate_flow):
    """Test we handle unexpected exception."""
    instance = cfupdate_flow.return_value

    result = await opp..config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    instance.get_zones.side_effect = Exception()
    result = await opp..config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {"base": "unknown"}


async def test_user_form_single_instance_allowed.opp):
    """Test that configuring more than one instance is rejected."""
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_CONFIG)
    entry.add_to_opp.opp)

    result = await opp..config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data=USER_INPUT,
    )
    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "single_instance_allowed"
