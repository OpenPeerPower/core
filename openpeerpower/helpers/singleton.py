"""Helper to help coordinating calls."""
import asyncio
import functools
from typing import Callable, Optional, TypeVar, cast

from openpeerpower.core import OpenPeerPower
from openpeerpower.loader import bind_opp

T = TypeVar("T")

FUNC = Callable[[OpenPeerPower], T]


def singleton(data_key: str) -> Callable[[FUNC], FUNC]:
    """Decorate a function that should be called once per instance.

    Result will be cached and simultaneous calls will be handled.
    """

    def wrapper(func: FUNC) -> FUNC:
        """Wrap a function with caching logic."""
        if not asyncio.iscoroutinefunction(func):

            @bind_opp
            @functools.wraps(func)
            def wrapped(opp: OpenPeerPower) -> T:
                obj: Optional[T] = opp.data.get(data_key)
                if obj is None:
                    obj = opp.data[data_key] = func(opp)
                return obj

            return wrapped

        @bind_opp
        @functools.wraps(func)
        async def async_wrapped(opp: OpenPeerPower) -> T:
            obj_or_evt = opp.data.get(data_key)

            if not obj_or_evt:
                evt = opp.data[data_key] = asyncio.Event()

                result = await func(opp)

                opp.data[data_key] = result
                evt.set()
                return cast(T, result)

            if isinstance(obj_or_evt, asyncio.Event):
                evt = obj_or_evt
                await evt.wait()
                return cast(T, opp.data.get(data_key))

            return cast(T, obj_or_evt)

        return async_wrapped

    return wrapper
