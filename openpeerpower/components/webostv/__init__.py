"""Support for LG webOS Smart TV."""
import asyncio
from contextlib import suppress
import json
import logging
import os

from aiopylgtv import PyLGTVCmdException, PyLGTVPairException, WebOsClient
from sqlitedict import SqliteDict
import voluptuous as vol
from websockets.exceptions import ConnectionClosed

from openpeerpower.const import (
    ATTR_COMMAND,
    ATTR_ENTITY_ID,
    CONF_CUSTOMIZE,
    CONF_HOST,
    CONF_ICON,
    CONF_NAME,
    EVENT_OPENPEERPOWER_STOP,
)
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.dispatcher import async_dispatcher_send

from .const import (
    ATTR_BUTTON,
    ATTR_PAYLOAD,
    ATTR_SOUND_OUTPUT,
    CONF_ON_ACTION,
    CONF_SOURCES,
    DEFAULT_NAME,
    DOMAIN,
    SERVICE_BUTTON,
    SERVICE_COMMAND,
    SERVICE_SELECT_SOUND_OUTPUT,
    WEBOSTV_CONFIG_FILE,
)

CUSTOMIZE_SCHEMA = vol.Schema(
    {vol.Optional(CONF_SOURCES, default=[]): vol.All(cv.ensure_list, [cv.string])}
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            cv.ensure_list,
            [
                vol.Schema(
                    {
                        vol.Optional(CONF_CUSTOMIZE, default={}): CUSTOMIZE_SCHEMA,
                        vol.Required(CONF_HOST): cv.string,
                        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                        vol.Optional(CONF_ON_ACTION): cv.SCRIPT_SCHEMA,
                        vol.Optional(CONF_ICON): cv.string,
                    }
                )
            ],
        )
    },
    extra=vol.ALLOW_EXTRA,
)

CALL_SCHEMA = vol.Schema({vol.Required(ATTR_ENTITY_ID): cv.comp_entity_ids})

BUTTON_SCHEMA = CALL_SCHEMA.extend({vol.Required(ATTR_BUTTON): cv.string})

COMMAND_SCHEMA = CALL_SCHEMA.extend(
    {vol.Required(ATTR_COMMAND): cv.string, vol.Optional(ATTR_PAYLOAD): dict}
)

SOUND_OUTPUT_SCHEMA = CALL_SCHEMA.extend({vol.Required(ATTR_SOUND_OUTPUT): cv.string})

SERVICE_TO_METHOD = {
    SERVICE_BUTTON: {"method": "async_button", "schema": BUTTON_SCHEMA},
    SERVICE_COMMAND: {"method": "async_command", "schema": COMMAND_SCHEMA},
    SERVICE_SELECT_SOUND_OUTPUT: {
        "method": "async_select_sound_output",
        "schema": SOUND_OUTPUT_SCHEMA,
    },
}

_LOGGER = logging.getLogger(__name__)


async def async_setup(opp, config):
    """Set up the LG WebOS TV platform."""
    opp.data[DOMAIN] = {}

    async def async_service_handler(service):
        method = SERVICE_TO_METHOD.get(service.service)
        data = service.data.copy()
        data["method"] = method["method"]
        async_dispatcher_send(opp, DOMAIN, data)

    for service in SERVICE_TO_METHOD:
        schema = SERVICE_TO_METHOD[service]["schema"]
        opp.services.async_register(
            DOMAIN, service, async_service_handler, schema=schema
        )

    tasks = [async_setup_tv(opp, config, conf) for conf in config[DOMAIN]]
    if tasks:
        await asyncio.gather(*tasks)

    return True


def convert_client_keys(config_file):
    """In case the config file contains JSON, convert it to a Sqlite config file."""
    # Return early if config file is non-existing
    if not os.path.isfile(config_file):
        return

    # Try to parse the file as being JSON
    with open(config_file) as json_file:
        try:
            json_conf = json.load(json_file)
        except (json.JSONDecodeError, UnicodeDecodeError):
            json_conf = None

    # If the file contains JSON, convert it to an Sqlite DB
    if json_conf:
        _LOGGER.warning("LG webOS TV client-key file is being migrated to Sqlite!")

        # Clean the JSON file
        os.remove(config_file)

        # Write the data to the Sqlite DB
        with SqliteDict(config_file) as conf:
            for host, key in json_conf.items():
                conf[host] = key
            conf.commit()


async def async_setup_tv(opp, config, conf):
    """Set up a LG WebOS TV based on host parameter."""

    host = conf[CONF_HOST]
    config_file = opp.config.path(WEBOSTV_CONFIG_FILE)
    await opp.async_add_executor_job(convert_client_keys, config_file)

    client = await WebOsClient.create(host, config_file)
    opp.data[DOMAIN][host] = {"client": client}

    if client.is_registered():
        await async_setup_tv_finalize(opp, config, conf, client)
    else:
        _LOGGER.warning("LG webOS TV %s needs to be paired", host)
        await async_request_configuration(opp, config, conf, client)


async def async_connect(client):
    """Attempt a connection, but fail gracefully if tv is off for example."""
    with suppress(
        OSError,
        ConnectionClosed,
        ConnectionRefusedError,
        asyncio.TimeoutError,
        asyncio.CancelledError,
        PyLGTVPairException,
        PyLGTVCmdException,
    ):
        await client.connect()


async def async_setup_tv_finalize(opp, config, conf, client):
    """Make initial connection attempt and call platform setup."""

    async def async_on_stop(event):
        """Unregister callbacks and disconnect."""
        client.clear_state_update_callbacks()
        await client.disconnect()

    opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, async_on_stop)

    await async_connect(client)
    opp.async_create_task(
        opp.helpers.discovery.async_load_platform("media_player", DOMAIN, conf, config)
    )
    opp.async_create_task(
        opp.helpers.discovery.async_load_platform("notify", DOMAIN, conf, config)
    )


async def async_request_configuration(opp, config, conf, client):
    """Request configuration steps from the user."""
    host = conf.get(CONF_HOST)
    name = conf.get(CONF_NAME)
    configurator = opp.components.configurator

    async def lgtv_configuration_callback(data):
        """Handle actions when configuration callback is called."""
        try:
            await client.connect()
        except PyLGTVPairException:
            _LOGGER.warning("Connected to LG webOS TV %s but not paired", host)
            return
        except (
            OSError,
            ConnectionClosed,
            ConnectionRefusedError,
            asyncio.TimeoutError,
            asyncio.CancelledError,
            PyLGTVCmdException,
        ):
            _LOGGER.error("Unable to connect to host %s", host)
            return

        await async_setup_tv_finalize(opp, config, conf, client)
        configurator.async_request_done(request_id)

    request_id = configurator.async_request_config(
        name,
        lgtv_configuration_callback,
        description="Click start and accept the pairing request on your TV.",
        description_image="/static/images/config_webos.png",
        submit_caption="Start pairing request",
    )
