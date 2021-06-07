"""Support for KNX scenes."""
from __future__ import annotations

from typing import Any

from xknx import XKNX
from xknx.devices import Scene as XknxScene

from openpeerpower.components.scene import Scene
from openpeerpower.const import CONF_NAME
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.entity_platform import AddEntitiesCallback
from openpeerpower.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DOMAIN, KNX_ADDRESS
from .knx_entity import KnxEntity
from .schema import SceneSchema


async def async_setup_platform(
    opp: OpenPeerPower,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the scenes for KNX platform."""
    if not discovery_info or not discovery_info["platform_config"]:
        return

    platform_config = discovery_info["platform_config"]
    xknx: XKNX = opp.data[DOMAIN].xknx

    entities = []
    for entity_config in platform_config:
        entities.append(KNXScene(xknx, entity_config))

    async_add_entities(entities)


class KNXScene(KnxEntity, Scene):
    """Representation of a KNX scene."""

    def __init__(self, xknx: XKNX, config: ConfigType) -> None:
        """Init KNX scene."""
        self._device: XknxScene
        super().__init__(
            device=XknxScene(
                xknx,
                name=config[CONF_NAME],
                group_address=config[KNX_ADDRESS],
                scene_number=config[SceneSchema.CONF_SCENE_NUMBER],
            )
        )
        self._unique_id = (
            f"{self._device.scene_value.group_address}_{self._device.scene_number}"
        )

    async def async_activate(self, **kwargs: Any) -> None:
        """Activate the scene."""
        await self._device.run()
