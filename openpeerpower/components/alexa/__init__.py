"""Support for Alexa skill service end point."""
import voluptuous as vol

from openpeerpower.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_DESCRIPTION,
    CONF_NAME,
    CONF_PASSWORD,
)
from openpeerpower.helpers import config_validation as cv, entityfilter

from . import flash_briefings, intent, smart_home_http
from .const import (
    CONF_AUDIO,
    CONF_DISPLAY_CATEGORIES,
    CONF_DISPLAY_URL,
    CONF_ENDPOINT,
    CONF_ENTITY_CONFIG,
    CONF_FILTER,
    CONF_LOCALE,
    CONF_SUPPORTED_LOCALES,
    CONF_TEXT,
    CONF_TITLE,
    CONF_UID,
    DOMAIN,
)

CONF_FLASH_BRIEFINGS = "flash_briefings"
CONF_SMART_HOME = "smart_home"
DEFAULT_LOCALE = "en-US"

ALEXA_ENTITY_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_DESCRIPTION): cv.string,
        vol.Optional(CONF_DISPLAY_CATEGORIES): cv.string,
        vol.Optional(CONF_NAME): cv.string,
    }
)

SMART_HOME_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_ENDPOINT): cv.string,
        vol.Optional(CONF_CLIENT_ID): cv.string,
        vol.Optional(CONF_CLIENT_SECRET): cv.string,
        vol.Optional(CONF_LOCALE, default=DEFAULT_LOCALE): vol.In(
            CONF_SUPPORTED_LOCALES
        ),
        vol.Optional(CONF_FILTER, default={}): entityfilter.FILTER_SCHEMA,
        vol.Optional(CONF_ENTITY_CONFIG): {cv.entity_id: ALEXA_ENTITY_SCHEMA},
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: {
            CONF_FLASH_BRIEFINGS: {
                vol.Required(CONF_PASSWORD): cv.string,
                cv.string: vol.All(
                    cv.ensure_list,
                    [
                        {
                            vol.Optional(CONF_UID): cv.string,
                            vol.Required(CONF_TITLE): cv.template,
                            vol.Optional(CONF_AUDIO): cv.template,
                            vol.Required(CONF_TEXT, default=""): cv.template,
                            vol.Optional(CONF_DISPLAY_URL): cv.template,
                        }
                    ],
                ),
            },
            # vol.Optional here would mean we couldn't distinguish between an empty
            # smart_home: and none at all.
            CONF_SMART_HOME: vol.Any(SMART_HOME_SCHEMA, None),
        }
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Activate the Alexa component."""
    if DOMAIN not in config:
        return True

    config = config[DOMAIN]

    flash_briefings_config = config.get(CONF_FLASH_BRIEFINGS)

    intent.async_setup(opp)

    if flash_briefings_config:
        flash_briefings.async_setup(opp, flash_briefings_config)

    try:
        smart_home_config = config[CONF_SMART_HOME]
    except KeyError:
        pass
    else:
        smart_home_config = smart_home_config or SMART_HOME_SCHEMA({})
        await smart_home_http.async_setup(opp, smart_home_config)

    return True
