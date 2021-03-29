"""Commands part of Websocket API."""
import asyncio

import voluptuous as vol

from openpeerpower.auth.permissions.const import CAT_ENTITIES, POLICY_READ
from openpeerpower.components.websocket_api.const import ERR_NOT_FOUND
from openpeerpower.const import EVENT_STATE_CHANGED, EVENT_TIME_CHANGED, MATCH_ALL
from openpeerpower.core import DOMAIN as OPP_DOMAIN, callback
from openpeerpower.exceptions import (
    OpenPeerPowerError,
    ServiceNotFound,
    TemplateError,
    Unauthorized,
)
from openpeerpower.helpers import config_validation as cv, entity
from openpeerpower.helpers.event import TrackTemplate, async_track_template_result
from openpeerpower.helpers.service import async_get_all_descriptions
from openpeerpower.helpers.template import Template
from openpeerpower.loader import IntegrationNotFound, async_get_integration

from . import const, decorators, messages

# mypy: allow-untyped-calls, allow-untyped-defs


@callback
def async_register_commands(opp, async_reg):
    """Register commands."""
    async_reg(opp, handle_subscribe_events)
    async_reg(opp, handle_unsubscribe_events)
    async_reg(opp, handle_call_service)
    async_reg(opp, handle_get_states)
    async_reg(opp, handle_get_services)
    async_reg(opp, handle_get_config)
    async_reg(opp, handle_ping)
    async_reg(opp, handle_render_template)
    async_reg(opp, handle_manifest_list)
    async_reg(opp, handle_manifest_get)
    async_reg(opp, handle_entity_source)
    async_reg(opp, handle_subscribe_trigger)
    async_reg(opp, handle_test_condition)


def pong_message(iden):
    """Return a pong message."""
    return {"id": iden, "type": "pong"}


@callback
@decorators.websocket_command(
    {
        vol.Required("type"): "subscribe_events",
        vol.Optional("event_type", default=MATCH_ALL): str,
    }
)
def handle_subscribe_events(opp, connection, msg):
    """Handle subscribe events command."""
    # Circular dep
    # pylint: disable=import-outside-toplevel
    from .permissions import SUBSCRIBE_ALLOWLIST

    event_type = msg["event_type"]

    if event_type not in SUBSCRIBE_ALLOWLIST and not connection.user.is_admin:
        raise Unauthorized

    if event_type == EVENT_STATE_CHANGED:

        @callback
        def forward_events(event):
            """Forward state changed events to websocket."""
            if not connection.user.permissions.check_entity(
                event.data["entity_id"], POLICY_READ
            ):
                return

            connection.send_message(messages.cached_event_message(msg["id"], event))

    else:

        @callback
        def forward_events(event):
            """Forward events to websocket."""
            if event.event_type == EVENT_TIME_CHANGED:
                return

            connection.send_message(messages.cached_event_message(msg["id"], event))

    connection.subscriptions[msg["id"]] = opp.bus.async_listen(
        event_type, forward_events
    )

    connection.send_message(messages.result_message(msg["id"]))


@callback
@decorators.websocket_command(
    {
        vol.Required("type"): "unsubscribe_events",
        vol.Required("subscription"): cv.positive_int,
    }
)
def handle_unsubscribe_events(opp, connection, msg):
    """Handle unsubscribe events command."""
    subscription = msg["subscription"]

    if subscription in connection.subscriptions:
        connection.subscriptions.pop(subscription)()
        connection.send_message(messages.result_message(msg["id"]))
    else:
        connection.send_message(
            messages.error_message(
                msg["id"], const.ERR_NOT_FOUND, "Subscription not found."
            )
        )


