"""Component to interface with an alarm control panel."""
from __future__ import annotations

from abc import abstractmethod
from datetime import timedelta
import logging
from typing import Any, Final, final

import voluptuous as vol

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import (
    ATTR_CODE,
    ATTR_CODE_FORMAT,
    SERVICE_ALARM_ARM_AWAY,
    SERVICE_ALARM_ARM_CUSTOM_BYPASS,
    SERVICE_ALARM_ARM_HOME,
    SERVICE_ALARM_ARM_NIGHT,
    SERVICE_ALARM_DISARM,
    SERVICE_ALARM_TRIGGER,
)
from openpeerpower.core import OpenPeerPower
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.config_validation import make_entity_service_schema
from openpeerpower.helpers.entity import Entity
from openpeerpower.helpers.entity_component import EntityComponent
from openpeerpower.helpers.typing import ConfigType

from .const import (
    SUPPORT_ALARM_ARM_AWAY,
    SUPPORT_ALARM_ARM_CUSTOM_BYPASS,
    SUPPORT_ALARM_ARM_HOME,
    SUPPORT_ALARM_ARM_NIGHT,
    SUPPORT_ALARM_TRIGGER,
)

_LOGGER: Final = logging.getLogger(__name__)

DOMAIN: Final = "alarm_control_panel"
SCAN_INTERVAL: Final = timedelta(seconds=30)
ATTR_CHANGED_BY: Final = "changed_by"
FORMAT_TEXT: Final = "text"
FORMAT_NUMBER: Final = "number"
ATTR_CODE_ARM_REQUIRED: Final = "code_arm_required"

ENTITY_ID_FORMAT: Final = DOMAIN + ".{}"

ALARM_SERVICE_SCHEMA: Final = make_entity_service_schema(
    {vol.Optional(ATTR_CODE): cv.string}
)

PLATFORM_SCHEMA: Final = cv.PLATFORM_SCHEMA
PLATFORM_SCHEMA_BASE: Final = cv.PLATFORM_SCHEMA_BASE


async def async_setup(opp: OpenPeerPower, config: ConfigType) -> bool:
    """Track states and offer events for sensors."""
    component = opp.data[DOMAIN] = EntityComponent(
        logging.getLogger(__name__), DOMAIN, opp, SCAN_INTERVAL
    )

    await component.async_setup(config)

    component.async_register_entity_service(
        SERVICE_ALARM_DISARM, ALARM_SERVICE_SCHEMA, "async_alarm_disarm"
    )
    component.async_register_entity_service(
        SERVICE_ALARM_ARM_HOME,
        ALARM_SERVICE_SCHEMA,
        "async_alarm_arm_home",
        [SUPPORT_ALARM_ARM_HOME],
    )
    component.async_register_entity_service(
        SERVICE_ALARM_ARM_AWAY,
        ALARM_SERVICE_SCHEMA,
        "async_alarm_arm_away",
        [SUPPORT_ALARM_ARM_AWAY],
    )
    component.async_register_entity_service(
        SERVICE_ALARM_ARM_NIGHT,
        ALARM_SERVICE_SCHEMA,
        "async_alarm_arm_night",
        [SUPPORT_ALARM_ARM_NIGHT],
    )
    component.async_register_entity_service(
        SERVICE_ALARM_ARM_CUSTOM_BYPASS,
        ALARM_SERVICE_SCHEMA,
        "async_alarm_arm_custom_bypass",
        [SUPPORT_ALARM_ARM_CUSTOM_BYPASS],
    )
    component.async_register_entity_service(
        SERVICE_ALARM_TRIGGER,
        ALARM_SERVICE_SCHEMA,
        "async_alarm_trigger",
        [SUPPORT_ALARM_TRIGGER],
    )

    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    component: EntityComponent = opp.data[DOMAIN]
    return await component.async_setup_entry(entry)


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    component: EntityComponent = opp.data[DOMAIN]
    return await component.async_unload_entry(entry)


class AlarmControlPanelEntity(Entity):
    """An abstract class for alarm control entities."""

    @property
    def code_format(self) -> str | None:
        """Regex for code format or None if no code is required."""
        return None

    @property
    def changed_by(self) -> str | None:
        """Last change triggered by."""
        return None

    @property
    def code_arm_required(self) -> bool:
        """Whether the code is required for arm actions."""
        return True

    def alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        raise NotImplementedError()

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        await self.opp.async_add_executor_job(self.alarm_disarm, code)

    def alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        raise NotImplementedError()

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        await self.opp.async_add_executor_job(self.alarm_arm_home, code)

    def alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        raise NotImplementedError()

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        await self.opp.async_add_executor_job(self.alarm_arm_away, code)

    def alarm_arm_night(self, code: str | None = None) -> None:
        """Send arm night command."""
        raise NotImplementedError()

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        """Send arm night command."""
        await self.opp.async_add_executor_job(self.alarm_arm_night, code)

    def alarm_trigger(self, code: str | None = None) -> None:
        """Send alarm trigger command."""
        raise NotImplementedError()

    async def async_alarm_trigger(self, code: str | None = None) -> None:
        """Send alarm trigger command."""
        await self.opp.async_add_executor_job(self.alarm_trigger, code)

    def alarm_arm_custom_bypass(self, code: str | None = None) -> None:
        """Send arm custom bypass command."""
        raise NotImplementedError()

    async def async_alarm_arm_custom_bypass(self, code: str | None = None) -> None:
        """Send arm custom bypass command."""
        await self.opp.async_add_executor_job(self.alarm_arm_custom_bypass, code)

    @property
    @abstractmethod
    def supported_features(self) -> int:
        """Return the list of supported features."""

    @final
    @property
    def state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes."""
        return {
            ATTR_CODE_FORMAT: self.code_format,
            ATTR_CHANGED_BY: self.changed_by,
            ATTR_CODE_ARM_REQUIRED: self.code_arm_required,
        }


class AlarmControlPanel(AlarmControlPanelEntity):
    """An abstract class for alarm control entities (for backwards compatibility)."""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Print deprecation warning."""
        super().__init_subclass__(**kwargs)  # type: ignore[call-arg]
        _LOGGER.warning(
            "AlarmControlPanel is deprecated, modify %s to extend AlarmControlPanelEntity",
            cls.__name__,
        )
