"""Component for handling Air Quality data for your location."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Final, final

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import (
    ATTR_ATTRIBUTION,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
)
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.config_validation import (  # noqa: F401
    PLATFORM_SCHEMA,
    PLATFORM_SCHEMA_BASE,
)
from openpeerpower.helpers.entity import Entity
from openpeerpower.helpers.entity_component import EntityComponent
from openpeerpower.helpers.typing import ConfigType, StateType

_LOGGER: Final = logging.getLogger(__name__)

ATTR_AQI: Final = "air_quality_index"
ATTR_CO2: Final = "carbon_dioxide"
ATTR_CO: Final = "carbon_monoxide"
ATTR_N2O: Final = "nitrogen_oxide"
ATTR_NO: Final = "nitrogen_monoxide"
ATTR_NO2: Final = "nitrogen_dioxide"
ATTR_OZONE: Final = "ozone"
ATTR_PM_0_1: Final = "particulate_matter_0_1"
ATTR_PM_10: Final = "particulate_matter_10"
ATTR_PM_2_5: Final = "particulate_matter_2_5"
ATTR_SO2: Final = "sulphur_dioxide"

DOMAIN: Final = "air_quality"

ENTITY_ID_FORMAT: Final = DOMAIN + ".{}"

SCAN_INTERVAL: Final = timedelta(seconds=30)

PROP_TO_ATTR: Final[dict[str, str]] = {
    "air_quality_index": ATTR_AQI,
    "attribution": ATTR_ATTRIBUTION,
    "carbon_dioxide": ATTR_CO2,
    "carbon_monoxide": ATTR_CO,
    "nitrogen_oxide": ATTR_N2O,
    "nitrogen_monoxide": ATTR_NO,
    "nitrogen_dioxide": ATTR_NO2,
    "ozone": ATTR_OZONE,
    "particulate_matter_0_1": ATTR_PM_0_1,
    "particulate_matter_10": ATTR_PM_10,
    "particulate_matter_2_5": ATTR_PM_2_5,
    "sulphur_dioxide": ATTR_SO2,
}


async def async_setup(opp: OpenPeerPower, config: ConfigType) -> bool:
    """Set up the air quality component."""
    component = opp.data[DOMAIN] = EntityComponent(
        _LOGGER, DOMAIN, opp, SCAN_INTERVAL
    )
    await component.async_setup(config)
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    component: EntityComponent = opp.data[DOMAIN]
    return await component.async_setup_entry(entry)


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    component: EntityComponent = opp.data[DOMAIN]
    return await component.async_unload_entry(entry)


class AirQualityEntity(Entity):
    """ABC for air quality data."""

    @property
    def particulate_matter_2_5(self) -> StateType:
        """Return the particulate matter 2.5 level."""
        raise NotImplementedError()

    @property
    def particulate_matter_10(self) -> StateType:
        """Return the particulate matter 10 level."""
        return None

    @property
    def particulate_matter_0_1(self) -> StateType:
        """Return the particulate matter 0.1 level."""
        return None

    @property
    def air_quality_index(self) -> StateType:
        """Return the Air Quality Index (AQI)."""
        return None

    @property
    def ozone(self) -> StateType:
        """Return the O3 (ozone) level."""
        return None

    @property
    def carbon_monoxide(self) -> StateType:
        """Return the CO (carbon monoxide) level."""
        return None

    @property
    def carbon_dioxide(self) -> StateType:
        """Return the CO2 (carbon dioxide) level."""
        return None

    @property
    def attribution(self) -> StateType:
        """Return the attribution."""
        return None

    @property
    def sulphur_dioxide(self) -> StateType:
        """Return the SO2 (sulphur dioxide) level."""
        return None

    @property
    def nitrogen_oxide(self) -> StateType:
        """Return the N2O (nitrogen oxide) level."""
        return None

    @property
    def nitrogen_monoxide(self) -> StateType:
        """Return the NO (nitrogen monoxide) level."""
        return None

    @property
    def nitrogen_dioxide(self) -> StateType:
        """Return the NO2 (nitrogen dioxide) level."""
        return None

    @final
    @property
    def state_attributes(self) -> dict[str, str | int | float]:
        """Return the state attributes."""
        data: dict[str, str | int | float] = {}

        for prop, attr in PROP_TO_ATTR.items():
            value = getattr(self, prop)
            if value is not None:
                data[attr] = value

        return data

    @property
    def state(self) -> StateType:
        """Return the current state."""
        return self.particulate_matter_2_5

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement of this entity."""
        return CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
