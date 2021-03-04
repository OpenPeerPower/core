"""Runtime entry data for ESPHome stored in opp.data."""
import asyncio
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Set, Tuple

from aioesphomeapi import (
    COMPONENT_TYPE_TO_INFO,
    BinarySensorInfo,
    CameraInfo,
    ClimateInfo,
    CoverInfo,
    DeviceInfo,
    EntityInfo,
    EntityState,
    FanInfo,
    LightInfo,
    SensorInfo,
    SwitchInfo,
    TextSensorInfo,
    UserService,
)
import attr

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.core import callback
from openpeerpower.helpers.dispatcher import async_dispatcher_send
from openpeerpower.helpers.storage import Store
from openpeerpower.helpers.typing import OpenPeerPowerType

if TYPE_CHECKING:
    from . import APIClient

SAVE_DELAY = 120

# Mapping from ESPHome info type to OP platform
INFO_TYPE_TO_PLATFORM = {
    BinarySensorInfo: "binary_sensor",
    CameraInfo: "camera",
    ClimateInfo: "climate",
    CoverInfo: "cover",
    FanInfo: "fan",
    LightInfo: "light",
    SensorInfo: "sensor",
    SwitchInfo: "switch",
    TextSensorInfo: "sensor",
}


@attr.s
class RuntimeEntryData:
    """Store runtime data for esphome config entries."""

    entry_id: str = attr.ib()
    client: "APIClient" = attr.ib()
    store: Store = attr.ib()
    reconnect_task: Optional[asyncio.Task] = attr.ib(default=None)
    state: Dict[str, Dict[str, Any]] = attr.ib(factory=dict)
    info: Dict[str, Dict[str, Any]] = attr.ib(factory=dict)

    # A second list of EntityInfo objects
    # This is necessary for when an entity is being removed. OP requires
    # some static info to be accessible during removal (unique_id, maybe others)
    # If an entity can't find anything in the info array, it will look for info here.
    old_info: Dict[str, Dict[str, Any]] = attr.ib(factory=dict)

    services: Dict[int, "UserService"] = attr.ib(factory=dict)
    available: bool = attr.ib(default=False)
    device_info: Optional[DeviceInfo] = attr.ib(default=None)
    cleanup_callbacks: List[Callable[[], None]] = attr.ib(factory=list)
    disconnect_callbacks: List[Callable[[], None]] = attr.ib(factory=list)
    loaded_platforms: Set[str] = attr.ib(factory=set)
    platform_load_lock: asyncio.Lock = attr.ib(factory=asyncio.Lock)

    @callback
    def async_update_entity(
        self, opp: OpenPeerPowerType, component_key: str, key: int
    ) -> None:
        """Schedule the update of an entity."""
        signal = f"esphome_{self.entry_id}_update_{component_key}_{key}"
        async_dispatcher_send(opp, signal)

    @callback
    def async_remove_entity(
        self, opp: OpenPeerPowerType, component_key: str, key: int
    ) -> None:
        """Schedule the removal of an entity."""
        signal = f"esphome_{self.entry_id}_remove_{component_key}_{key}"
        async_dispatcher_send(opp, signal)

    async def _ensure_platforms_loaded(
        self, opp: OpenPeerPowerType, entry: ConfigEntry, platforms: Set[str]
    ):
        async with self.platform_load_lock:
            needed = platforms - self.loaded_platforms
            tasks = []
            for platform in needed:
                tasks.append(
                    opp.config_entries.async_forward_entry_setup(entry, platform)
                )
            if tasks:
                await asyncio.wait(tasks)
            self.loaded_platforms |= needed

    async def async_update_static_infos(
        self, opp: OpenPeerPowerType, entry: ConfigEntry, infos: List[EntityInfo]
    ) -> None:
        """Distribute an update of static infos to all platforms."""
        # First, load all platforms
        needed_platforms = set()
        for info in infos:
            for info_type, platform in INFO_TYPE_TO_PLATFORM.items():
                if isinstance(info, info_type):
                    needed_platforms.add(platform)
                    break
        await self._ensure_platforms_loaded(opp, entry, needed_platforms)

        # Then send dispatcher event
        signal = f"esphome_{self.entry_id}_on_list"
        async_dispatcher_send(opp, signal, infos)

    @callback
    def async_update_state(self, opp: OpenPeerPowerType, state: EntityState) -> None:
        """Distribute an update of state information to all platforms."""
        signal = f"esphome_{self.entry_id}_on_state"
        async_dispatcher_send(opp, signal, state)

    @callback
    def async_update_device_state(self, opp: OpenPeerPowerType) -> None:
        """Distribute an update of a core device state like availability."""
        signal = f"esphome_{self.entry_id}_on_device_update"
        async_dispatcher_send(opp, signal)

    async def async_load_from_store(self) -> Tuple[List[EntityInfo], List[UserService]]:
        """Load the retained data from store and return de-serialized data."""
        restored = await self.store.async_load()
        if restored is None:
            return [], []

        self.device_info = _attr_obj_from_dict(
            DeviceInfo, **restored.pop("device_info")
        )
        infos = []
        for comp_type, restored_infos in restored.items():
            if comp_type not in COMPONENT_TYPE_TO_INFO:
                continue
            for info in restored_infos:
                cls = COMPONENT_TYPE_TO_INFO[comp_type]
                infos.append(_attr_obj_from_dict(cls, **info))
        services = []
        for service in restored.get("services", []):
            services.append(UserService.from_dict(service))
        return infos, services

    async def async_save_to_store(self) -> None:
        """Generate dynamic data to store and save it to the filesystem."""
        store_data = {"device_info": attr.asdict(self.device_info), "services": []}

        for comp_type, infos in self.info.items():
            store_data[comp_type] = [attr.asdict(info) for info in infos.values()]
        for service in self.services.values():
            store_data["services"].append(service.to_dict())

        self.store.async_delay_save(lambda: store_data, SAVE_DELAY)


def _attr_obj_from_dict(cls, **kwargs):
    return cls(**{key: kwargs[key] for key in attr.fields_dict(cls) if key in kwargs})
