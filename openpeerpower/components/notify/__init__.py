"""Provides functionality to notify people."""
import asyncio
from functools import partial
import logging
from typing import Any, Dict, Optional, cast

import voluptuous as vol

import openpeerpower.components.persistent_notification as pn
from openpeerpower.const import CONF_NAME, CONF_PLATFORM
from openpeerpower.core import ServiceCall
from openpeerpower.exceptions import OpenPeerPowerError
from openpeerpower.helpers import config_per_platform, discovery
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.service import async_set_service_schema
from openpeerpower.helpers.typing import OpenPeerPowerType
from openpeerpower.loader import async_get_integration, bind_opp
from openpeerpower.setup import async_prepare_setup_platform
from openpeerpower.util import slugify
from openpeerpower.util.yaml import load_yaml

# mypy: allow-untyped-defs, no-check-untyped-defs

_LOGGER = logging.getLogger(__name__)

# Platform specific data
ATTR_DATA = "data"

# Text to notify user of
ATTR_MESSAGE = "message"

# Target of the notification (user, device, etc)
ATTR_TARGET = "target"

# Title of notification
ATTR_TITLE = "title"
ATTR_TITLE_DEFAULT = "Open Peer Power"

DOMAIN = "notify"

SERVICE_NOTIFY = "notify"
SERVICE_PERSISTENT_NOTIFICATION = "persistent_notification"

NOTIFY_SERVICES = "notify_services"

CONF_DESCRIPTION = "description"
CONF_FIELDS = "fields"

PLATFORM_SCHEMA = vol.Schema(
    {vol.Required(CONF_PLATFORM): cv.string, vol.Optional(CONF_NAME): cv.string},
    extra=vol.ALLOW_EXTRA,
)

NOTIFY_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_MESSAGE): cv.template,
        vol.Optional(ATTR_TITLE): cv.template,
        vol.Optional(ATTR_TARGET): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(ATTR_DATA): dict,
    }
)

PERSISTENT_NOTIFICATION_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_MESSAGE): cv.template,
        vol.Optional(ATTR_TITLE): cv.template,
    }
)


@bind_opp
async def async_reload(opp: OpenPeerPowerType, integration_name: str) -> None:
    """Register notify services for an integration."""
    if not _async_integration_has_notify_services(opp, integration_name):
        return

    tasks = [
        notify_service.async_register_services()
        for notify_service in opp.data[NOTIFY_SERVICES][integration_name]
    ]

    await asyncio.gather(*tasks)


@bind_opp
async def async_reset_platform(opp: OpenPeerPowerType, integration_name: str) -> None:
    """Unregister notify services for an integration."""
    if not _async_integration_has_notify_services(opp, integration_name):
        return

    tasks = [
        notify_service.async_unregister_services()
        for notify_service in opp.data[NOTIFY_SERVICES][integration_name]
    ]

    await asyncio.gather(*tasks)

    del opp.data[NOTIFY_SERVICES][integration_name]


def _async_integration_has_notify_services(
    opp: OpenPeerPowerType, integration_name: str
) -> bool:
    """Determine if an integration has notify services registered."""
    if (
        NOTIFY_SERVICES not in opp.data
        or integration_name not in opp.data[NOTIFY_SERVICES]
    ):
        return False

    return True


