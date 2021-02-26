"""The sentry integration."""
import re
from typing import Dict, Union

import sentry_sdk
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import (
    EVENT_OPENPEERPOWER_STARTED,
    __version__ as current_version,
)
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers import config_validation as cv, entity_platform
from openpeerpower.loader import Integration, async_get_custom_components

from .const import (
    CONF_DSN,
    CONF_ENVIRONMENT,
    CONF_EVENT_CUSTOM_COMPONENTS,
    CONF_EVENT_HANDLED,
    CONF_EVENT_THIRD_PARTY_PACKAGES,
    CONF_LOGGING_EVENT_LEVEL,
    CONF_LOGGING_LEVEL,
    CONF_TRACING,
    CONF_TRACING_SAMPLE_RATE,
    DEFAULT_LOGGING_EVENT_LEVEL,
    DEFAULT_LOGGING_LEVEL,
    DEFAULT_TRACING_SAMPLE_RATE,
    DOMAIN,
    ENTITY_COMPONENTS,
)

CONFIG_SCHEMA = cv.deprecated(DOMAIN)


LOGGER_INFO_REGEX = re.compile(r"^(\w+)\.?(\w+)?\.?(\w+)?\.?(\w+)?(?:\..*)?$")


async def async_setup(opp: OpenPeerPower, config: dict) -> bool:
    """Set up the Sentry component."""
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up Sentry from a config entry."""

    # Migrate environment from config entry data to config entry options
    if (
        CONF_ENVIRONMENT not in entry.options
        and CONF_ENVIRONMENT in entry.data
        and entry.data[CONF_ENVIRONMENT]
    ):
        options = {**entry.options, CONF_ENVIRONMENT: entry.data[CONF_ENVIRONMENT]}
        data = entry.data.copy()
        data.pop(CONF_ENVIRONMENT)
        opp.config_entries.async_update_entry(entry, data=data, options=options)

    # https://docs.sentry.io/platforms/python/logging/
    sentry_logging = LoggingIntegration(
        level=entry.options.get(CONF_LOGGING_LEVEL, DEFAULT_LOGGING_LEVEL),
        event_level=entry.options.get(
            CONF_LOGGING_EVENT_LEVEL, DEFAULT_LOGGING_EVENT_LEVEL
        ),
    )

    # Additional/extra data collection
    channel = get_channel(current_version)
    huuid = await opp.helpers.instance_id.async_get()
    system_info = await opp.helpers.system_info.async_get_system_info()
    custom_components = await async_get_custom_components(opp)

    tracing = {}
    if entry.options.get(CONF_TRACING):
        tracing = {
            "traces_sample_rate": entry.options.get(
                CONF_TRACING_SAMPLE_RATE, DEFAULT_TRACING_SAMPLE_RATE
            ),
        }

    sentry_sdk.init(
        dsn=entry.data[CONF_DSN],
        environment=entry.options.get(CONF_ENVIRONMENT),
        integrations=[sentry_logging, AioHttpIntegration(), SqlalchemyIntegration()],
        release=current_version,
        before_send=lambda event, hint: process_before_send(
            opp,
            entry.options,
            channel,
            huuid,
            system_info,
            custom_components,
            event,
            hint,
        ),
        **tracing,
    )

    async def update_system_info(now):
        nonlocal system_info
        system_info = await opp.helpers.system_info.async_get_system_info()

        # Update system info every hour
        opp.helpers.event.async_call_later(3600, update_system_info)

    opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STARTED, update_system_info)

    return True


def get_channel(version: str) -> str:
    """Find channel based on version number."""
    if "dev0" in version:
        return "dev"
    if "dev" in version:
        return "nightly"
    if "b" in version:
        return "beta"
    return "stable"


def process_before_send(
    opp: OpenPeerPower,
    options,
    channel: str,
    huuid: str,
    system_info: Dict[str, Union[bool, str]],
    custom_components: Dict[str, Integration],
    event,
    hint,
):
    """Process a Sentry event before sending it to Sentry."""
    # Filter out handled events by default
    if (
        "tags" in event
        and event.tags.get("handled", "no") == "yes"
        and not options.get(CONF_EVENT_HANDLED)
    ):
        return None

    # Additional tags to add to the event
    additional_tags = {
        "channel": channel,
        "installation_type": system_info["installation_type"],
        "uuid": huuid,
    }

    # Find out all integrations in use, filter "auth", because it
    # triggers security rules, hiding all data.
    integrations = [
        integration
        for integration in opp.config.components
        if integration != "auth" and "." not in integration
    ]

    # Add additional tags based on what caused the event.
    platform = entity_platform.current_platform.get()
    if platform is not None:
        # This event happened in a platform
        additional_tags["custom_component"] = "no"
        additional_tags["integration"] = platform.platform_name
        additional_tags["platform"] = platform.domain
    elif "logger" in event:
        # Logger event, try to get integration information from the logger name.
        matches = LOGGER_INFO_REGEX.findall(event["logger"])
        if matches:
            group1, group2, group3, group4 = matches[0]
            # Handle the "openpeerpower." package differently
            if group1 == "openpeerpower" and group2 and group3:
                if group2 == "components":
                    # This logger is from a component
                    additional_tags["custom_component"] = "no"
                    additional_tags["integration"] = group3
                    if group4 and group4 in ENTITY_COMPONENTS:
                        additional_tags["platform"] = group4
                else:
                    # Not a component, could be helper, or something else.
                    additional_tags[group2] = group3
            else:
                # Not the "openpeerpower" package, this third-party
                if not options.get(CONF_EVENT_THIRD_PARTY_PACKAGES):
                    return None
                additional_tags["package"] = group1

    # If this event is caused by an integration, add a tag if this
    # integration is custom or not.
    if (
        "integration" in additional_tags
        and additional_tags["integration"] in custom_components
    ):
        if not options.get(CONF_EVENT_CUSTOM_COMPONENTS):
            return None
        additional_tags["custom_component"] = "yes"

    # Update event with the additional tags
    event.setdefault("tags", {}).update(additional_tags)

    # Set user context to the installation UUID
    event.setdefault("user", {}).update({"id": huuid})

    # Update event data with Open Peer Power Context
    event.setdefault("contexts", {}).update(
        {
            "Open Peer Power": {
                "channel": channel,
                "custom_components": "\n".join(sorted(custom_components)),
                "integrations": "\n".join(sorted(integrations)),
                **system_info,
            },
        }
    )
    return event
