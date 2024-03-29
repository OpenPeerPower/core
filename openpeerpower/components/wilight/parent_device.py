"""The WiLight Device integration."""
import asyncio
import logging

import pywilight
import requests

from openpeerpower.const import CONF_HOST, EVENT_OPENPEERPOWER_STOP
from openpeerpower.core import callback
from openpeerpower.helpers.dispatcher import async_dispatcher_send

_LOGGER = logging.getLogger(__name__)


class WiLightParent:
    """Manages a single WiLight Parent Device."""

    def __init__(self, opp, config_entry):
        """Initialize the system."""
        self._host = config_entry.data[CONF_HOST]
        self._opp = opp
        self._api = None

    @property
    def host(self):
        """Return the host of this parent."""
        return self._host

    @property
    def api(self):
        """Return the api of this parent."""
        return self._api

    async def async_setup(self):
        """Set up a WiLight Parent Device based on host parameter."""
        host = self._host
        opp = self._opp

        api_device = await opp.async_add_executor_job(create_api_device, host)

        if api_device is None:
            return False

        @callback
        def disconnected():
            # Schedule reconnect after connection has been lost.
            _LOGGER.warning("WiLight %s disconnected", api_device.device_id)
            async_dispatcher_send(
                opp, f"wilight_device_available_{api_device.device_id}", False
            )

        @callback
        def reconnected():
            # Schedule reconnect after connection has been lost.
            _LOGGER.warning("WiLight %s reconnect", api_device.device_id)
            async_dispatcher_send(
                opp, f"wilight_device_available_{api_device.device_id}", True
            )

        async def connect(api_device):
            # Set up connection and hook it into OPP for reconnect/shutdown.
            _LOGGER.debug("Initiating connection to %s", api_device.device_id)

            client = await api_device.config_client(
                disconnect_callback=disconnected,
                reconnect_callback=reconnected,
                loop=asyncio.get_running_loop(),
                logger=_LOGGER,
            )

            # handle shutdown of WiLight asyncio transport
            opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, lambda x: client.stop())

            _LOGGER.info("Connected to WiLight device: %s", api_device.device_id)

        await connect(api_device)

        self._api = api_device

        return True

    async def async_reset(self):
        """Reset api."""

        # If the initialization was not wrong.
        if self._api is not None:
            self._api.client.stop()


def create_api_device(host):
    """Create an API Device."""
    try:
        device = pywilight.device_from_host(host)
    except (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
    ) as err:
        _LOGGER.error("Unable to access WiLight at %s (%s)", host, err)
        return None

    return device
