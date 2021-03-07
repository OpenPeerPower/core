"""Component to allow numeric input for platforms."""
from abc import abstractmethod
from datetime import timedelta
import logging
from typing import Any, Dict

import voluptuous as vol

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.helpers.config_validation import (  # noqa: F401
    PLATFORM_SCHEMA,
    PLATFORM_SCHEMA_BASE,
)
from openpeerpower.helpers.entity import Entity
from openpeerpower.helpers.entity_component import EntityComponent
from openpeerpower.helpers.typing import ConfigType, OpenPeerPowerType

from .const import (
    ATTR_MAX,
    ATTR_MIN,
    ATTR_STEP,
    ATTR_VALUE,
    DEFAULT_MAX_VALUE,
    DEFAULT_MIN_VALUE,
    DEFAULT_STEP,
    DOMAIN,
    SERVICE_SET_VALUE,
)

SCAN_INTERVAL = timedelta(seconds=30)

ENTITY_ID_FORMAT = DOMAIN + ".{}"

MIN_TIME_BETWEEN_SCANS = timedelta(seconds=10)

_LOGGER = logging.getLogger(__name__)


async def async_setup(opp: OpenPeerPowerType, config: ConfigType) -> bool:
    """Set up Number entities."""
    component = opp.data[DOMAIN] = EntityComponent(_LOGGER, DOMAIN, opp, SCAN_INTERVAL)
    await component.async_setup(config)

    component.async_register_entity_service(
        SERVICE_SET_VALUE,
        {vol.Required(ATTR_VALUE): vol.Coerce(float)},
        "async_set_value",
    )

    return True


async def async_setup_entry(opp: OpenPeerPowerType, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    return await opp.data[DOMAIN].async_setup_entry(entry)  # type: ignore


async def async_unload_entry(opp: OpenPeerPowerType, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await opp.data[DOMAIN].async_unload_entry(entry)  # type: ignore


class NumberEntity(Entity):
    """Representation of a Number entity."""

    @property
    def capability_attributes(self) -> Dict[str, Any]:
        """Return capability attributes."""
        return {
            ATTR_MIN: self.min_value,
            ATTR_MAX: self.max_value,
            ATTR_STEP: self.step,
        }

    @property
    def min_value(self) -> float:
        """Return the minimum value."""
        return DEFAULT_MIN_VALUE

    @property
    def max_value(self) -> float:
        """Return the maximum value."""
        return DEFAULT_MAX_VALUE

    @property
    def step(self) -> float:
        """Return the increment/decrement step."""
        step = DEFAULT_STEP
        value_range = abs(self.max_value - self.min_value)
        if value_range != 0:
            while value_range <= step:
                step /= 10.0
        return step

    @property
    def state(self) -> float:
        """Return the entity state."""
        return self.value

    @property
    @abstractmethod
    def value(self) -> float:
        """Return the entity value to represent the entity state."""

    def set_value(self, value: float) -> None:
        """Set new value."""
        raise NotImplementedError()

    async def async_set_value(self, value: float) -> None:
        """Set new value."""
        assert self.opp is not None
        await self.opp.async_add_executor_job(self.set_value, value)
