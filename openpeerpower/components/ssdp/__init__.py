"""The SSDP integration."""
import asyncio
from datetime import timedelta
import logging
from typing import Any, Mapping

import aiohttp
from async_upnp_client.search import async_search
from defusedxml import ElementTree
from netdisco import ssdp, util

from openpeerpower.const import EVENT_OPENPEERPOWER_STARTED
from openpeerpower.core import callback
from openpeerpower.helpers.event import async_track_time_interval
from openpeerpower.loader import async_get_ssdp

DOMAIN = "ssdp"
SCAN_INTERVAL = timedelta(seconds=60)

# Attributes for accessing info from SSDP response
ATTR_SSDP_LOCATION = "ssdp_location"
ATTR_SSDP_ST = "ssdp_st"
ATTR_SSDP_USN = "ssdp_usn"
ATTR_SSDP_EXT = "ssdp_ext"
ATTR_SSDP_SERVER = "ssdp_server"
# Attributes for accessing info from retrieved UPnP device description
ATTR_UPNP_DEVICE_TYPE = "deviceType"
ATTR_UPNP_FRIENDLY_NAME = "friendlyName"
ATTR_UPNP_MANUFACTURER = "manufacturer"
ATTR_UPNP_MANUFACTURER_URL = "manufacturerURL"
ATTR_UPNP_MODEL_DESCRIPTION = "modelDescription"
ATTR_UPNP_MODEL_NAME = "modelName"
ATTR_UPNP_MODEL_NUMBER = "modelNumber"
ATTR_UPNP_MODEL_URL = "modelURL"
ATTR_UPNP_SERIAL = "serialNumber"
ATTR_UPNP_UDN = "UDN"
ATTR_UPNP_UPC = "UPC"
ATTR_UPNP_PRESENTATION_URL = "presentationURL"

_LOGGER = logging.getLogger(__name__)


async def async_setup(opp, config):
    """Set up the SSDP integration."""

    async def initialize(_):
        scanner = Scanner(opp, await async_get_ssdp(opp))
        await scanner.async_scan(None)
        async_track_time_interval(opp, scanner.async_scan, SCAN_INTERVAL)

    opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STARTED, initialize)

    return True


class Scanner:
    """Class to manage SSDP scanning."""

    def __init__(self, opp, integration_matchers):
        """Initialize class."""
        self.opp = opp
        self.seen = set()
        self._entries = []
        self._integration_matchers = integration_matchers
        self._description_cache = {}

    async def _on_ssdp_response(self, data: Mapping[str, Any]) -> None:
        """Process an ssdp response."""
        self.async_store_entry(
            ssdp.UPNPEntry({key.lower(): item for key, item in data.items()})
        )

    @callback
    def async_store_entry(self, entry):
        """Save an entry for later processing."""
        self._entries.append(entry)

    async def async_scan(self, _):
        """Scan for new entries."""

        await async_search(async_callback=self._on_ssdp_response)
        await self._process_entries()

        # We clear the cache after each run. We track discovered entries
        # so will never need a description twice.
        self._description_cache.clear()
        self._entries.clear()

    async def _process_entries(self):
        """Process SSDP entries."""
        entries_to_process = []
        unseen_locations = set()

        for entry in self._entries:
            key = (entry.st, entry.location)

            if key in self.seen:
                continue

            self.seen.add(key)

            entries_to_process.append(entry)

            if (
                entry.location is not None
                and entry.location not in self._description_cache
            ):
                unseen_locations.add(entry.location)

        if not entries_to_process:
            return

        if unseen_locations:
            await self._fetch_descriptions(list(unseen_locations))

        tasks = []

        for entry in entries_to_process:
            info, domains = self._process_entry(entry)
            for domain in domains:
                _LOGGER.debug("Discovered %s at %s", domain, entry.location)
                tasks.append(
                    self.opp.config_entries.flow.async_init(
                        domain, context={"source": DOMAIN}, data=info
                    )
                )

        if tasks:
            await asyncio.gather(*tasks)

    async def _fetch_descriptions(self, locations):
        """Fetch descriptions from locations."""

        for idx, result in enumerate(
            await asyncio.gather(
                *[self._fetch_description(location) for location in locations],
                return_exceptions=True,
            )
        ):
            location = locations[idx]

            if isinstance(result, Exception):
                _LOGGER.exception(
                    "Failed to fetch ssdp data from: %s", location, exc_info=result
                )
                continue

            self._description_cache[location] = result

    def _process_entry(self, entry):
        """Process a single entry."""

        info = {"st": entry.st}
        for key in "usn", "ext", "server":
            if key in entry.values:
                info[key] = entry.values[key]

        if entry.location:
            # Multiple entries usually share same location. Make sure
            # we fetch it only once.
            info_req = self._description_cache.get(entry.location)
            if info_req is None:
                return (None, [])

            info.update(info_req)

        domains = set()
        for domain, matchers in self._integration_matchers.items():
            for matcher in matchers:
                if all(info.get(k) == v for (k, v) in matcher.items()):
                    domains.add(domain)

        if domains:
            return (info_from_entry(entry, info), domains)

        return (None, [])

    async def _fetch_description(self, xml_location):
        """Fetch an XML description."""
        session = self.opp.helpers.aiohttp_client.async_get_clientsession()
        try:
            resp = await session.get(xml_location, timeout=5)
            xml = await resp.text(errors="replace")

            # Samsung Smart TV sometimes returns an empty document the
            # first time. Retry once.
            if not xml:
                resp = await session.get(xml_location, timeout=5)
                xml = await resp.text(errors="replace")
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.debug("Error fetching %s: %s", xml_location, err)
            return {}

        try:
            tree = ElementTree.fromstring(xml)
        except ElementTree.ParseError as err:
            _LOGGER.debug("Error parsing %s: %s", xml_location, err)
            return {}

        return util.etree_to_dict(tree).get("root", {}).get("device", {})


def info_from_entry(entry, device_info):
    """Get info from an entry."""
    info = {
        ATTR_SSDP_LOCATION: entry.location,
        ATTR_SSDP_ST: entry.st,
    }
    if device_info:
        info.update(device_info)
        info.pop("st", None)
        if "usn" in info:
            info[ATTR_SSDP_USN] = info.pop("usn")
        if "ext" in info:
            info[ATTR_SSDP_EXT] = info.pop("ext")
        if "server" in info:
            info[ATTR_SSDP_SERVER] = info.pop("server")

    return info
