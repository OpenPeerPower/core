"""The buienradar integration."""
from __future__ import annotations

import logging

from openpeerpower.config_entries import SOURCE_IMPORT, ConfigEntry
from openpeerpower.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers import entity_registry
from openpeerpower.helpers.typing import ConfigType

from .const import (
    CONF_COUNTRY,
    CONF_DELTA,
    CONF_DIMENSION,
    CONF_TIMEFRAME,
    DEFAULT_COUNTRY,
    DEFAULT_DELTA,
    DEFAULT_DIMENSION,
    DEFAULT_TIMEFRAME,
    DOMAIN,
)

PLATFORMS = ["camera", "sensor", "weather"]

_LOGGER = logging.getLogger(__name__)


async def async_setup(opp: OpenPeerPower, config: ConfigType) -> bool:
    """Set up the buienradar component."""
    opp.data.setdefault(DOMAIN, {})

    weather_configs = _filter_domain_configs(config, "weather", DOMAIN)
    sensor_configs = _filter_domain_configs(config, "sensor", DOMAIN)
    camera_configs = _filter_domain_configs(config, "camera", DOMAIN)

    _import_configs(opp, weather_configs, sensor_configs, camera_configs)

    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up buienradar from a config entry."""
    opp.config_entries.async_setup_platforms(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)

    return unload_ok


async def async_update_options(opp: OpenPeerPower, config_entry: ConfigEntry) -> None:
    """Update options."""
    await opp.config_entries.async_reload(config_entry.entry_id)


def _import_configs(
    opp: OpenPeerPower,
    weather_configs: list[ConfigType],
    sensor_configs: list[ConfigType],
    camera_configs: list[ConfigType],
) -> None:
    camera_config = {}
    if camera_configs:
        camera_config = camera_configs[0]

    for config in sensor_configs:
        # Remove weather configurations which share lat/lon with sensor configurations
        matching_weather_config = None
        latitude = config.get(CONF_LATITUDE, opp.config.latitude)
        longitude = config.get(CONF_LONGITUDE, opp.config.longitude)
        for weather_config in weather_configs:
            weather_latitude = config.get(CONF_LATITUDE, opp.config.latitude)
            weather_longitude = config.get(CONF_LONGITUDE, opp.config.longitude)
            if latitude == weather_latitude and longitude == weather_longitude:
                matching_weather_config = weather_config
                break

        if matching_weather_config is not None:
            weather_configs.remove(matching_weather_config)

    configs = weather_configs + sensor_configs

    if not configs and camera_configs:
        config = {
            CONF_LATITUDE: opp.config.latitude,
            CONF_LONGITUDE: opp.config.longitude,
        }
        configs.append(config)

    if configs:
        _try_update_unique_id(opp, configs[0], camera_config)

    for config in configs:
        data = {
            CONF_LATITUDE: config.get(CONF_LATITUDE, opp.config.latitude),
            CONF_LONGITUDE: config.get(CONF_LONGITUDE, opp.config.longitude),
            CONF_TIMEFRAME: config.get(CONF_TIMEFRAME, DEFAULT_TIMEFRAME),
            CONF_COUNTRY: camera_config.get(CONF_COUNTRY, DEFAULT_COUNTRY),
            CONF_DELTA: camera_config.get(CONF_DELTA, DEFAULT_DELTA),
            CONF_NAME: config.get(CONF_NAME, "Buienradar"),
        }

        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=data,
            )
        )


def _try_update_unique_id(
    opp: OpenPeerPower, config: ConfigType, camera_config: ConfigType
) -> None:
    dimension = camera_config.get(CONF_DIMENSION, DEFAULT_DIMENSION)
    country = camera_config.get(CONF_COUNTRY, DEFAULT_COUNTRY)

    registry = entity_registry.async_get(opp)
    entity_id = registry.async_get_entity_id("camera", DOMAIN, f"{dimension}_{country}")

    if entity_id is not None:
        latitude = config[CONF_LATITUDE]
        longitude = config[CONF_LONGITUDE]

        new_unique_id = f"{latitude:2.6f}{longitude:2.6f}"
        registry.async_update_entity(entity_id, new_unique_id=new_unique_id)


def _filter_domain_configs(
    config: ConfigType, domain: str, platform: str
) -> list[ConfigType]:
    configs = []
    for entry in config:
        if entry.startswith(domain):
            configs += [x for x in config[entry] if x["platform"] == platform]
    return configs
