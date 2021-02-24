"""Web socket API for Z-Wave."""
import voluptuous as vol

from openpeerpower.components import websocket_api
from openpeerpower.components.ozw.const import DOMAIN as OZW_DOMAIN
from openpeerpower.config_entries import SOURCE_IMPORT
from openpeerpower.core import callback

from .const import (
    CONF_AUTOHEAL,
    CONF_DEBUG,
    CONF_NETWORK_KEY,
    CONF_POLLING_INTERVAL,
    CONF_USB_STICK_PATH,
    DATA_NETWORK,
    DATA_ZWAVE_CONFIG,
)

TYPE = "type"
ID = "id"


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required(TYPE): "zwave/network_status"})
def websocket_network_status(opp, connection, msg):
    """Get Z-Wave network status."""
    network = opp.data[DATA_NETWORK]
    connection.send_result(msg[ID], {"state": network.state})


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required(TYPE): "zwave/get_config"})
def websocket_get_config(opp, connection, msg):
    """Get Z-Wave configuration."""
    config = opp.data[DATA_ZWAVE_CONFIG]
    connection.send_result(
        msg[ID],
        {
            CONF_AUTOHEAL: config[CONF_AUTOHEAL],
            CONF_DEBUG: config[CONF_DEBUG],
            CONF_POLLING_INTERVAL: config[CONF_POLLING_INTERVAL],
            CONF_USB_STICK_PATH: config[CONF_USB_STICK_PATH],
        },
    )


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required(TYPE): "zwave/get_migration_config"})
def websocket_get_migration_config(opp, connection, msg):
    """Get Z-Wave configuration for migration."""
    config = opp.data[DATA_ZWAVE_CONFIG]
    connection.send_result(
        msg[ID],
        {
            CONF_USB_STICK_PATH: config[CONF_USB_STICK_PATH],
            CONF_NETWORK_KEY: config[CONF_NETWORK_KEY],
        },
    )


@websocket_api.require_admin
@websocket_api.async_response
@websocket_api.websocket_command({vol.Required(TYPE): "zwave/start_ozw_config_flow"})
async def websocket_start_ozw_config_flow(opp, connection, msg):
    """Start the ozw integration config flow (for migration wizard).

    Return data with the flow id of the started ozw config flow.
    """
    config = opp.data[DATA_ZWAVE_CONFIG]
    data = {
        "usb_path": config[CONF_USB_STICK_PATH],
        "network_key": config[CONF_NETWORK_KEY],
    }
    result = await opp.config_entries.flow.async_init(
        OZW_DOMAIN, context={"source": SOURCE_IMPORT}, data=data
    )
    connection.send_result(
        msg[ID],
        {"flow_id": result["flow_id"]},
    )


@callback
def async_load_websocket_api(opp):
    """Set up the web socket API."""
    websocket_api.async_register_command(opp, websocket_network_status)
    websocket_api.async_register_command(opp, websocket_get_config)
    websocket_api.async_register_command(opp, websocket_get_migration_config)
    websocket_api.async_register_command(opp, websocket_start_ozw_config_flow)
