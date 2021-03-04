"""Support to send data to a Splunk instance."""
import asyncio
import json
import logging
import time

from aiohttp import ClientConnectionError, ClientResponseError
from opp_splunk import SplunkPayloadError, opp_splunk
import voluptuous as vol

from openpeerpower.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_SSL,
    CONF_TOKEN,
    CONF_VERIFY_SSL,
    EVENT_STATE_CHANGED,
)
from openpeerpower.helpers import state as state_helper
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.entityfilter import FILTER_SCHEMA
from openpeerpower.helpers.json import JSONEncoder

_LOGGER = logging.getLogger(__name__)

DOMAIN = "splunk"
CONF_FILTER = "filter"

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8088
DEFAULT_SSL = False
DEFAULT_NAME = "OPP"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_TOKEN): cv.string,
                vol.Optional(CONF_HOST, default=DEFAULT_HOST): cv.string,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
                vol.Optional(CONF_SSL, default=False): cv.boolean,
                vol.Optional(CONF_VERIFY_SSL, default=True): cv.boolean,
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                vol.Optional(CONF_FILTER, default={}): FILTER_SCHEMA,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp, config):
    """Set up the Splunk component."""
    conf = config[DOMAIN]
    host = conf.get(CONF_HOST)
    port = conf.get(CONF_PORT)
    token = conf.get(CONF_TOKEN)
    use_ssl = conf[CONF_SSL]
    verify_ssl = conf.get(CONF_VERIFY_SSL)
    name = conf.get(CONF_NAME)
    entity_filter = conf[CONF_FILTER]

    event_collector = opp_splunk(
        session=async_get_clientsession(opp),
        host=host,
        port=port,
        token=token,
        use_ssl=use_ssl,
        verify_ssl=verify_ssl,
    )

    if not await event_collector.check(connectivity=False, token=True, busy=False):
        return False

    payload = {
        "time": time.time(),
        "host": name,
        "event": {
            "domain": DOMAIN,
            "meta": "Splunk integration has started",
        },
    }

    await event_collector.queue(json.dumps(payload, cls=JSONEncoder), send=False)

    async def splunk_event_listener(event):
        """Listen for new messages on the bus and sends them to Splunk."""

        state = event.data.get("new_state")
        if state is None or not entity_filter(state.entity_id):
            return

        try:
            _state = state_helper.state_as_number(state)
        except ValueError:
            _state = state.state

        payload = {
            "time": event.time_fired.timestamp(),
            "host": name,
            "event": {
                "domain": state.domain,
                "entity_id": state.object_id,
                "attributes": dict(state.attributes),
                "value": _state,
            },
        }

        try:
            await event_collector.queue(json.dumps(payload, cls=JSONEncoder), send=True)
        except SplunkPayloadError as err:
            if err.status == 401:
                _LOGGER.error(err)
            else:
                _LOGGER.warning(err)
        except ClientConnectionError as err:
            _LOGGER.warning(err)
        except asyncio.TimeoutError:
            _LOGGER.warning("Connection to %s:%s timed out", host, port)
        except ClientResponseError as err:
            _LOGGER.error(err.message)

    opp.bus.async_listen(EVENT_STATE_CHANGED, splunk_event_listener)

    return True
