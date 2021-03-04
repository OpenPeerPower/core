"""The BleBox devices integration."""
import asyncio
import logging

from blebox_uniapi.error import Error
from blebox_uniapi.products import Products
from blebox_uniapi.session import ApiHost

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_HOST, CONF_PORT
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.entity import Entity

from .const import DEFAULT_SETUP_TIMEOUT, DOMAIN, PRODUCT

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["cover", "sensor", "switch", "air_quality", "light", "climate"]

PARALLEL_UPDATES = 0


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the BleBox devices component."""
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up BleBox devices from a config entry."""

    websession = async_get_clientsession(opp)

    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    timeout = DEFAULT_SETUP_TIMEOUT

    api_host = ApiHost(host, port, timeout, websession, opp.loop)

    try:
        product = await Products.async_from_host(api_host)
    except Error as ex:
        _LOGGER.error("Identify failed at %s:%d (%s)", api_host.host, api_host.port, ex)
        raise ConfigEntryNotReady from ex

    domain = opp.data.setdefault(DOMAIN, {})
    domain_entry = domain.setdefault(entry.entry_id, {})
    product = domain_entry.setdefault(PRODUCT, product)

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
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

    return unload_ok


@callback
def create_blebox_entities(
    opp, config_entry, async_add_entities, entity_klass, entity_type
):
    """Create entities from a BleBox product's features."""

    product = opp.data[DOMAIN][config_entry.entry_id][PRODUCT]

    entities = []
    if entity_type in product.features:
        for feature in product.features[entity_type]:
            entities.append(entity_klass(feature))

    async_add_entities(entities, True)


class BleBoxEntity(Entity):
    """Implements a common class for entities representing a BleBox feature."""

    def __init__(self, feature):
        """Initialize a BleBox entity."""
        self._feature = feature

    @property
    def name(self):
        """Return the internal entity name."""
        return self._feature.full_name

    @property
    def unique_id(self):
        """Return a unique id."""
        return self._feature.unique_id

    async def async_update(self):
        """Update the entity state."""
        try:
            await self._feature.async_update()
        except Error as ex:
            _LOGGER.error("Updating '%s' failed: %s", self.name, ex)

    @property
    def device_info(self):
        """Return device information for this entity."""
        product = self._feature.product
        return {
            "identifiers": {(DOMAIN, product.unique_id)},
            "name": product.name,
            "manufacturer": product.brand,
            "model": product.model,
            "sw_version": product.firmware_version,
        }
