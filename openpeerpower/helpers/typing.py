"""Typing Helpers for Open Peer Power."""
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Tuple, Union

import openpeerpower.core

GPSType = Tuple[float, float]
ConfigType = Dict[str, Any]
ContextType = openpeerpower.core.Context
DiscoveryInfoType = Dict[str, Any]
EventType = openpeerpower.core.Event
OpenPeerPowerType = openpeerpower.core.OpenPeerPower
ServiceCallType = openpeerpower.core.ServiceCall
ServiceDataType = Dict[str, Any]
StateType = Union[None, str, int, float]
TemplateVarsType = Optional[Mapping[str, Any]]

# Custom type for recorder Queries
QueryType = Any


class UndefinedType(Enum):
    # pylint: disable=invalid-name
    """Singleton type for use with not set sentinel values."""

    _singleton = 0


UNDEFINED = UndefinedType._singleton  # pylint: disable=protected-access
