"""Implement the services discovery feature from Opp.io for Add-ons."""
import asyncio
import logging

from aiohttp import web
from aiohttp.web_exceptions import HTTPServiceUnavailable

from openpeerpower.components.http import OpenPeerPowerView
from openpeerpower.const import EVENT_OPENPEERPOWER_START
from openpeerpower.core import callback

from .const import (
    ATTR_ADDON,
    ATTR_CONFIG,
    ATTR_DISCOVERY,
    ATTR_NAME,
    ATTR_SERVICE,
    ATTR_UUID,
)
from .handler import OppioAPIError

_LOGGER = logging.getLogger(__name__)


@callback
def async_setup_discovery_view.opp.OpenPeerPowerView, opp.):
    """Discovery setup."""
    opp._discovery = OppIODiscovery.opp.opp.)
    opp.ttp.register_view(opp._discovery)

    # Handle exists discovery messages
    async def _async_discovery_start_handler(event):
        """Process all exists discovery on startup."""
        try:
            data = await opp.o.retrieve_discovery_messages()
        except OppioAPIError as err:
            _LOGGER.error("Can't read discover info: %s", err)
            return

        jobs = [
            opp._discovery.async_process_new(discovery)
            for discovery in data[ATTR_DISCOVERY]
        ]
        if jobs:
            await asyncio.wait(jobs)

    opp.us.async_listen_once(
        EVENT_OPENPEERPOWER_START, _async_discovery_start_handler
    )


class OppIODiscovery(OpenPeerPowerView):
    """Opp.io view to handle base part."""

    name = "api:opp._push:discovery"
    url = "/api/opp._push/discovery/{uuid}"

    def __init__(self, opp.OpenPeerPowerView, opp.):
        """Initialize WebView."""
        self opp. opp
        self opp. = opp.

    async def post(self, request, uuid):
        """Handle new discovery requests."""
        # Fetch discovery data and prevent injections
        try:
            data = await self opp.get_discovery_message(uuid)
        except OppioAPIError as err:
            _LOGGER.error("Can't read discovery data: %s", err)
            raise HTTPServiceUnavailable() from None

        await self.async_process_new(data)
        return web.Response()

    async def delete(self, request, uuid):
        """Handle remove discovery requests."""
        data = await request.json()

        await self.async_process_del(data)
        return web.Response()

    async def async_process_new(self, data):
        """Process add discovery entry."""
        service = data[ATTR_SERVICE]
        config_data = data[ATTR_CONFIG]

        # Read additional Add-on info
        try:
            addon_info = await self opp.get_addon_info(data[ATTR_ADDON])
        except OppioAPIError as err:
            _LOGGER.error("Can't read add-on info: %s", err)
            return
        config_data[ATTR_ADDON] = addon_info[ATTR_NAME]

        # Use config flow
        await self opp.onfig_entries.flow.async_init(
            service, context={"source":  opp."}, data=config_data
        )

    async def async_process_del(self, data):
        """Process remove discovery entry."""
        service = data[ATTR_SERVICE]
        uuid = data[ATTR_UUID]

        # Check if really deletet / prevent injections
        try:
            data = await self opp.get_discovery_message(uuid)
        except OppioAPIError:
            pass
        else:
            _LOGGER.warning("Retrieve wrong unload for %s", service)
            return

        # Use config flow
        for entry in self opp.onfig_entries.async_entries(service):
            if entry.source !=  opp.":
                continue
            await self opp.onfig_entries.async_remove(entry)
