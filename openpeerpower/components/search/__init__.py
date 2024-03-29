"""The Search integration."""
from collections import defaultdict, deque
import logging

import voluptuous as vol

from openpeerpower.components import automation, group, script, websocket_api
from openpeerpower.components.openpeerpower import scene
from openpeerpower.core import OpenPeerPower, callback, split_entity_id
from openpeerpower.helpers import device_registry, entity_registry

DOMAIN = "search"
_LOGGER = logging.getLogger(__name__)


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the Search component."""
    websocket_api.async_register_command(opp, websocket_search_related)
    return True


@websocket_api.websocket_command(
    {
        vol.Required("type"): "search/related",
        vol.Required("item_type"): vol.In(
            (
                "area",
                "automation",
                "config_entry",
                "device",
                "entity",
                "group",
                "scene",
                "script",
            )
        ),
        vol.Required("item_id"): str,
    }
)
@callback
def websocket_search_related(opp, connection, msg):
    """Handle search."""
    searcher = Searcher(
        opp,
        device_registry.async_get(opp),
        entity_registry.async_get(opp),
    )
    connection.send_result(
        msg["id"], searcher.async_search(msg["item_type"], msg["item_id"])
    )


class Searcher:
    """Find related things.

    Few rules:
    Scenes, scripts, automations and config entries will only be expanded if they are
    the entry point. They won't be expanded if we process them. This is because they
    turn the results into garbage.
    """

    # These types won't be further explored. Config entries + Output types.
    DONT_RESOLVE = {"scene", "automation", "script", "group", "config_entry", "area"}
    # These types exist as an entity and so need cleanup in results
    EXIST_AS_ENTITY = {"script", "scene", "automation", "group"}

    def __init__(
        self,
        opp: OpenPeerPower,
        device_reg: device_registry.DeviceRegistry,
        entity_reg: entity_registry.EntityRegistry,
    ) -> None:
        """Search results."""
        self.opp = opp
        self._device_reg = device_reg
        self._entity_reg = entity_reg
        self.results = defaultdict(set)
        self._to_resolve = deque()

    @callback
    def async_search(self, item_type, item_id):
        """Find results."""
        _LOGGER.debug("Searching for %s/%s", item_type, item_id)
        self.results[item_type].add(item_id)
        self._to_resolve.append((item_type, item_id))

        while self._to_resolve:
            search_type, search_id = self._to_resolve.popleft()
            getattr(self, f"_resolve_{search_type}")(search_id)

        # Clean up entity_id items, from the general "entity" type result,
        # that are also found in the specific entity domain type.
        for result_type in self.EXIST_AS_ENTITY:
            self.results["entity"] -= self.results[result_type]

        # Remove entry into graph from search results.
        to_remove_item_type = item_type
        if item_type == "entity":
            domain = split_entity_id(item_id)[0]

            if domain in self.EXIST_AS_ENTITY:
                to_remove_item_type = domain

        self.results[to_remove_item_type].remove(item_id)

        # Filter out empty sets.
        return {key: val for key, val in self.results.items() if val}

    @callback
    def _add_or_resolve(self, item_type, item_id):
        """Add an item to explore."""
        if item_id in self.results[item_type]:
            return

        self.results[item_type].add(item_id)

        if item_type not in self.DONT_RESOLVE:
            self._to_resolve.append((item_type, item_id))

    @callback
    def _resolve_area(self, area_id) -> None:
        """Resolve an area."""
        for device in device_registry.async_entries_for_area(self._device_reg, area_id):
            self._add_or_resolve("device", device.id)
        for entity_entry in entity_registry.async_entries_for_area(
            self._entity_reg, area_id
        ):
            self._add_or_resolve("entity", entity_entry.entity_id)

        for entity_id in script.scripts_with_area(self.opp, area_id):
            self._add_or_resolve("entity", entity_id)

        for entity_id in automation.automations_with_area(self.opp, area_id):
            self._add_or_resolve("entity", entity_id)

    @callback
    def _resolve_device(self, device_id) -> None:
        """Resolve a device."""
        device_entry = self._device_reg.async_get(device_id)
        # Unlikely entry doesn't exist, but let's guard for bad data.
        if device_entry is not None:
            if device_entry.area_id:
                self._add_or_resolve("area", device_entry.area_id)

            for config_entry_id in device_entry.config_entries:
                self._add_or_resolve("config_entry", config_entry_id)

            # We do not resolve device_entry.via_device_id because that
            # device is not related data-wise inside HA.

        for entity_entry in entity_registry.async_entries_for_device(
            self._entity_reg, device_id
        ):
            self._add_or_resolve("entity", entity_entry.entity_id)

        for entity_id in script.scripts_with_device(self.opp, device_id):
            self._add_or_resolve("entity", entity_id)

        for entity_id in automation.automations_with_device(self.opp, device_id):
            self._add_or_resolve("entity", entity_id)

    @callback
    def _resolve_entity(self, entity_id) -> None:
        """Resolve an entity."""
        # Extra: Find automations and scripts that reference this entity.

        for entity in scene.scenes_with_entity(self.opp, entity_id):
            self._add_or_resolve("entity", entity)

        for entity in group.groups_with_entity(self.opp, entity_id):
            self._add_or_resolve("entity", entity)

        for entity in automation.automations_with_entity(self.opp, entity_id):
            self._add_or_resolve("entity", entity)

        for entity in script.scripts_with_entity(self.opp, entity_id):
            self._add_or_resolve("entity", entity)

        # Find devices
        entity_entry = self._entity_reg.async_get(entity_id)
        if entity_entry is not None:
            if entity_entry.device_id:
                self._add_or_resolve("device", entity_entry.device_id)

            if entity_entry.config_entry_id is not None:
                self._add_or_resolve("config_entry", entity_entry.config_entry_id)

        domain = split_entity_id(entity_id)[0]

        if domain in self.EXIST_AS_ENTITY:
            self._add_or_resolve(domain, entity_id)

    @callback
    def _resolve_automation(self, automation_entity_id) -> None:
        """Resolve an automation.

        Will only be called if automation is an entry point.
        """
        for entity in automation.entities_in_automation(self.opp, automation_entity_id):
            self._add_or_resolve("entity", entity)

        for device in automation.devices_in_automation(self.opp, automation_entity_id):
            self._add_or_resolve("device", device)

        for area in automation.areas_in_automation(self.opp, automation_entity_id):
            self._add_or_resolve("area", area)

    @callback
    def _resolve_script(self, script_entity_id) -> None:
        """Resolve a script.

        Will only be called if script is an entry point.
        """
        for entity in script.entities_in_script(self.opp, script_entity_id):
            self._add_or_resolve("entity", entity)

        for device in script.devices_in_script(self.opp, script_entity_id):
            self._add_or_resolve("device", device)

        for area in script.areas_in_script(self.opp, script_entity_id):
            self._add_or_resolve("area", area)

    @callback
    def _resolve_group(self, group_entity_id) -> None:
        """Resolve a group.

        Will only be called if group is an entry point.
        """
        for entity_id in group.get_entity_ids(self.opp, group_entity_id):
            self._add_or_resolve("entity", entity_id)

    @callback
    def _resolve_scene(self, scene_entity_id) -> None:
        """Resolve a scene.

        Will only be called if scene is an entry point.
        """
        for entity in scene.entities_in_scene(self.opp, scene_entity_id):
            self._add_or_resolve("entity", entity)

    @callback
    def _resolve_config_entry(self, config_entry_id) -> None:
        """Resolve a config entry.

        Will only be called if config entry is an entry point.
        """
        for device_entry in device_registry.async_entries_for_config_entry(
            self._device_reg, config_entry_id
        ):
            self._add_or_resolve("device", device_entry.id)

        for entity_entry in entity_registry.async_entries_for_config_entry(
            self._entity_reg, config_entry_id
        ):
            self._add_or_resolve("entity", entity_entry.entity_id)
