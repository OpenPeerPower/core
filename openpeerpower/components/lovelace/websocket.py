"""Websocket API for Lovelace."""
from functools import wraps

import voluptuous as vol

from openpeerpower.components import websocket_api
from openpeerpower.core import callback
from openpeerpower.exceptions import OpenPeerPowerError
from openpeerpower.helpers import config_validation as cv

from .const import CONF_URL_PATH, DOMAIN, ConfigNotFound


def _handle_errors(func):
    """Handle error with WebSocket calls."""

    @wraps(func)
    async def send_with_error_handling(opp, connection, msg):
        url_path = msg.get(CONF_URL_PATH)
        config = opp.data[DOMAIN]["dashboards"].get(url_path)

        if config is None:
            connection.send_error(
                msg["id"], "config_not_found", f"Unknown config specified: {url_path}"
            )
            return

        error = None
        try:
            result = await func(opp, connection, msg, config)
        except ConfigNotFound:
            error = "config_not_found", "No config found."
        except OpenPeerPowerError as err:
            error = "error", str(err)

        if error is not None:
            connection.send_error(msg["id"], *error)
            return

        if msg is not None:
            await connection.send_big_result(msg["id"], result)
        else:
            connection.send_result(msg["id"], result)

    return send_with_error_handling


@websocket_api.async_response
@websocket_api.websocket_command({"type": "lovelace/resources"})
async def websocket_lovelace_resources(opp, connection, msg):
    """Send Lovelace UI resources over WebSocket configuration."""
    resources = opp.data[DOMAIN]["resources"]

    if not resources.loaded:
        await resources.async_load()
        resources.loaded = True

    connection.send_result(msg["id"], resources.async_items())


@websocket_api.async_response
@websocket_api.websocket_command(
    {
        "type": "lovelace/config",
        vol.Optional("force", default=False): bool,
        vol.Optional(CONF_URL_PATH): vol.Any(None, cv.string),
    }
)
@_handle_errors
async def websocket_lovelace_config(opp, connection, msg, config):
    """Send Lovelace UI config over WebSocket configuration."""
    return await config.async_load(msg["force"])


@websocket_api.require_admin
@websocket_api.async_response
@websocket_api.websocket_command(
    {
        "type": "lovelace/config/save",
        "config": vol.Any(str, dict),
        vol.Optional(CONF_URL_PATH): vol.Any(None, cv.string),
    }
)
@_handle_errors
async def websocket_lovelace_save_config(opp, connection, msg, config):
    """Save Lovelace UI configuration."""
    await config.async_save(msg["config"])


@websocket_api.require_admin
@websocket_api.async_response
@websocket_api.websocket_command(
    {
        "type": "lovelace/config/delete",
        vol.Optional(CONF_URL_PATH): vol.Any(None, cv.string),
    }
)
@_handle_errors
async def websocket_lovelace_delete_config(opp, connection, msg, config):
    """Delete Lovelace UI configuration."""
    await config.async_delete()


@websocket_api.websocket_command({"type": "lovelace/dashboards/list"})
@callback
def websocket_lovelace_dashboards(opp, connection, msg):
    """Delete Lovelace UI configuration."""
    connection.send_result(
        msg["id"],
        [
            dashboard.config
            for dashboard in opp.data[DOMAIN]["dashboards"].values()
            if dashboard.config
        ],
    )
