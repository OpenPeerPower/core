"""Support for device tracking of Huawei LTE routers."""

import logging
import re
from typing import Any, Callable, Dict, List, Optional, Set, cast

import attr
from stringcase import snakecase

from openpeerpower.components.device_tracker.config_entry import ScannerEntity
from openpeerpower.components.device_tracker.const import (
    DOMAIN as DEVICE_TRACKER_DOMAIN,
    SOURCE_TYPE_ROUTER,
)
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_URL
from openpeerpower.core import callback
from openpeerpower.helpers import entity_registry
from openpeerpower.helpers.dispatcher import async_dispatcher_connect
from openpeerpower.helpers.entity import Entity
from openpeerpower.helpers.typing import OpenPeerPowerType

from . import HuaweiLteBaseEntity
from .const import DOMAIN, KEY_WLAN_HOST_LIST, UPDATE_SIGNAL

_LOGGER = logging.getLogger(__name__)

_DEVICE_SCAN = f"{DEVICE_TRACKER_DOMAIN}/device_scan"


async def async_setup_entry(
    opp: OpenPeerPowerType,
    config_entry: ConfigEntry,
    async_add_entities: Callable[[List[Entity], bool], None],
) -> None:
    """Set up from config entry."""

    # Grab hosts list once to examine whether the initial fetch has got some data for
    # us, i.e. if wlan host list is supported. Only set up a subscription and proceed
    # with adding and tracking entities if it is.
    router = opp.data[DOMAIN].routers[config_entry.data[CONF_URL]]
    try:
        _ = router.data[KEY_WLAN_HOST_LIST]["Hosts"]["Host"]
    except KeyError:
        _LOGGER.debug("%s[%s][%s] not in data", KEY_WLAN_HOST_LIST, "Hosts", "Host")
        return

    # Initialize already tracked entities
    tracked: Set[str] = set()
    registry = await entity_registry.async_get_registry(opp)
    known_entities: List[Entity] = []
    for entity in registry.entities.values():
        if (
            entity.domain == DEVICE_TRACKER_DOMAIN
            and entity.config_entry_id == config_entry.entry_id
        ):
            tracked.add(entity.unique_id)
            known_entities.append(
                HuaweiLteScannerEntity(router, entity.unique_id.partition("-")[2])
            )
    async_add_entities(known_entities, True)

    # Tell parent router to poll hosts list to gather new devices
    router.subscriptions[KEY_WLAN_HOST_LIST].add(_DEVICE_SCAN)

    async def _async_maybe_add_new_entities(url: str) -> None:
        """Add new entities if the update signal comes from our router."""
        if url == router.url:
            async_add_new_entities(opp, url, async_add_entities, tracked)

    # Register to handle router data updates
    disconnect_dispatcher = async_dispatcher_connect(
        opp, UPDATE_SIGNAL, _async_maybe_add_new_entities
    )
    router.unload_handlers.append(disconnect_dispatcher)

    # Add new entities from initial scan
    async_add_new_entities(opp, router.url, async_add_entities, tracked)


@callback
def async_add_new_entities(
    opp: OpenPeerPowerType,
    router_url: str,
    async_add_entities: Callable[[List[Entity], bool], None],
    tracked: Set[str],
) -> None:
    """Add new entities that are not already being tracked."""
    router = opp.data[DOMAIN].routers[router_url]
    try:
        hosts = router.data[KEY_WLAN_HOST_LIST]["Hosts"]["Host"]
    except KeyError:
        _LOGGER.debug("%s[%s][%s] not in data", KEY_WLAN_HOST_LIST, "Hosts", "Host")
        return

    new_entities: List[Entity] = []
    for host in (x for x in hosts if x.get("MacAddress")):
        entity = HuaweiLteScannerEntity(router, host["MacAddress"])
        if entity.unique_id in tracked:
            continue
        tracked.add(entity.unique_id)
        new_entities.append(entity)
    async_add_entities(new_entities, True)


def _better_snakecase(text: str) -> str:
    if text == text.upper():
        # All uppercase to all lowercase to get http for HTTP, not h_t_t_p
        text = text.lower()
    else:
        # Three or more consecutive uppercase with middle part lowercased
        # to get http_response for HTTPResponse, not h_t_t_p_response
        text = re.sub(
            r"([A-Z])([A-Z]+)([A-Z](?:[^A-Z]|$))",
            lambda match: f"{match.group(1)}{match.group(2).lower()}{match.group(3)}",
            text,
        )
    return cast(str, snakecase(text))


@attr.s
class HuaweiLteScannerEntity(HuaweiLteBaseEntity, ScannerEntity):
    """Huawei LTE router scanner entity."""

    mac: str = attr.ib()

    _is_connected: bool = attr.ib(init=False, default=False)
    _hostname: Optional[str] = attr.ib(init=False, default=None)
    _device_state_attributes: Dict[str, Any] = attr.ib(init=False, factory=dict)

    def __attrs_post_init__(self) -> None:
        """Initialize internal state."""
        self._device_state_attributes["mac_address"] = self.mac

    @property
    def _entity_name(self) -> str:
        return self._hostname or self.mac

    @property
    def _device_unique_id(self) -> str:
        return self.mac

    @property
    def source_type(self) -> str:
        """Return SOURCE_TYPE_ROUTER."""
        return SOURCE_TYPE_ROUTER

    @property
    def is_connected(self) -> bool:
        """Get whether the entity is connected."""
        return self._is_connected

    @property
    def device_state_attributes(self) -> Dict[str, Any]:
        """Get additional attributes related to entity state."""
        return self._device_state_attributes

    async def async_update(self) -> None:
        """Update state."""
        hosts = self.router.data[KEY_WLAN_HOST_LIST]["Hosts"]["Host"]
        host = next((x for x in hosts if x.get("MacAddress") == self.mac), None)
        self._is_connected = host is not None
        if host is not None:
            self._hostname = host.get("HostName")
            self._device_state_attributes = {
                _better_snakecase(k): v for k, v in host.items() if k != "HostName"
            }
