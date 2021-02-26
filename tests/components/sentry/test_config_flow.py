"""Test the sentry config flow."""
import logging
from unittest.mock import patch

from sentry_sdk.utils import BadDsn

from openpeerpower.components.sentry.const import (
    CONF_ENVIRONMENT,
    CONF_EVENT_CUSTOM_COMPONENTS,
    CONF_EVENT_HANDLED,
    CONF_EVENT_THIRD_PARTY_PACKAGES,
    CONF_LOGGING_EVENT_LEVEL,
    CONF_LOGGING_LEVEL,
    CONF_TRACING,
    CONF_TRACING_SAMPLE_RATE,
    DOMAIN,
)
from openpeerpower.config_entries import SOURCE_USER
from openpeerpower.data_entry_flow import RESULT_TYPE_ABORT, RESULT_TYPE_FORM
from openpeerpower.setup import async_setup_component

from tests.common import MockConfigEntry


async def test_full_user_flow_implementation(opp):
    """Test we get the form."""
    await async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {}

    with patch("openpeerpower.components.sentry.config_flow.Dsn"), patch(
        "openpeerpower.components.sentry.async_setup", return_value=True
    ) as mock_setup, patch(
        "openpeerpower.components.sentry.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"dsn": "http://public@sentry.local/1"},
        )

    assert result2["type"] == "create_entry"
    assert result2["title"] == "Sentry"
    assert result2["data"] == {
        "dsn": "http://public@sentry.local/1",
    }
    await opp.async_block_till_done()

    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_integration_already_exists(opp):
    """Test we only allow a single config flow."""
    MockConfigEntry(domain=DOMAIN).add_to_opp(opp)

    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_user_flow_bad_dsn(opp):
    """Test we handle bad dsn error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.sentry.config_flow.Dsn",
        side_effect=BadDsn,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"dsn": "foo"},
        )

    assert result2["type"] == RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "bad_dsn"}


async def test_user_flow_unkown_exception(opp):
    """Test we handle any unknown exception error."""
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    with patch(
        "openpeerpower.components.sentry.config_flow.Dsn",
        side_effect=Exception,
    ):
        result2 = await opp.config_entries.flow.async_configure(
            result["flow_id"],
            {"dsn": "foo"},
        )

    assert result2["type"] == RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "unknown"}


async def test_options_flow(opp):
    """Test options config flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"dsn": "http://public@sentry.local/1"},
    )
    entry.add_to_opp(opp)

    with patch("openpeerpower.components.sentry.async_setup_entry", return_value=True):
        assert await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()

    result = await opp.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == RESULT_TYPE_FORM
    assert result["step_id"] == "init"

    result = await opp.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_ENVIRONMENT: "Test",
            CONF_EVENT_CUSTOM_COMPONENTS: True,
            CONF_EVENT_HANDLED: True,
            CONF_EVENT_THIRD_PARTY_PACKAGES: True,
            CONF_LOGGING_EVENT_LEVEL: logging.DEBUG,
            CONF_LOGGING_LEVEL: logging.DEBUG,
            CONF_TRACING: True,
            CONF_TRACING_SAMPLE_RATE: 0.5,
        },
    )

    assert result["type"] == "create_entry"
    assert result["data"] == {
        CONF_ENVIRONMENT: "Test",
        CONF_EVENT_CUSTOM_COMPONENTS: True,
        CONF_EVENT_HANDLED: True,
        CONF_EVENT_THIRD_PARTY_PACKAGES: True,
        CONF_LOGGING_EVENT_LEVEL: logging.DEBUG,
        CONF_LOGGING_LEVEL: logging.DEBUG,
        CONF_TRACING: True,
        CONF_TRACING_SAMPLE_RATE: 0.5,
    }
