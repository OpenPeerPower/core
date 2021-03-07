"""Support to embed Plex."""
import asyncio
from functools import partial
import logging

import plexapi.exceptions
from plexapi.gdm import GDM
from plexwebsocket import (
    SIGNAL_CONNECTION_STATE,
    SIGNAL_DATA,
    STATE_CONNECTED,
    STATE_DISCONNECTED,
    STATE_STOPPED,
    PlexWebsocket,
)
import requests.exceptions

from openpeerpower.components.media_player import DOMAIN as MP_DOMAIN
from openpeerpower.config_entries import ENTRY_STATE_SETUP_RETRY, SOURCE_REAUTH
from openpeerpower.const import (
    CONF_SOURCE,
    CONF_URL,
    CONF_VERIFY_SSL,
    EVENT_OPENPEERPOWER_STOP,
)
from openpeerpower.core import callback
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.debounce import Debouncer
from openpeerpower.helpers.dispatcher import async_dispatcher_connect

from .const import (
    CONF_SERVER,
    CONF_SERVER_IDENTIFIER,
    DISPATCHERS,
    DOMAIN as PLEX_DOMAIN,
    GDM_DEBOUNCER,
    GDM_SCANNER,
    PLATFORMS,
    PLATFORMS_COMPLETED,
    PLEX_SERVER_CONFIG,
    PLEX_UPDATE_PLATFORMS_SIGNAL,
    SERVERS,
    WEBSOCKETS,
)
from .errors import ShouldUpdateConfigEntry
from .server import PlexServer
from .services import async_setup_services

_LOGGER = logging.getLogger(__package__)


async def async_setup(opp, config):
    """Set up the Plex component."""
    opp.data.setdefault(
        PLEX_DOMAIN,
        {SERVERS: {}, DISPATCHERS: {}, WEBSOCKETS: {}, PLATFORMS_COMPLETED: {}},
    )

    await async_setup_services(opp)

    gdm = opp.data[PLEX_DOMAIN][GDM_SCANNER] = GDM()

    opp.data[PLEX_DOMAIN][GDM_DEBOUNCER] = Debouncer(
        opp,
        _LOGGER,
        cooldown=10,
        immediate=True,
        function=partial(gdm.scan, scan_for_clients=True),
    ).async_call

    return True


