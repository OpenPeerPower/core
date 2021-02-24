"""Typing helpers for ZHA component."""

from typing import TYPE_CHECKING, Callable, TypeVar

import zigpy.device
import zigpy.endpoint
import zigpy.group
import zigpy.zcl
import zigpy.zdo

# pylint: disable=invalid-name
CALLABLE_T = TypeVar("CALLABLE_T", bound=Callable)
ChannelType = "ZigbeeChannel"
ChannelsType = "Channels"
ChannelPoolType = "ChannelPool"
ClientChannelType = "ClientChannel"
ZDOChannelType = "ZDOChannel"
ZhaDeviceType = "ZHADevice"
ZhaEntityType = "ZHAEntity"
ZhaGatewayType = "ZHAGateway"
ZhaGroupType = "ZHAGroupType"
ZigpyClusterType = zigpy.zcl.Cluster
ZigpyDeviceType = zigpy.device.Device
ZigpyEndpointType = zigpy.endpoint.Endpoint
ZigpyGroupType = zigpy.group.Group
ZigpyZdoType = zigpy.zdo.ZDO

if TYPE_CHECKING:
    import openpeerpower.components.zop.core.channels
    import openpeerpower.components.zop.core.channels as channels
    import openpeerpower.components.zop.core.channels.base as base_channels
    import openpeerpower.components.zop.core.device
    import openpeerpower.components.zop.core.gateway
    import openpeerpower.components.zop.core.group
    import openpeerpower.components.zop.entity

    ChannelType = base_channels.ZigbeeChannel
    ChannelsType = channels.Channels
    ChannelPoolType = channels.ChannelPool
    ClientChannelType = base_channels.ClientChannel
    ZDOChannelType = base_channels.ZDOChannel
    ZhaDeviceType = openpeerpower.components.zop.core.device.ZHADevice
    ZhaEntityType = openpeerpower.components.zop.entity.ZhaEntity
    ZhaGatewayType = openpeerpower.components.zop.core.gateway.ZHAGateway
    ZhaGroupType = openpeerpower.components.zop.core.group.ZHAGroup