class BaseNotificationService:
    """An abstract class for notification services."""

    opp: Optional[OpenPeerPowerType] = None
    # Name => target
    registered_targets: Dict[str, str]

    def send_message(self, message, **kwargs):
        """Send a message.

        kwargs can contain ATTR_TITLE to specify a title.
        """
        raise NotImplementedError()

    async def async_send_message(self, message: Any, **kwargs: Any) -> None:
        """Send a message.

        kwargs can contain ATTR_TITLE to specify a title.
        """
        await self.opp.async_add_executor_job(partial(self.send_message, message, **kwargs))  # type: ignore

    async def _async_notify_message_service(self, service: ServiceCall) -> None:
        """Handle sending notification message service calls."""
        kwargs = {}
        message = service.data[ATTR_MESSAGE]
        title = service.data.get(ATTR_TITLE)

        if title:
            title.opp = self.opp
            kwargs[ATTR_TITLE] = title.async_render(parse_result=False)

        if self.registered_targets.get(service.service) is not None:
            kwargs[ATTR_TARGET] = [self.registered_targets[service.service]]
        elif service.data.get(ATTR_TARGET) is not None:
            kwargs[ATTR_TARGET] = service.data.get(ATTR_TARGET)

        message.opp = self.opp
        kwargs[ATTR_MESSAGE] = message.async_render(parse_result=False)
        kwargs[ATTR_DATA] = service.data.get(ATTR_DATA)

        await self.async_send_message(**kwargs)

    async def async_setup(
        self,
        opp: OpenPeerPowerType,
        service_name: str,
        target_service_name_prefix: str,
    ) -> None:
        """Store the data for the notify service."""
        # pylint: disable=attribute-defined-outside-init
        self.opp = opp
        self._service_name = service_name
        self._target_service_name_prefix = target_service_name_prefix
        self.registered_targets = {}

        # Load service descriptions from notify/services.yaml
        integration = await async_get_integration(opp, DOMAIN)
        services_yaml = integration.file_path / "services.yaml"
        self.services_dict = cast(
            dict, await opp.async_add_executor_job(load_yaml, str(services_yaml))
        )

    async def async_register_services(self) -> None:
        """Create or update the notify services."""
        assert self.opp

        if hasattr(self, "targets"):
            stale_targets = set(self.registered_targets)

            # pylint: disable=no-member
            for name, target in self.targets.items():  # type: ignore
                target_name = slugify(f"{self._target_service_name_prefix}_{name}")
                if target_name in stale_targets:
                    stale_targets.remove(target_name)
                if (
                    target_name in self.registered_targets
                    and target == self.registered_targets[target_name]
                ):
                    continue
                self.registered_targets[target_name] = target
                self.opp.services.async_register(
                    DOMAIN,
                    target_name,
                    self._async_notify_message_service,
                    schema=NOTIFY_SERVICE_SCHEMA,
                )
                # Register the service description
                service_desc = {
                    CONF_NAME: f"Send a notification via {target_name}",
                    CONF_DESCRIPTION: f"Sends a notification message using the {target_name} integration.",
                    CONF_FIELDS: self.services_dict[SERVICE_NOTIFY][CONF_FIELDS],
                }
                async_set_service_schema(self.opp, DOMAIN, target_name, service_desc)

            for stale_target_name in stale_targets:
                del self.registered_targets[stale_target_name]
                self.opp.services.async_remove(
                    DOMAIN,
                    stale_target_name,
                )

        if self.opp.services.has_service(DOMAIN, self._service_name):
            return

        self.opp.services.async_register(
            DOMAIN,
            self._service_name,
            self._async_notify_message_service,
            schema=NOTIFY_SERVICE_SCHEMA,
        )

        # Register the service description
        service_desc = {
            CONF_NAME: f"Send a notification with {self._service_name}",
            CONF_DESCRIPTION: f"Sends a notification message using the {self._service_name} service.",
            CONF_FIELDS: self.services_dict[SERVICE_NOTIFY][CONF_FIELDS],
        }
        async_set_service_schema(self.opp, DOMAIN, self._service_name, service_desc)

    async def async_unregister_services(self) -> None:
        """Unregister the notify services."""
        assert self.opp

        if self.registered_targets:
            remove_targets = set(self.registered_targets)
            for remove_target_name in remove_targets:
                del self.registered_targets[remove_target_name]
                self.opp.services.async_remove(
                    DOMAIN,
                    remove_target_name,
                )

        if not self.opp.services.has_service(DOMAIN, self._service_name):
            return

        self.opp.services.async_remove(
            DOMAIN,
            self._service_name,
        )


async def async_setup(opp, config):
    """Set up the notify services."""
    opp.data.setdefault(NOTIFY_SERVICES, {})

    async def persistent_notification(service: ServiceCall) -> None:
        """Send notification via the built-in persistsent_notify integration."""
        payload = {}
        message = service.data[ATTR_MESSAGE]
        message.opp = opp
        payload[ATTR_MESSAGE] = message.async_render(parse_result=False)

        title = service.data.get(ATTR_TITLE)
        if title:
            title.opp = opp
            payload[ATTR_TITLE] = title.async_render(parse_result=False)

        await opp.services.async_call(
            pn.DOMAIN, pn.SERVICE_CREATE, payload, blocking=True
        )

    async def async_setup_platform(
        integration_name, p_config=None, discovery_info=None
    ):
        """Set up a notify platform."""
        if p_config is None:
            p_config = {}

        platform = await async_prepare_setup_platform(
            opp, config, DOMAIN, integration_name
        )

        if platform is None:
            _LOGGER.error("Unknown notification service specified")
            return

        _LOGGER.info("Setting up %s.%s", DOMAIN, integration_name)
        notify_service = None
        try:
            if hasattr(platform, "async_get_service"):
                notify_service = await platform.async_get_service(
                    opp, p_config, discovery_info
                )
            elif hasattr(platform, "get_service"):
                notify_service = await opp.async_add_executor_job(
                    platform.get_service, opp, p_config, discovery_info
                )
            else:
                raise OpenPeerPowerError("Invalid notify platform.")

            if notify_service is None:
                # Platforms can decide not to create a service based
                # on discovery data.
                if discovery_info is None:
                    _LOGGER.error(
                        "Failed to initialize notification service %s", integration_name
                    )
                return

        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Error setting up platform %s", integration_name)
            return

        if discovery_info is None:
            discovery_info = {}

        conf_name = p_config.get(CONF_NAME) or discovery_info.get(CONF_NAME)
        target_service_name_prefix = conf_name or integration_name
        service_name = slugify(conf_name or SERVICE_NOTIFY)

        await notify_service.async_setup(opp, service_name, target_service_name_prefix)
        await notify_service.async_register_services()

        opp.data[NOTIFY_SERVICES].setdefault(integration_name, []).append(
            notify_service
        )
        opp.config.components.add(f"{DOMAIN}.{integration_name}")

        return True

    opp.services.async_register(
        DOMAIN,
        SERVICE_PERSISTENT_NOTIFICATION,
        persistent_notification,
        schema=PERSISTENT_NOTIFICATION_SERVICE_SCHEMA,
    )

    setup_tasks = [
        asyncio.create_task(async_setup_platform(integration_name, p_config))
        for integration_name, p_config in config_per_platform(config, DOMAIN)
    ]

    if setup_tasks:
        await asyncio.wait(setup_tasks)

    async def async_platform_discovered(platform, info):
        """Handle for discovered platform."""
        await async_setup_platform(platform, discovery_info=info)

    discovery.async_listen_platform(opp, DOMAIN, async_platform_discovered)

    return True