async def async_setup_entry(opp, entry):
    """Set up Plex from a config entry."""
    server_config = entry.data[PLEX_SERVER_CONFIG]

    if entry.unique_id is None:
        opp.config_entries.async_update_entry(
            entry, unique_id=entry.data[CONF_SERVER_IDENTIFIER]
        )

    if MP_DOMAIN not in entry.options:
        options = dict(entry.options)
        options.setdefault(MP_DOMAIN, {})
        opp.config_entries.async_update_entry(entry, options=options)

    plex_server = PlexServer(
        opp,
        server_config,
        entry.data[CONF_SERVER_IDENTIFIER],
        entry.options,
        entry.entry_id,
    )
    try:
        await opp.async_add_executor_job(plex_server.connect)
    except ShouldUpdateConfigEntry:
        new_server_data = {
            **entry.data[PLEX_SERVER_CONFIG],
            CONF_URL: plex_server.url_in_use,
            CONF_SERVER: plex_server.friendly_name,
        }
        opp.config_entries.async_update_entry(
            entry, data={**entry.data, PLEX_SERVER_CONFIG: new_server_data}
        )
    except requests.exceptions.ConnectionError as error:
        if entry.state != ENTRY_STATE_SETUP_RETRY:
            _LOGGER.error(
                "Plex server (%s) could not be reached: [%s]",
                server_config[CONF_URL],
                error,
            )
        raise ConfigEntryNotReady from error
    except plexapi.exceptions.Unauthorized:
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                PLEX_DOMAIN,
                context={CONF_SOURCE: SOURCE_REAUTH},
                data=entry.data,
            )
        )
        _LOGGER.error(
            "Token not accepted, please reauthenticate Plex server '%s'",
            entry.data[CONF_SERVER],
        )
        return False
    except (
        plexapi.exceptions.BadRequest,
        plexapi.exceptions.NotFound,
    ) as error:
        _LOGGER.error(
            "Login to %s failed, verify token and SSL settings: [%s]",
            entry.data[CONF_SERVER],
            error,
        )
        return False

    _LOGGER.debug(
        "Connected to: %s (%s)", plex_server.friendly_name, plex_server.url_in_use
    )
    server_id = plex_server.machine_identifier
    opp.data[PLEX_DOMAIN][SERVERS][server_id] = plex_server
    opp.data[PLEX_DOMAIN][PLATFORMS_COMPLETED][server_id] = set()

    entry.add_update_listener(async_options_updated)

    async def async_update_plex():
        await opp.data[PLEX_DOMAIN][GDM_DEBOUNCER]()
        await plex_server.async_update_platforms()

    unsub = async_dispatcher_connect(
        opp,
        PLEX_UPDATE_PLATFORMS_SIGNAL.format(server_id),
        async_update_plex,
    )
    opp.data[PLEX_DOMAIN][DISPATCHERS].setdefault(server_id, [])
    opp.data[PLEX_DOMAIN][DISPATCHERS][server_id].append(unsub)

    @callback
    def plex_websocket_callback(signal, data, error):
        """Handle callbacks from plexwebsocket library."""
        if signal == SIGNAL_CONNECTION_STATE:

            if data == STATE_CONNECTED:
                _LOGGER.debug("Websocket to %s successful", entry.data[CONF_SERVER])
                opp.async_create_task(async_update_plex())
            elif data == STATE_DISCONNECTED:
                _LOGGER.debug(
                    "Websocket to %s disconnected, retrying", entry.data[CONF_SERVER]
                )
            # Stopped websockets without errors are expected during shutdown and ignored
            elif data == STATE_STOPPED and error:
                _LOGGER.error(
                    "Websocket to %s failed, aborting [Error: %s]",
                    entry.data[CONF_SERVER],
                    error,
                )
                opp.async_create_task(opp.config_entries.async_reload(entry.entry_id))

        elif signal == SIGNAL_DATA:
            opp.async_create_task(plex_server.async_update_session(data))

    session = async_get_clientsession(opp)
    verify_ssl = server_config.get(CONF_VERIFY_SSL)
    websocket = PlexWebsocket(
        plex_server.plex_server,
        plex_websocket_callback,
        session=session,
        verify_ssl=verify_ssl,
    )
    opp.data[PLEX_DOMAIN][WEBSOCKETS][server_id] = websocket

    def start_websocket_session(platform, _):
        opp.data[PLEX_DOMAIN][PLATFORMS_COMPLETED][server_id].add(platform)
        if opp.data[PLEX_DOMAIN][PLATFORMS_COMPLETED][server_id] == PLATFORMS:
            opp.loop.create_task(websocket.listen())

    def close_websocket_session(_):
        websocket.close()

    unsub = opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, close_websocket_session)
    opp.data[PLEX_DOMAIN][DISPATCHERS][server_id].append(unsub)

    for platform in PLATFORMS:
        task = opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )
        task.add_done_callback(partial(start_websocket_session, platform))

    def get_plex_account(plex_server):
        try:
            return plex_server.account
        except (plexapi.exceptions.BadRequest, plexapi.exceptions.Unauthorized):
            return None

    await opp.async_add_executor_job(get_plex_account, plex_server)

    return True


async def async_unload_entry(opp, entry):
    """Unload a config entry."""
    server_id = entry.data[CONF_SERVER_IDENTIFIER]

    websocket = opp.data[PLEX_DOMAIN][WEBSOCKETS].pop(server_id)
    websocket.close()

    dispatchers = opp.data[PLEX_DOMAIN][DISPATCHERS].pop(server_id)
    for unsub in dispatchers:
        unsub()

    tasks = [
        opp.config_entries.async_forward_entry_unload(entry, platform)
        for platform in PLATFORMS
    ]
    await asyncio.gather(*tasks)

    opp.data[PLEX_DOMAIN][SERVERS].pop(server_id)

    return True


async def async_options_updated(opp, entry):
    """Triggered by config entry options updates."""
    server_id = entry.data[CONF_SERVER_IDENTIFIER]

    # Guard incomplete setup during reauth flows
    if server_id in opp.data[PLEX_DOMAIN][SERVERS]:
        opp.data[PLEX_DOMAIN][SERVERS][server_id].options = entry.options
