"""Template config validator."""
import logging

import voluptuous as vol

from openpeerpower.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from openpeerpower.components.sensor import DOMAIN as SENSOR_DOMAIN
from openpeerpower.config import async_log_exception, config_without_domain
from openpeerpower.const import CONF_BINARY_SENSORS, CONF_SENSORS, CONF_UNIQUE_ID
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.trigger import async_validate_trigger_config

from . import binary_sensor as binary_sensor_platform, sensor as sensor_platform
from .const import CONF_TRIGGER, DOMAIN

CONFIG_SECTION_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Optional(CONF_TRIGGER): cv.TRIGGER_SCHEMA,
        vol.Optional(SENSOR_DOMAIN): vol.All(
            cv.ensure_list, [sensor_platform.SENSOR_SCHEMA]
        ),
        vol.Optional(CONF_SENSORS): cv.schema_with_slug_keys(
            sensor_platform.LEGACY_SENSOR_SCHEMA
        ),
        vol.Optional(BINARY_SENSOR_DOMAIN): vol.All(
            cv.ensure_list, [binary_sensor_platform.BINARY_SENSOR_SCHEMA]
        ),
        vol.Optional(CONF_BINARY_SENSORS): cv.schema_with_slug_keys(
            binary_sensor_platform.LEGACY_BINARY_SENSOR_SCHEMA
        ),
    }
)


async def async_validate_config(opp, config):
    """Validate config."""
    if DOMAIN not in config:
        return config

    config_sections = []

    for cfg in cv.ensure_list(config[DOMAIN]):
        try:
            cfg = CONFIG_SECTION_SCHEMA(cfg)

            if CONF_TRIGGER in cfg:
                cfg[CONF_TRIGGER] = await async_validate_trigger_config(
                    opp, cfg[CONF_TRIGGER]
                )
        except vol.Invalid as err:
            async_log_exception(err, DOMAIN, cfg, opp)
            continue

        legacy_warn_printed = False

        for old_key, new_key, transform in (
            (
                CONF_SENSORS,
                SENSOR_DOMAIN,
                sensor_platform.rewrite_legacy_to_modern_conf,
            ),
            (
                CONF_BINARY_SENSORS,
                BINARY_SENSOR_DOMAIN,
                binary_sensor_platform.rewrite_legacy_to_modern_conf,
            ),
        ):
            if old_key not in cfg:
                continue

            if not legacy_warn_printed:
                legacy_warn_printed = True
                logging.getLogger(__name__).warning(
                    "The entity definition format under template: differs from the platform "
                    "configuration format. See "
                    "https://www.openpeerpower.io/integrations/template#configuration-for-trigger-based-template-sensors"
                )

            definitions = list(cfg[new_key]) if new_key in cfg else []
            definitions.extend(transform(cfg[old_key]))
            cfg = {**cfg, new_key: definitions}

        config_sections.append(cfg)

    # Create a copy of the configuration with all config for current
    # component removed and add validated config back in.
    config = config_without_domain(config, DOMAIN)
    config[DOMAIN] = config_sections

    return config