@decorators.websocket_command(
    {
        vol.Required("type"): "call_service",
        vol.Required("domain"): str,
        vol.Required("service"): str,
        vol.Optional("target"): cv.ENTITY_SERVICE_FIELDS,
        vol.Optional("service_data"): dict,
    }
)
@decorators.async_response
async def handle_call_service(opp, connection, msg):
    """Handle call service command."""
    blocking = True
    if msg["domain"] == OPP_DOMAIN and msg["service"] in ["restart", "stop"]:
        blocking = False

    try:
        context = connection.context(msg)
        await opp.services.async_call(
            msg["domain"],
            msg["service"],
            msg.get("service_data"),
            blocking,
            context,
            target=msg.get("target"),
        )
        connection.send_message(
            messages.result_message(msg["id"], {"context": context})
        )
    except ServiceNotFound as err:
        if err.domain == msg["domain"] and err.service == msg["service"]:
            connection.send_message(
                messages.error_message(
                    msg["id"], const.ERR_NOT_FOUND, "Service not found."
                )
            )
        else:
            connection.send_message(
                messages.error_message(
                    msg["id"], const.ERR_OPEN_PEER_POWER_ERROR, str(err)
                )
            )
    except vol.Invalid as err:
        connection.send_message(
            messages.error_message(msg["id"], const.ERR_INVALID_FORMAT, str(err))
        )
    except OpenPeerPowerError as err:
        connection.logger.exception(err)
        connection.send_message(
            messages.error_message(msg["id"], const.ERR_OPEN_PEER_POWER_ERROR, str(err))
        )
    except Exception as err:  # pylint: disable=broad-except
        connection.logger.exception(err)
        connection.send_message(
            messages.error_message(msg["id"], const.ERR_UNKNOWN_ERROR, str(err))
        )


@callback
@decorators.websocket_command({vol.Required("type"): "get_states"})
def handle_get_states(opp, connection, msg):
    """Handle get states command."""
    if connection.user.permissions.access_all_entities("read"):
        states = opp.states.async_all()
    else:
        entity_perm = connection.user.permissions.check_entity
        states = [
            state
            for state in opp.states.async_all()
            if entity_perm(state.entity_id, "read")
        ]

    connection.send_message(messages.result_message(msg["id"], states))


@decorators.websocket_command({vol.Required("type"): "get_services"})
@decorators.async_response
async def handle_get_services(opp, connection, msg):
    """Handle get services command."""
    descriptions = await async_get_all_descriptions(opp)
    connection.send_message(messages.result_message(msg["id"], descriptions))


@callback
@decorators.websocket_command({vol.Required("type"): "get_config"})
def handle_get_config(opp, connection, msg):
    """Handle get config command."""
    connection.send_message(messages.result_message(msg["id"], opp.config.as_dict()))


@decorators.websocket_command({vol.Required("type"): "manifest/list"})
@decorators.async_response
async def handle_manifest_list(opp, connection, msg):
    """Handle integrations command."""
    integrations = await asyncio.gather(
        *[
            async_get_integration(opp, domain)
            for domain in opp.config.components
            # Filter out platforms.
            if "." not in domain
        ]
    )
    connection.send_result(
        msg["id"], [integration.manifest for integration in integrations]
    )


@decorators.websocket_command(
    {vol.Required("type"): "manifest/get", vol.Required("integration"): str}
)
@decorators.async_response
async def handle_manifest_get(opp, connection, msg):
    """Handle integrations command."""
    try:
        integration = await async_get_integration(opp, msg["integration"])
        connection.send_result(msg["id"], integration.manifest)
    except IntegrationNotFound:
        connection.send_error(msg["id"], const.ERR_NOT_FOUND, "Integration not found")


@callback
@decorators.websocket_command({vol.Required("type"): "ping"})
def handle_ping(opp, connection, msg):
    """Handle ping command."""
    connection.send_message(pong_message(msg["id"]))


