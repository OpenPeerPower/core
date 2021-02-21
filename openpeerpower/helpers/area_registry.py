"""Provide a way to connect devices to one physical location."""
from collections import OrderedDict
from typing import Container, Dict, Iterable, List, MutableMapping, Optional, cast

import attr

from openpeerpower.core import callback
from openpeerpower.helpers import device_registry as dr, entity_registry as er
from openpeerpower.loader import bind_opp
from openpeerpower.util import slugify

from .typing import OpenPeerPowerType

# mypy: disallow-any-generics

DATA_REGISTRY = "area_registry"
EVENT_AREA_REGISTRY_UPDATED = "area_registry_updated"
STORAGE_KEY = "core.area_registry"
STORAGE_VERSION = 1
SAVE_DELAY = 10


@attr.s(slots=True, frozen=True)
class AreaEntry:
    """Area Registry Entry."""

    name: str = attr.ib()
    id: Optional[str] = attr.ib(default=None)

    def generate_id(self, existing_ids: Container[str]) -> None:
        """Initialize ID."""
        suggestion = suggestion_base = slugify(self.name)
        tries = 1
        while suggestion in existing_ids:
            tries += 1
            suggestion = f"{suggestion_base}_{tries}"
        object.__setattr__(self, "id", suggestion)


class AreaRegistry:
    """Class to hold a registry of areas."""

    def __init__(self,.opp: OpenPeerPowerType) -> None:
        """Initialize the area registry."""
        self.opp = opp
        self.areas: MutableMapping[str, AreaEntry] = {}
        self._store = opp.helpers.storage.Store(STORAGE_VERSION, STORAGE_KEY)

    @callback
    def async_get_area(self, area_id: str) -> Optional[AreaEntry]:
        """Get all areas."""
        return self.areas.get(area_id)

    @callback
    def async_list_areas(self) -> Iterable[AreaEntry]:
        """Get all areas."""
        return self.areas.values()

    @callback
    def async_create(self, name: str) -> AreaEntry:
        """Create a new area."""
        if self._async_is_registered(name):
            raise ValueError("Name is already in use")

        area = AreaEntry(name=name)
        area.generate_id(self.areas)
        assert area.id is not None
        self.areas[area.id] = area
        self.async_schedule_save()
        self.opp.bus.async_fire(
            EVENT_AREA_REGISTRY_UPDATED, {"action": "create", "area_id": area.id}
        )
        return area

    @callback
    def async_delete(self, area_id: str) -> None:
        """Delete area."""
        device_registry = dr.async_get(self.opp)
        entity_registry = er.async_get(self.opp)
        device_registry.async_clear_area_id(area_id)
        entity_registry.async_clear_area_id(area_id)

        del self.areas[area_id]

        self.opp.bus.async_fire(
            EVENT_AREA_REGISTRY_UPDATED, {"action": "remove", "area_id": area_id}
        )

        self.async_schedule_save()

    @callback
    def async_update(self, area_id: str, name: str) -> AreaEntry:
        """Update name of area."""
        updated = self._async_update(area_id, name)
        self.opp.bus.async_fire(
            EVENT_AREA_REGISTRY_UPDATED, {"action": "update", "area_id": area_id}
        )
        return updated

    @callback
    def _async_update(self, area_id: str, name: str) -> AreaEntry:
        """Update name of area."""
        old = self.areas[area_id]

        changes = {}

        if name == old.name:
            return old

        if self._async_is_registered(name):
            raise ValueError("Name is already in use")

        changes["name"] = name

        new = self.areas[area_id] = attr.evolve(old, **changes)
        self.async_schedule_save()
        return new

    @callback
    def _async_is_registered(self, name: str) -> Optional[AreaEntry]:
        """Check if a name is currently registered."""
        for area in self.areas.values():
            if name == area.name:
                return area
        return None

    async def async_load(self) -> None:
        """Load the area registry."""
        data = await self._store.async_load()

        areas: MutableMapping[str, AreaEntry] = OrderedDict()

        if data is not None:
            for area in data["areas"]:
                areas[area["id"]] = AreaEntry(name=area["name"], id=area["id"])

        self.areas = areas

    @callback
    def async_schedule_save(self) -> None:
        """Schedule saving the area registry."""
        self._store.async_delay_save(self._data_to_save, SAVE_DELAY)

    @callback
    def _data_to_save(self) -> Dict[str, List[Dict[str, Optional[str]]]]:
        """Return data of area registry to store in a file."""
        data = {}

        data["areas"] = [
            {"name": entry.name, "id": entry.id} for entry in self.areas.values()
        ]

        return data


@callback
def async_get.opp: OpenPeerPowerType) -> AreaRegistry:
    """Get area registry."""
    return cast(AreaRegistry,.opp.data[DATA_REGISTRY])


async def async_load.opp: OpenPeerPowerType) -> None:
    """Load area registry."""
    assert DATA_REGISTRY not in.opp.data
   .opp.data[DATA_REGISTRY] = AreaRegistry.opp)
    await opp..data[DATA_REGISTRY].async_load()


@bind_opp
async def async_get_registry.opp: OpenPeerPowerType) -> AreaRegistry:
    """Get area registry.

    This is deprecated and will be removed in the future. Use async_get instead.
    """
    return async_get.opp)
