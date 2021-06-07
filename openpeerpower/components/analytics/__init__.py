"""Send instance and usage analytics."""
import voluptuous as vol

from openpeerpower.components import websocket_api
from openpeerpower.const import EVENT_OPENPEERPOWER_STARTED
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.event import async_call_later, async_track_time_interval

from .analytics import Analytics
from .const import ATTR_ONBOARDED, ATTR_PREFERENCES, DOMAIN, INTERVAL, PREFERENCE_SCHEMA


async def async_setup(opp: OpenPeerPower, _):
    """Set up the analytics integration."""
    analytics = Analytics(opp)

    # Load stored data
    await analytics.load()

    async def start_schedule(_event):
        """Start the send schedule after the started event."""
        # Wait 15 min after started
        async_call_later(opp, 900, analytics.send_analytics)

        # Send every day
        async_track_time_interval(opp, analytics.send_analytics, INTERVAL)

    opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STARTED, start_schedule)

    websocket_api.async_register_command(opp, websocket_analytics)
    websocket_api.async_register_command(opp, websocket_analytics_preferences)

    opp.data[DOMAIN] = analytics
    return True


@websocket_api.require_admin
@websocket_api.async_response
@websocket_api.websocket_command({vol.Required("type"): "analytics"})
async def websocket_analytics(
    opp: OpenPeerPower,
    connection: websocket_api.connection.ActiveConnection,
    msg: dict,
) -> None:
    """Return analytics preferences."""
    analytics: Analytics = opp.data[DOMAIN]
    connection.send_result(
        msg["id"],
        {ATTR_PREFERENCES: analytics.preferences, ATTR_ONBOARDED: analytics.onboarded},
    )


@websocket_api.require_admin
@websocket_api.async_response
@websocket_api.websocket_command(
    {
        vol.Required("type"): "analytics/preferences",
        vol.Required("preferences", default={}): PREFERENCE_SCHEMA,
    }
)
async def websocket_analytics_preferences(
    opp: OpenPeerPower,
    connection: websocket_api.connection.ActiveConnection,
    msg: dict,
) -> None:
    """Update analytics preferences."""
    preferences = msg[ATTR_PREFERENCES]
    analytics: Analytics = opp.data[DOMAIN]

    await analytics.save_preferences(preferences)
    await analytics.send_analytics()

    connection.send_result(
        msg["id"],
        {ATTR_PREFERENCES: analytics.preferences},
    )