@decorators.websocket_command(
    {
        vol.Required("type"): "render_template",
        vol.Required("template"): str,
        vol.Optional("entity_ids"): cv.entity_ids,
        vol.Optional("variables"): dict,
        vol.Optional("timeout"): vol.Coerce(float),
    }
)
@decorators.async_response
async def handle_render_template(opp, connection, msg):
    """Handle render_template command."""
    template_str = msg["template"]
    template = Template(template_str, opp)
    variables = msg.get("variables")
    timeout = msg.get("timeout")
    info = None

    if timeout:
        try:
            timed_out = await template.async_render_will_timeout(timeout)
        except TemplateError as ex:
            connection.send_error(msg["id"], const.ERR_TEMPLATE_ERROR, str(ex))
            return

        if timed_out:
            connection.send_error(
                msg["id"],
                const.ERR_TEMPLATE_ERROR,
                f"Exceeded maximum execution time of {timeout}s",
            )
            return

    @callback
    def _template_listener(event, updates):
        nonlocal info
        track_template_result = updates.pop()
        result = track_template_result.result
        if isinstance(result, TemplateError):
            connection.send_error(msg["id"], const.ERR_TEMPLATE_ERROR, str(result))
            return

        connection.send_message(
            messages.event_message(
                msg["id"], {"result": result, "listeners": info.listeners}  # type: ignore
            )
        )

    try:
        info = async_track_template_result(
            opp,
            [TrackTemplate(template, variables)],
            _template_listener,
            raise_on_template_error=True,
        )
    except TemplateError as ex:
        connection.send_error(msg["id"], const.ERR_TEMPLATE_ERROR, str(ex))
        return

    connection.subscriptions[msg["id"]] = info.async_remove

    connection.send_result(msg["id"])

    opp.loop.call_soon_threadsafe(info.async_refresh)


@callback
@decorators.websocket_command(
    {vol.Required("type"): "entity/source", vol.Optional("entity_id"): [cv.entity_id]}
)
def handle_entity_source(opp, connection, msg):
    """Handle entity source command."""
    raw_sources = entity.entity_sources(opp)
    entity_perm = connection.user.permissions.check_entity

    if "entity_id" not in msg:
        if connection.user.permissions.access_all_entities("read"):
            sources = raw_sources
        else:
            sources = {
                entity_id: source
                for entity_id, source in raw_sources.items()
                if entity_perm(entity_id, "read")
            }

        connection.send_message(messages.result_message(msg["id"], sources))
        return

    sources = {}

    for entity_id in msg["entity_id"]:
        if not entity_perm(entity_id, "read"):
            raise Unauthorized(
                context=connection.context(msg),
                permission=POLICY_READ,
                perm_category=CAT_ENTITIES,
            )

        source = raw_sources.get(entity_id)

        if source is None:
            connection.send_error(msg["id"], ERR_NOT_FOUND, "Entity not found")
            return

        sources[entity_id] = source

    connection.send_result(msg["id"], sources)


@callback
@decorators.websocket_command(
    {
        vol.Required("type"): "subscribe_trigger",
        vol.Required("trigger"): cv.TRIGGER_SCHEMA,
        vol.Optional("variables"): dict,
    }
)
@decorators.require_admin
@decorators.async_response
async def handle_subscribe_trigger(opp, connection, msg):
    """Handle subscribe trigger command."""
    # Circular dep
    # pylint: disable=import-outside-toplevel
    from openpeerpower.helpers import trigger

    trigger_config = await trigger.async_validate_trigger_config(opp, msg["trigger"])

    @callback
    def forward_triggers(variables, context=None):
        """Forward events to websocket."""
        connection.send_message(
            messages.event_message(
                msg["id"], {"variables": variables, "context": context}
            )
        )

    connection.subscriptions[msg["id"]] = (
        await trigger.async_initialize_triggers(
            opp,
            trigger_config,
            forward_triggers,
            const.DOMAIN,
            const.DOMAIN,
            connection.logger.log,
            variables=msg.get("variables"),
        )
    ) or (
        # Some triggers won't return an unsub function. Since the caller expects
        # a subscription, we're going to fake one.
        lambda: None
    )
    connection.send_result(msg["id"])


@decorators.websocket_command(
    {
        vol.Required("type"): "test_condition",
        vol.Required("condition"): cv.CONDITION_SCHEMA,
        vol.Optional("variables"): dict,
    }
)
@decorators.require_admin
@decorators.async_response
async def handle_test_condition(opp, connection, msg):
    """Handle test condition command."""
    # Circular dep
    # pylint: disable=import-outside-toplevel
    from openpeerpower.helpers import condition

    check_condition = await condition.async_from_config(opp, msg["condition"])
    connection.send_result(
        msg["id"], {"result": check_condition(opp, msg.get("variables"))}
    )
