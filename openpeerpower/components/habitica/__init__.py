"""The habitica integration."""
import asyncio
import logging

from habitipy.aio import HabitipyAsync
import voluptuous as vol

from openpeerpower import config_entries
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import (
    ATTR_NAME,
    CONF_API_KEY,
    CONF_NAME,
    CONF_SENSORS,
    CONF_URL,
)
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers import config_validation as cv
from openpeerpower.helpers.aiohttp_client import async_get_clientsession

from .const import (
    ATTR_ARGS,
    ATTR_PATH,
    CONF_API_USER,
    DEFAULT_URL,
    DOMAIN,
    EVENT_API_CALL_SUCCESS,
    SERVICE_API_CALL,
)
from .sensor import SENSORS_TYPES

_LOGGER = logging.getLogger(__name__)

INSTANCE_SCHEMA = vol.All(
    cv.deprecated(CONF_SENSORS),
    vol.Schema(
        {
            vol.Optional(CONF_URL, default=DEFAULT_URL): cv.url,
            vol.Optional(CONF_NAME): cv.string,
            vol.Required(CONF_API_USER): cv.string,
            vol.Required(CONF_API_KEY): cv.string,
            vol.Optional(CONF_SENSORS, default=list(SENSORS_TYPES)): vol.All(
                cv.ensure_list, vol.Unique(), [vol.In(list(SENSORS_TYPES))]
            ),
        }
    ),
)

has_unique_values = vol.Schema(vol.Unique())
# because we want a handy alias


def has_all_unique_users(value):
    """Validate that all API users are unique."""
    api_users = [user[CONF_API_USER] for user in value]
    has_unique_values(api_users)
    return value


def has_all_unique_users_names(value):
    """Validate that all user's names are unique and set if any is set."""
    names = [user.get(CONF_NAME) for user in value]
    if None in names and any(name is not None for name in names):
        raise vol.Invalid("user names of all users must be set if any is set")
    if not all(name is None for name in names):
        has_unique_values(names)
    return value


INSTANCE_LIST_SCHEMA = vol.All(
    cv.ensure_list, has_all_unique_users, has_all_unique_users_names, [INSTANCE_SCHEMA]
)
CONFIG_SCHEMA = vol.Schema({DOMAIN: INSTANCE_LIST_SCHEMA}, extra=vol.ALLOW_EXTRA)

PLATFORMS = ["sensor"]

SERVICE_API_CALL_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_NAME): str,
        vol.Required(ATTR_PATH): vol.All(cv.ensure_list, [str]),
        vol.Optional(ATTR_ARGS): dict,
    }
)


async def async_setup(opp: OpenPeerPower, config: dict) -> bool:
    """Set up the Habitica service."""
    configs = config.get(DOMAIN, [])

    for conf in configs:
        if conf.get(CONF_URL) is None:
            conf[CONF_URL] = DEFAULT_URL

        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data=conf
            )
        )

    return True


async def async_setup_entry(opp: OpenPeerPower, config_entry: ConfigEntry) -> bool:
    """Set up habitica from a config entry."""

    class HAHabitipyAsync(HabitipyAsync):
        """Closure API class to hold session."""

        def __call__(self, **kwargs):
            return super().__call__(websession, **kwargs)

    async def handle_api_call(call):
        name = call.data[ATTR_NAME]
        path = call.data[ATTR_PATH]
        api = opp.data[DOMAIN].get(name)
        if api is None:
            _LOGGER.error("API_CALL: User '%s' not configured", name)
            return
        try:
            for element in path:
                api = api[element]
        except KeyError:
            _LOGGER.error(
                "API_CALL: Path %s is invalid for API on '{%s}' element", path, element
            )
            return
        kwargs = call.data.get(ATTR_ARGS, {})
        data = await api(**kwargs)
        opp.bus.async_fire(
            EVENT_API_CALL_SUCCESS, {"name": name, "path": path, "data": data}
        )

    data = opp.data.setdefault(DOMAIN, {})
    config = config_entry.data
    websession = async_get_clientsession(opp)
    url = config[CONF_URL]
    username = config[CONF_API_USER]
    password = config[CONF_API_KEY]
    name = config.get(CONF_NAME)
    config_dict = {"url": url, "login": username, "password": password}
    api = HAHabitipyAsync(config_dict)
    user = await api.user.get()
    if name is None:
        name = user["profile"]["name"]
        opp.config_entries.async_update_entry(
            config_entry,
            data={**config_entry.data, CONF_NAME: name},
        )
    data[config_entry.entry_id] = api

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    if not opp.services.has_service(DOMAIN, SERVICE_API_CALL):
        opp.services.async_register(
            DOMAIN, SERVICE_API_CALL, handle_api_call, schema=SERVICE_API_CALL_SCHEMA
        )

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    if len(opp.config_entries.async_entries(DOMAIN)) == 1:
        opp.services.async_remove(DOMAIN, SERVICE_API_CALL)
    return unload_ok
