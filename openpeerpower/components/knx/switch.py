"""Support for KNX/IP switches."""
from __future__ import annotations

from typing import Any

from xknx import XKNX
from xknx.devices import Switch as XknxSwitch

from openpeerpower.components.switch import SwitchEntity
from openpeerpower.const import CONF_NAME
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.entity_platform import AddEntitiesCallback
from openpeerpower.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DOMAIN, KNX_ADDRESS
from .knx_entity import KnxEntity
from .schema import SwitchSchema


async def async_setup_platform(
    opp: OpenPeerPower,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up switch(es) for KNX platform."""
    if not discovery_info or not discovery_info["platform_config"]:
        return

    platform_config = discovery_info["platform_config"]
    xknx: XKNX = opp.data[DOMAIN].xknx

    entities = []
    for entity_config in platform_config:
        entities.append(KNXSwitch(xknx, entity_config))

    async_add_entities(entities)


class KNXSwitch(KnxEntity, SwitchEntity):
    """Representation of a KNX switch."""

    def __init__(self, xknx: XKNX, config: ConfigType) -> None:
        """Initialize of KNX switch."""
        self._device: XknxSwitch
        super().__init__(
            device=XknxSwitch(
                xknx,
                name=config[CONF_NAME],
                group_address=config[KNX_ADDRESS],
                group_address_state=config.get(SwitchSchema.CONF_STATE_ADDRESS),
                invert=config[SwitchSchema.CONF_INVERT],
            )
        )
        self._unique_id = f"{self._device.switch.group_address}"

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return bool(self._device.state)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        await self._device.set_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        await self._device.set_off()
