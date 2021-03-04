"""Support for Logi Circle devices."""
import asyncio

from aiohttp.client_exceptions import ClientResponseError
import async_timeout
from logi_circle import LogiCircle
from logi_circle.exception import AuthorizationFailed
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.components.camera import ATTR_FILENAME, CAMERA_SERVICE_SCHEMA
from openpeerpower.const import (
    ATTR_MODE,
    CONF_API_KEY,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_MONITORED_CONDITIONS,
    CONF_SENSORS,
    EVENT_OPENPEERPOWER_STOP,
)
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.dispatcher import async_dispatcher_send

from . import config_flow
from .const import (
    CONF_REDIRECT_URI,
    DATA_LOGI,
    DEFAULT_CACHEDB,
    DOMAIN,
    LED_MODE_KEY,
    LOGI_SENSORS,
    RECORDING_MODE_KEY,
    SIGNAL_LOGI_CIRCLE_RECONFIGURE,
    SIGNAL_LOGI_CIRCLE_RECORD,
    SIGNAL_LOGI_CIRCLE_SNAPSHOT,
)

NOTIFICATION_ID = "logi_circle_notification"
NOTIFICATION_TITLE = "Logi Circle Setup"

_TIMEOUT = 15  # seconds

SERVICE_SET_CONFIG = "set_config"
SERVICE_LIVESTREAM_SNAPSHOT = "livestream_snapshot"
SERVICE_LIVESTREAM_RECORD = "livestream_record"

ATTR_VALUE = "value"
ATTR_DURATION = "duration"

PLATFORMS = ["camera", "sensor"]

SENSOR_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_MONITORED_CONDITIONS, default=list(LOGI_SENSORS)): vol.All(
            cv.ensure_list, [vol.In(LOGI_SENSORS)]
        )
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID): cv.string,
                vol.Required(CONF_CLIENT_SECRET): cv.string,
                vol.Required(CONF_API_KEY): cv.string,
                vol.Required(CONF_REDIRECT_URI): cv.string,
                vol.Optional(CONF_SENSORS, default={}): SENSOR_SCHEMA,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

LOGI_CIRCLE_SERVICE_SET_CONFIG = CAMERA_SERVICE_SCHEMA.extend(
    {
        vol.Required(ATTR_MODE): vol.In([LED_MODE_KEY, RECORDING_MODE_KEY]),
        vol.Required(ATTR_VALUE): cv.boolean,
    }
)

LOGI_CIRCLE_SERVICE_SNAPSHOT = CAMERA_SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_FILENAME): cv.template}
)

LOGI_CIRCLE_SERVICE_RECORD = CAMERA_SERVICE_SCHEMA.extend(
    {
        vol.Required(ATTR_FILENAME): cv.template,
        vol.Required(ATTR_DURATION): cv.positive_int,
    }
)


async def async_setup(opp, config):
    """Set up configured Logi Circle component."""
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]

    config_flow.register_flow_implementation(
        opp,
        DOMAIN,
        client_id=conf[CONF_CLIENT_ID],
        client_secret=conf[CONF_CLIENT_SECRET],
        api_key=conf[CONF_API_KEY],
        redirect_uri=conf[CONF_REDIRECT_URI],
        sensors=conf[CONF_SENSORS],
    )

    opp.async_create_task(
        opp.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}
        )
    )

    return True


async def async_setup_entry(opp, entry):
    """Set up Logi Circle from a config entry."""
    logi_circle = LogiCircle(
        client_id=entry.data[CONF_CLIENT_ID],
        client_secret=entry.data[CONF_CLIENT_SECRET],
        api_key=entry.data[CONF_API_KEY],
        redirect_uri=entry.data[CONF_REDIRECT_URI],
        cache_file=opp.config.path(DEFAULT_CACHEDB),
    )

    if not logi_circle.authorized:
        opp.components.persistent_notification.create(
            (
                f"Error: The cached access tokens are missing from {DEFAULT_CACHEDB}.<br />"
                f"Please unload then re-add the Logi Circle integration to resolve."
            ),
            title=NOTIFICATION_TITLE,
            notification_id=NOTIFICATION_ID,
        )
        return False

    try:
        with async_timeout.timeout(_TIMEOUT):
            # Ensure the cameras property returns the same Camera objects for
            # all devices. Performs implicit login and session validation.
            await logi_circle.synchronize_cameras()
    except AuthorizationFailed:
        opp.components.persistent_notification.create(
            "Error: Failed to obtain an access token from the cached "
            "refresh token.<br />"
            "Token may have expired or been revoked.<br />"
            "Please unload then re-add the Logi Circle integration to resolve",
            title=NOTIFICATION_TITLE,
            notification_id=NOTIFICATION_ID,
        )
        return False
    except asyncio.TimeoutError:
        # The TimeoutError exception object returns nothing when casted to a
        # string, so we'll handle it separately.
        err = f"{_TIMEOUT}s timeout exceeded when connecting to Logi Circle API"
        opp.components.persistent_notification.create(
            f"Error: {err}<br />You will need to restart opp after fixing.",
            title=NOTIFICATION_TITLE,
            notification_id=NOTIFICATION_ID,
        )
        return False
    except ClientResponseError as ex:
        opp.components.persistent_notification.create(
            f"Error: {ex}<br />You will need to restart opp after fixing.",
            title=NOTIFICATION_TITLE,
            notification_id=NOTIFICATION_ID,
        )
        return False

    opp.data[DATA_LOGI] = logi_circle

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    async def service_handler(service):
        """Dispatch service calls to target entities."""
        params = dict(service.data)

        if service.service == SERVICE_SET_CONFIG:
            async_dispatcher_send(opp, SIGNAL_LOGI_CIRCLE_RECONFIGURE, params)
        if service.service == SERVICE_LIVESTREAM_SNAPSHOT:
            async_dispatcher_send(opp, SIGNAL_LOGI_CIRCLE_SNAPSHOT, params)
        if service.service == SERVICE_LIVESTREAM_RECORD:
            async_dispatcher_send(opp, SIGNAL_LOGI_CIRCLE_RECORD, params)

    opp.services.async_register(
        DOMAIN,
        SERVICE_SET_CONFIG,
        service_handler,
        schema=LOGI_CIRCLE_SERVICE_SET_CONFIG,
    )

    opp.services.async_register(
        DOMAIN,
        SERVICE_LIVESTREAM_SNAPSHOT,
        service_handler,
        schema=LOGI_CIRCLE_SERVICE_SNAPSHOT,
    )

    opp.services.async_register(
        DOMAIN,
        SERVICE_LIVESTREAM_RECORD,
        service_handler,
        schema=LOGI_CIRCLE_SERVICE_RECORD,
    )

    async def shut_down(event=None):
        """Close Logi Circle aiohttp session."""
        await logi_circle.auth_provider.close()

    opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, shut_down)

    return True


async def async_unload_entry(opp, entry):
    """Unload a config entry."""
    for platform in PLATFORMS:
        await opp.config_entries.async_forward_entry_unload(entry, platform)

    logi_circle = opp.data.pop(DATA_LOGI)

    # Tell API wrapper to close all aiohttp sessions, invalidate WS connections
    # and clear all locally cached tokens
    await logi_circle.auth_provider.clear_authorization()

    return True
