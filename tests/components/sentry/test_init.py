"""Tests for Sentry integration."""
import logging
from unittest.mock import MagicMock, Mock, patch

import pytest

from openpeerpower.components.sentry import get_channel, process_before_send
from openpeerpower.components.sentry.const import (
    CONF_DSN,
    CONF_ENVIRONMENT,
    CONF_EVENT_CUSTOM_COMPONENTS,
    CONF_EVENT_HANDLED,
    CONF_EVENT_THIRD_PARTY_PACKAGES,
    CONF_TRACING,
    CONF_TRACING_SAMPLE_RATE,
    DOMAIN,
)
from openpeerpower.const import __version__ as current_version
from openpeerpower.core import OpenPeerPower

from tests.common import MockConfigEntry


async def test_setup_entry.opp: OpenPeerPower) -> None:
    """Test integration setup from entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_DSN: "http://public@example.com/1", CONF_ENVIRONMENT: "production"},
    )
    entry.add_to.opp.opp)

    with patch(
        "openpeerpower.components.sentry.AioHttpIntegration"
    ) as sentry_aiohttp_mock, patch(
        "openpeerpower.components.sentry.SqlalchemyIntegration"
    ) as sentry_sqlalchemy_mock, patch(
        "openpeerpower.components.sentry.LoggingIntegration"
    ) as sentry_logging_mock, patch(
        "openpeerpower.components.sentry.sentry_sdk"
    ) as sentry_mock:
        assert await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()

    # Test CONF_ENVIRONMENT is migrated to entry options
    assert CONF_ENVIRONMENT not in entry.data
    assert CONF_ENVIRONMENT in entry.options
    assert entry.options[CONF_ENVIRONMENT] == "production"

    assert sentry_logging_mock.call_count == 1
    assert sentry_logging_mock.called_once_with(
        level=logging.WARNING, event_level=logging.WARNING
    )

    assert sentry_aiohttp_mock.call_count == 1
    assert sentry_sqlalchemy_mock.call_count == 1
    assert sentry_mock.init.call_count == 1

    call_args = sentry_mock.init.call_args[1]
    assert set(call_args) == {
        "dsn",
        "environment",
        "integrations",
        "release",
        "before_send",
    }
    assert call_args["dsn"] == "http://public@example.com/1"
    assert call_args["environment"] == "production"
    assert call_args["integrations"] == [
        sentry_logging_mock.return_value,
        sentry_aiohttp_mock.return_value,
        sentry_sqlalchemy_mock.return_value,
    ]
    assert call_args["release"] == current_version
    assert call_args["before_send"]


async def test_setup_entry_with_tracing.opp: OpenPeerPower) -> None:
    """Test integration setup from entry with tracing enabled."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_DSN: "http://public@example.com/1"},
        options={CONF_TRACING: True, CONF_TRACING_SAMPLE_RATE: 0.5},
    )
    entry.add_to.opp.opp)

    with patch("openpeerpower.components.sentry.AioHttpIntegration"), patch(
        "openpeerpower.components.sentry.SqlalchemyIntegration"
    ), patch("openpeerpower.components.sentry.LoggingIntegration"), patch(
        "openpeerpower.components.sentry.sentry_sdk"
    ) as sentry_mock:
        assert await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()

    call_args = sentry_mock.init.call_args[1]
    assert set(call_args) == {
        "dsn",
        "environment",
        "integrations",
        "release",
        "before_send",
        "traces_sample_rate",
    }
    assert call_args["traces_sample_rate"] == 0.5


@pytest.mark.parametrize(
    "version,channel",
    [
        ("0.115.0.dev20200815", "nightly"),
        ("0.115.0", "stable"),
        ("0.115.0b4", "beta"),
        ("0.115.0dev0", "dev"),
    ],
)
async def test_get_channel(version, channel) -> None:
    """Test if channel detection works from Open Peer Power version number."""
    assert get_channel(version) == channel


async def test_process_before_send.opp: OpenPeerPower):
    """Test regular use of the Sentry process before sending function."""
    opp.config.components.add("puppies")
    opp.config.components.add("a_integration")

    # These should not show up in the result.
    opp.config.components.add("puppies.light")
    opp.config.components.add("auth")

    result = process_before_send(
        opp,
        options={},
        channel="test",
        huuid="12345",
        system_info={"installation_type": "pytest"},
        custom_components=["ironing_robot", "fridge_opener"],
        event={},
        hint={},
    )

    assert result
    assert result["tags"]
    assert result["contexts"]
    assert result["contexts"]

    op_context = result["contexts"]["Open Peer Power"]
    assert op_context["channel"] == "test"
    assert op_context["custom_components"] == "fridge_opener\nironing_robot"
    assert op_context["integrations"] == "a_integration\npuppies"

    tags = result["tags"]
    assert tags["channel"] == "test"
    assert tags["uuid"] == "12345"
    assert tags["installation_type"] == "pytest"

    user = result["user"]
    assert user["id"] == "12345"


