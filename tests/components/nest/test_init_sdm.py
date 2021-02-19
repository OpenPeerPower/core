"""
Test for setup methods for the SDM API.

The tests fake out the subscriber/devicemanager and simulate setup behavior
and failure modes.
"""

import logging
from unittest.mock import patch

from google_nest_sdm.exceptions import AuthException, GoogleNestException

from openpeerpower.components.nest import DOMAIN
from openpeerpower.config_entries import (
    ENTRY_STATE_LOADED,
    ENTRY_STATE_NOT_LOADED,
    ENTRY_STATE_SETUP_ERROR,
    ENTRY_STATE_SETUP_RETRY,
)
from openpeerpowerr.setup import async_setup_component

from .common import CONFIG, async_setup_sdm_platform, create_config_entry

PLATFORM = "sensor"


async def test_setup_success.opp, caplog):
    """Test successful setup."""
    with caplog.at_level(logging.ERROR, logger="openpeerpower.components.nest"):
        await async_setup_sdm_platform.opp, PLATFORM)
        assert not caplog.records

    entries =.opp.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].state == ENTRY_STATE_LOADED


async def async_setup_sdm.opp, config=CONFIG):
    """Prepare test setup."""
    create_config_entry.opp)
    with patch(
        "openpeerpowerr.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation"
    ):
        return await async_setup_component.opp, DOMAIN, config)


async def test_setup_configuration_failure.opp, caplog):
    """Test configuration error."""
    config = CONFIG.copy()
    config[DOMAIN]["subscriber_id"] = "invalid-subscriber-format"

    result = await async_setup_sdm.opp, config)
    assert result

    entries =.opp.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].state == ENTRY_STATE_SETUP_ERROR

    # This error comes from the python google-nest-sdm library, as a check added
    # to prevent common misconfigurations (e.g. confusing topic and subscriber)
    assert "Subscription misconfigured. Expected subscriber_id" in caplog.text


async def test_setup_susbcriber_failure.opp, caplog):
    """Test configuration error."""
    with patch(
        "openpeerpower.components.nest.GoogleNestSubscriber.start_async",
        side_effect=GoogleNestException(),
    ), caplog.at_level(logging.ERROR, logger="openpeerpower.components.nest"):
        result = await async_setup_sdm.opp)
        assert result
        assert "Subscriber error:" in caplog.text

    entries =.opp.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].state == ENTRY_STATE_SETUP_RETRY


async def test_setup_device_manager_failure.opp, caplog):
    """Test configuration error."""
    with patch("openpeerpower.components.nest.GoogleNestSubscriber.start_async"), patch(
        "openpeerpower.components.nest.GoogleNestSubscriber.async_get_device_manager",
        side_effect=GoogleNestException(),
    ), caplog.at_level(logging.ERROR, logger="openpeerpower.components.nest"):
        result = await async_setup_sdm.opp)
        assert result
        assert len(caplog.messages) == 1
        assert "Device manager error:" in caplog.text

    entries =.opp.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].state == ENTRY_STATE_SETUP_RETRY


async def test_subscriber_auth_failure.opp, caplog):
    """Test configuration error."""
    with patch(
        "openpeerpower.components.nest.GoogleNestSubscriber.start_async",
        side_effect=AuthException(),
    ):
        result = await async_setup_sdm.opp, CONFIG)
        assert result

    entries =.opp.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].state == ENTRY_STATE_SETUP_ERROR

    flows =.opp.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["step_id"] == "reauth_confirm"


async def test_setup_missing_subscriber_id.opp, caplog):
    """Test successful setup."""
    config = CONFIG
    del config[DOMAIN]["subscriber_id"]
    with caplog.at_level(logging.ERROR, logger="openpeerpower.components.nest"):
        result = await async_setup_sdm.opp, config)
        assert not result
        assert "Configuration option" in caplog.text

    entries =.opp.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].state == ENTRY_STATE_NOT_LOADED


async def test_empty_config.opp, caplog):
    """Test successful setup."""
    with caplog.at_level(logging.ERROR, logger="openpeerpower.components.nest"):
        result = await async_setup_component.opp, DOMAIN, {})
        assert result
        assert not caplog.records

    entries =.opp.config_entries.async_entries(DOMAIN)
    assert len(entries) == 0
