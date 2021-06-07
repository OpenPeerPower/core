"""The template component."""
from __future__ import annotations

import asyncio
import logging
from typing import Callable

from openpeerpower import config as conf_util
from openpeerpower.const import (
    CONF_UNIQUE_ID,
    EVENT_OPENPEERPOWER_START,
    SERVICE_RELOAD,
)
from openpeerpower.core import CoreState, Event, callback
from openpeerpower.exceptions import OpenPeerPowerError
from openpeerpower.helpers import (
    discovery,
    trigger as trigger_helper,
    update_coordinator,
)
from openpeerpower.helpers.reload import async_reload_integration_platforms
from openpeerpower.loader import async_get_integration

from .const import CONF_TRIGGER, DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


async def async_setup(opp, config):
    """Set up the template integration."""
    if DOMAIN in config:
        await _process_config(opp, config)

    async def _reload_config(call: Event) -> None:
        """Reload top-level + platforms."""
        try:
            unprocessed_conf = await conf_util.async_opp_config_yaml(opp)
        except OpenPeerPowerError as err:
            _LOGGER.error(err)
            return

        conf = await conf_util.async_process_component_config(
            opp, unprocessed_conf, await async_get_integration(opp, DOMAIN)
        )

        if conf is None:
            return

        await async_reload_integration_platforms(opp, DOMAIN, PLATFORMS)

        if DOMAIN in conf:
            await _process_config(opp, conf)

        opp.bus.async_fire(f"event_{DOMAIN}_reloaded", context=call.context)

    opp.helpers.service.async_register_admin_service(
        DOMAIN, SERVICE_RELOAD, _reload_config
    )

    return True


async def _process_config(opp, opp_config):
    """Process config."""
    coordinators: list[TriggerUpdateCoordinator] | None = opp.data.pop(DOMAIN, None)

    # Remove old ones
    if coordinators:
        for coordinator in coordinators:
            coordinator.async_remove()

    async def init_coordinator(opp, conf_section):
        coordinator = TriggerUpdateCoordinator(opp, conf_section)
        await coordinator.async_setup(opp_config)
        return coordinator

    coordinator_tasks = []

    for conf_section in opp_config[DOMAIN]:
        if CONF_TRIGGER in conf_section:
            coordinator_tasks.append(init_coordinator(opp, conf_section))
            continue

        for platform_domain in PLATFORMS:
            if platform_domain in conf_section:
                opp.async_create_task(
                    discovery.async_load_platform(
                        opp,
                        platform_domain,
                        DOMAIN,
                        {
                            "unique_id": conf_section.get(CONF_UNIQUE_ID),
                            "entities": conf_section[platform_domain],
                        },
                        opp_config,
                    )
                )

    if coordinator_tasks:
        opp.data[DOMAIN] = await asyncio.gather(*coordinator_tasks)


class TriggerUpdateCoordinator(update_coordinator.DataUpdateCoordinator):
    """Class to handle incoming data."""

    REMOVE_TRIGGER = object()

    def __init__(self, opp, config):
        """Instantiate trigger data."""
        super().__init__(opp, _LOGGER, name="Trigger Update Coordinator")
        self.config = config
        self._unsub_start: Callable[[], None] | None = None
        self._unsub_trigger: Callable[[], None] | None = None

    @property
    def unique_id(self) -> str | None:
        """Return unique ID for the entity."""
        return self.config.get("unique_id")

    @callback
    def async_remove(self):
        """Signal that the entities need to remove themselves."""
        if self._unsub_start:
            self._unsub_start()
        if self._unsub_trigger:
            self._unsub_trigger()

    async def async_setup(self, opp_config):
        """Set up the trigger and create entities."""
        if self.opp.state == CoreState.running:
            await self._attach_triggers()
        else:
            self._unsub_start = self.opp.bus.async_listen_once(
                EVENT_OPENPEERPOWER_START, self._attach_triggers
            )

        for platform_domain in PLATFORMS:
            if platform_domain in self.config:
                self.opp.async_create_task(
                    discovery.async_load_platform(
                        self.opp,
                        platform_domain,
                        DOMAIN,
                        {"coordinator": self, "entities": self.config[platform_domain]},
                        opp_config,
                    )
                )

    async def _attach_triggers(self, start_event=None) -> None:
        """Attach the triggers."""
        if start_event is not None:
            self._unsub_start = None

        self._unsub_trigger = await trigger_helper.async_initialize_triggers(
            self.opp,
            self.config[CONF_TRIGGER],
            self._handle_triggered,
            DOMAIN,
            self.name,
            self.logger.log,
            start_event is not None,
        )

    @callback
    def _handle_triggered(self, run_variables, context=None):
        self.async_set_updated_data(
            {"run_variables": run_variables, "context": context}
        )