async def test_event_with_platform_context.opp: OpenPeerPower):
    """Test extraction of platform context information during Sentry events."""

    current_platform_mock = Mock()
    current_platform_mock.get().platform_name = "hue"
    current_platform_mock.get().domain = "light"

    with patch(
        "openpeerpower.components.sentry.entity_platform.current_platform",
        new=current_platform_mock,
    ):
        result = process_before_send(
            opp,
            options={},
            channel="test",
            huuid="12345",
            system_info={"installation_type": "pytest"},
            custom_components=["ironing_robot"],
            event={},
            hint={},
        )

    assert result
    assert result["tags"]["integration"] == "hue"
    assert result["tags"]["platform"] == "light"
    assert result["tags"]["custom_component"] == "no"

    current_platform_mock.get().platform_name = "ironing_robot"
    current_platform_mock.get().domain = "switch"

    with patch(
        "openpeerpower.components.sentry.entity_platform.current_platform",
        new=current_platform_mock,
    ):
        result = process_before_send(
            opp,
            options={CONF_EVENT_CUSTOM_COMPONENTS: True},
            channel="test",
            huuid="12345",
            system_info={"installation_type": "pytest"},
            custom_components=["ironing_robot"],
            event={},
            hint={},
        )

    assert result
    assert result["tags"]["integration"] == "ironing_robot"
    assert result["tags"]["platform"] == "switch"
    assert result["tags"]["custom_component"] == "yes"


@pytest.mark.parametrize(
    "logger,tags",
    [
        ("adguard", {"package": "adguard"}),
        (
            "openpeerpower.components.hue.coordinator",
            {"integration": "hue", "custom_component": "no"},
        ),
        (
            "openpeerpower.components.hue.light",
            {"integration": "hue", "platform": "light", "custom_component": "no"},
        ),
        (
            "openpeerpower.components.ironing_robot.switch",
            {
                "integration": "ironing_robot",
                "platform": "switch",
                "custom_component": "yes",
            },
        ),
        (
            "openpeerpower.components.ironing_robot",
            {"integration": "ironing_robot", "custom_component": "yes"},
        ),
        ("openpeerpower.helpers.network", {"helpers": "network"}),
        ("tuyapi.test", {"package": "tuyapi"}),
    ],
)
async def test_logger_event_extraction.opp: OpenPeerPower, logger, tags):
    """Test extraction of information from Sentry logger events."""

    result = process_before_send(
        opp,
        options={
            CONF_EVENT_CUSTOM_COMPONENTS: True,
            CONF_EVENT_THIRD_PARTY_PACKAGES: True,
        },
        channel="test",
        huuid="12345",
        system_info={"installation_type": "pytest"},
        custom_components=["ironing_robot"],
        event={"logger": logger},
        hint={},
    )

    assert result
    assert result["tags"] == {
        "channel": "test",
        "uuid": "12345",
        "installation_type": "pytest",
        **tags,
    }


@pytest.mark.parametrize(
    "logger,options,event",
    [
        ("adguard", {CONF_EVENT_THIRD_PARTY_PACKAGES: True}, True),
        ("adguard", {CONF_EVENT_THIRD_PARTY_PACKAGES: False}, False),
        (
            "openpeerpower.components.ironing_robot.switch",
            {CONF_EVENT_CUSTOM_COMPONENTS: True},
            True,
        ),
        (
            "openpeerpower.components.ironing_robot.switch",
            {CONF_EVENT_CUSTOM_COMPONENTS: False},
            False,
        ),
    ],
)
async def test_filter_log_events.opp: OpenPeerPower, logger, options, event):
    """Test filtering of events based on configuration options."""
    result = process_before_send(
        opp,
        options=options,
        channel="test",
        huuid="12345",
        system_info={"installation_type": "pytest"},
        custom_components=["ironing_robot"],
        event={"logger": logger},
        hint={},
    )

    if event:
        assert result
    else:
        assert result is None


@pytest.mark.parametrize(
    "handled,options,event",
    [
        ("yes", {CONF_EVENT_HANDLED: True}, True),
        ("yes", {CONF_EVENT_HANDLED: False}, False),
        ("no", {CONF_EVENT_HANDLED: False}, True),
        ("no", {CONF_EVENT_HANDLED: True}, True),
    ],
)
async def test_filter_handled_events.opp: OpenPeerPower, handled, options, event):
    """Tests filtering of handled events based on configuration options."""

    event_mock = MagicMock()
    event_mock.__iter__ = ["tags"]
    event_mock.__contains__ = lambda _, val: val == "tags"
    event_mock.tags = {"handled": handled}

    result = process_before_send(
        opp,
        options=options,
        channel="test",
        huuid="12345",
        system_info={"installation_type": "pytest"},
        custom_components=[],
        event=event_mock,
        hint={},
    )

    if event:
        assert result
    else:
        assert result is None
