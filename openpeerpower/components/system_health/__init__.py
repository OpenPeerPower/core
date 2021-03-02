"""Support for System health ."""
import asyncio
import dataclasses
from datetime import datetime
import logging
from typing import Awaitable, Callable, Dict, Optional

import aiohttp
import async_timeout
import voluptuous as vol

from openpeerpower.components import websocket_api
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.helpers import aiohttp_client, integration_platform
from openpeerpower.helpers.typing import ConfigType
from openpeerpower.loader import bind_opp

_LOGGER = logging.getLogger(__name__)

DOMAIN = "system_health"

INFO_CALLBACK_TIMEOUT = 5


@bind_opp
@callback
def async_register_info(
    opp: OpenPeerPower,
    domain: str,
    info_callback: Callable[[OpenPeerPower], Dict],
):
    """Register an info callback.

    Deprecated.
    """
    _LOGGER.warning(
        "system_health.async_register_info is deprecated. Add a system_health platform instead."
    )
    opp.data.setdefault(DOMAIN, {})
    SystemHealthRegistration(opp, domain).async_register_info(info_callback)


async def async_setup(opp: OpenPeerPower, config: ConfigType):
    """Set up the System Health component."""
    opp.components.websocket_api.async_register_command(handle_info)
    opp.data.setdefault(DOMAIN, {})

    await integration_platform.async_process_integration_platforms(
        opp, DOMAIN, _register_system_health_platform
    )

    return True


async def _register_system_health_platform(opp, integration_domain, platform):
    """Register a system health platform."""
    platform.async_register(opp, SystemHealthRegistration(opp, integration_domain))


async def get_integration_info(
    opp: OpenPeerPower, registration: "SystemHealthRegistration"
):
    """Get integration system health."""
    try:
        with async_timeout.timeout(INFO_CALLBACK_TIMEOUT):
            data = await registration.info_callback(opp)
    except asyncio.TimeoutError:
        data = {"error": {"type": "failed", "error": "timeout"}}
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("Error fetching info")
        data = {"error": {"type": "failed", "error": "unknown"}}

    result = {"info": data}

    if registration.manage_url:
        result["manage_url"] = registration.manage_url

    return result


@callback
def _format_value(val):
    """Format a system health value."""
    if isinstance(val, datetime):
        return {"value": val.isoformat(), "type": "date"}
    return val


@websocket_api.async_response
@websocket_api.websocket_command({vol.Required("type"): "system_health/info"})
async def handle_info(
    opp: OpenPeerPower, connection: websocket_api.ActiveConnection, msg: Dict
):
    """Handle an info request via a subscription."""
    registrations: Dict[str, SystemHealthRegistration] = opp.data[DOMAIN]
    data = {}
    pending_info = {}

    for domain, domain_data in zip(
        registrations,
        await asyncio.gather(
            *(
                get_integration_info(opp, registration)
                for registration in registrations.values()
            )
        ),
    ):
        for key, value in domain_data["info"].items():
            if asyncio.iscoroutine(value):
                value = asyncio.create_task(value)
            if isinstance(value, asyncio.Task):
                pending_info[(domain, key)] = value
                domain_data["info"][key] = {"type": "pending"}
            else:
                domain_data["info"][key] = _format_value(value)

        data[domain] = domain_data

    # Confirm subscription
    connection.send_result(msg["id"])

    stop_event = asyncio.Event()
    connection.subscriptions[msg["id"]] = stop_event.set

    # Send initial data
    connection.send_message(
        websocket_api.messages.event_message(
            msg["id"], {"type": "initial", "data": data}
        )
    )

    # If nothing pending, wrap it up.
    if not pending_info:
        connection.send_message(
            websocket_api.messages.event_message(msg["id"], {"type": "finish"})
        )
        return

    tasks = [asyncio.create_task(stop_event.wait()), *pending_info.values()]
    pending_lookup = {val: key for key, val in pending_info.items()}

    # One task is the stop_event.wait() and is always there
    while len(tasks) > 1 and not stop_event.is_set():
        # Wait for first completed task
        done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        if stop_event.is_set():
            for task in tasks:
                task.cancel()
            return

        # Update subscription of all finished tasks
        for result in done:
            domain, key = pending_lookup[result]
            event_msg = {
                "type": "update",
                "domain": domain,
                "key": key,
            }

            if result.exception():
                exception = result.exception()
                _LOGGER.error(
                    "Error fetching system info for %s - %s",
                    domain,
                    key,
                    exc_info=(type(exception), exception, exception.__traceback__),
                )
                event_msg["success"] = False
                event_msg["error"] = {"type": "failed", "error": "unknown"}
            else:
                event_msg["success"] = True
                event_msg["data"] = _format_value(result.result())

            connection.send_message(
                websocket_api.messages.event_message(msg["id"], event_msg)
            )

    connection.send_message(
        websocket_api.messages.event_message(msg["id"], {"type": "finish"})
    )


@dataclasses.dataclass()
class SystemHealthRegistration:
    """Helper class to track platform registration."""

    opp: OpenPeerPower
    domain: str
    info_callback: Optional[Callable[[OpenPeerPower], Awaitable[Dict]]] = None
    manage_url: Optional[str] = None

    @callback
    def async_register_info(
        self,
        info_callback: Callable[[OpenPeerPower], Awaitable[Dict]],
        manage_url: Optional[str] = None,
    ):
        """Register an info callback."""
        self.info_callback = info_callback
        self.manage_url = manage_url
        self.opp.data[DOMAIN][self.domain] = self


async def async_check_can_reach_url(
    opp: OpenPeerPower, url: str, more_info: Optional[str] = None
) -> str:
    """Test if the url can be reached."""
    session = aiohttp_client.async_get_clientsession(opp)

    try:
        await session.get(url, timeout=5)
        return "ok"
    except aiohttp.ClientError:
        data = {"type": "failed", "error": "unreachable"}
        if more_info is not None:
            data["more_info"] = more_info
        return data
