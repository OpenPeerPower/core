"""Provide a way to connect devices to one physical location."""
from __future__ import annotations

from collections import OrderedDict
from collections.abc import Container, Iterable, MutableMapping
from typing import cast

import attr

from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.helpers import device_registry as dr, entity_registry as er
from openpeerpower.loader import bind_opp
from openpeerpower.util import slugify

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
    normalized_name: str = attr.ib()
    id: str | None = attr.ib(default=None)

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

    def __init__(self, opp: OpenPeerPower) -> None:
        """Initialize the area registry."""
        self.opp = opp
        self.areas: MutableMapping[str, AreaEntry] = {}
        self._store = opp.helpers.storage.Store(STORAGE_VERSION, STORAGE_KEY)
        self._normalized_name_area_idx: dict[str, str] = {}

    @callback
    def async_get_area(self, area_id: str) -> AreaEntry | None:
        """Get area by id."""
        return self.areas.get(area_id)

    @callback
    def async_get_area_by_name(self, name: str) -> AreaEntry | None:
        """Get area by name."""
        normalized_name = normalize_area_name(name)
        if normalized_name not in self._normalized_name_area_idx:
            return None
        return self.areas[self._normalized_name_area_idx[normalized_name]]

    @callback
    def async_list_areas(self) -> Iterable[AreaEntry]:
        """Get all areas."""
        return self.areas.values()

    @callback
    def async_get_or_create(self, name: str) -> AreaEntry:
        """Get or create an area."""
        area = self.async_get_area_by_name(name)
        if area:
            return area
        return self.async_create(name)

    @callback
    def async_create(self, name: str) -> AreaEntry:
        """Create a new area."""
        normalized_name = normalize_area_name(name)

        if self.async_get_area_by_name(name):
            raise ValueError(f"The name {name} ({normalized_name}) is already in use")

        area = AreaEntry(name=name, normalized_name=normalized_name)
        area.generate_id(self.areas)
        assert area.id is not None
        self.areas[area.id] = area
        self._normalized_name_area_idx[normalized_name] = area.id
        self.async_schedule_save()
        self.opp.bus.async_fire(
            EVENT_AREA_REGISTRY_UPDATED, {"action": "create", "area_id": area.id}
        )
        return area

    @callback
    def async_delete(self, area_id: str) -> None:
        """Delete area."""
        area = self.areas[area_id]
        device_registry = dr.async_get(self.opp)
        entity_registry = er.async_get(self.opp)
        device_registry.async_clear_area_id(area_id)
        entity_registry.async_clear_area_id(area_id)

        del self.areas[area_id]
        del self._normalized_name_area_idx[area.normalized_name]

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

        normalized_name = normalize_area_name(name)

        if normalized_name != old.normalized_name and self.async_get_area_by_name(name):
            raise ValueError(f"The name {name} ({normalized_name}) is already in use")

        changes["name"] = name
        changes["normalized_name"] = normalized_name

        new = self.areas[area_id] = attr.evolve(old, **changes)
        self._normalized_name_area_idx[
            normalized_name
        ] = self._normalized_name_area_idx.pop(old.normalized_name)

        self.async_schedule_save()
        return new

    async def async_load(self) -> None:
        """Load the area registry."""
        data = await self._store.async_load()

        areas: MutableMapping[str, AreaEntry] = OrderedDict()

        if data is not None:
            for area in data["areas"]:
                normalized_name = normalize_area_name(area["name"])
                areas[area["id"]] = AreaEntry(
                    name=area["name"], id=area["id"], normalized_name=normalized_name
                )
                self._normalized_name_area_idx[normalized_name] = area["id"]

        self.areas = areas

    @callback
    def async_schedule_save(self) -> None:
        """Schedule saving the area registry."""
        self._store.async_delay_save(self._data_to_save, SAVE_DELAY)

    @callback
    def _data_to_save(self) -> dict[str, list[dict[str, str | None]]]:
        """Return data of area registry to store in a file."""
        data = {}

        data["areas"] = [
            {
                "name": entry.name,
                "id": entry.id,
            }
            for entry in self.areas.values()
        ]

        return data


@callback
def async_get(opp: OpenPeerPower) -> AreaRegistry:
    """Get area registry."""
    return cast(AreaRegistry, opp.data[DATA_REGISTRY])


async def async_load(opp: OpenPeerPower) -> None:
    """Load area registry."""
    assert DATA_REGISTRY not in opp.data
    opp.data[DATA_REGISTRY] = AreaRegistry(opp)
    await opp.data[DATA_REGISTRY].async_load()


@bind_opp
async def async_get_registry(opp: OpenPeerPower) -> AreaRegistry:
    """Get area registry.

    This is deprecated and will be removed in the future. Use async_get instead.
    """
    return async_get(opp)


def normalize_area_name(area_name: str) -> str:
    """Normalize an area name by removing whitespace and case folding."""
    return area_name.casefold().replace(" ", "")
