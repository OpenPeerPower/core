"""The Network Configuration integration."""
from __future__ import annotations

import logging

import voluptuous as vol

from openpeerpower.components import websocket_api
from openpeerpower.components.websocket_api.connection import ActiveConnection
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.typing import ConfigType
from openpeerpower.loader import bind_opp

from .const import (
    ATTR_ADAPTERS,
    ATTR_CONFIGURED_ADAPTERS,
    DOMAIN,
    NETWORK_CONFIG_SCHEMA,
)
from .models import Adapter
from .network import Network

ZEROCONF_DOMAIN = "zeroconf"  # cannot import from zeroconf due to circular dep
_LOGGER = logging.getLogger(__name__)


@bind_opp
async def async_get_adapters(opp: OpenPeerPower) -> list[Adapter]:
    """Get the network adapter configuration."""
    network: Network = opp.data[DOMAIN]
    return network.adapters


async def async_setup(opp: OpenPeerPower, config: ConfigType) -> bool:
    """Set up network for Open Peer Power."""

    opp.data[DOMAIN] = network = Network(opp)
    await network.async_setup()
    if ZEROCONF_DOMAIN in config:
        await network.async_migrate_from_zeroconf(config[ZEROCONF_DOMAIN])
    network.async_configure()

    _LOGGER.debug("Adapters: %s", network.adapters)

    websocket_api.async_register_command(opp, websocket_network_adapters)
    websocket_api.async_register_command(opp, websocket_network_adapters_configure)

    return True


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "network"})
@websocket_api.async_response
async def websocket_network_adapters(
    opp: OpenPeerPower,
    connection: ActiveConnection,
    msg: dict,
) -> None:
    """Return network preferences."""
    network: Network = opp.data[DOMAIN]
    connection.send_result(
        msg["id"],
        {
            ATTR_ADAPTERS: network.adapters,
            ATTR_CONFIGURED_ADAPTERS: network.configured_adapters,
        },
    )


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "network/configure",
        vol.Required("config", default={}): NETWORK_CONFIG_SCHEMA,
    }
)
@websocket_api.async_response
async def websocket_network_adapters_configure(
    opp: OpenPeerPower,
    connection: ActiveConnection,
    msg: dict,
) -> None:
    """Update network config."""
    network: Network = opp.data[DOMAIN]

    await network.async_reconfig(msg["config"])

    connection.send_result(
        msg["id"],
        {ATTR_CONFIGURED_ADAPTERS: network.configured_adapters},
    )
