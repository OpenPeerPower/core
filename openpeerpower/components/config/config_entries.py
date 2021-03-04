"""Http views to control the config manager."""
import aiohttp.web_exceptions
import voluptuous as vol

from openpeerpower import config_entries, data_entry_flow
from openpeerpower.auth.permissions.const import CAT_CONFIG_ENTRIES, POLICY_EDIT
from openpeerpower.components import websocket_api
from openpeerpower.components.http import OpenPeerPowerView
from openpeerpower.const import HTTP_FORBIDDEN, HTTP_NOT_FOUND
from openpeerpower.core import callback
from openpeerpower.exceptions import Unauthorized
from openpeerpower.helpers.data_entry_flow import (
    FlowManagerIndexView,
    FlowManagerResourceView,
)
from openpeerpower.loader import async_get_config_flows


async def async_setup(opp):
    """Enable the Open Peer Power views."""
    opp.http.register_view(ConfigManagerEntryIndexView)
    opp.http.register_view(ConfigManagerEntryResourceView)
    opp.http.register_view(ConfigManagerEntryResourceReloadView)
    opp.http.register_view(ConfigManagerFlowIndexView(opp.config_entries.flow))
    opp.http.register_view(ConfigManagerFlowResourceView(opp.config_entries.flow))
    opp.http.register_view(ConfigManagerAvailableFlowView)

    opp.http.register_view(OptionManagerFlowIndexView(opp.config_entries.options))
    opp.http.register_view(OptionManagerFlowResourceView(opp.config_entries.options))

    opp.components.websocket_api.async_register_command(config_entry_disable)
    opp.components.websocket_api.async_register_command(config_entry_update)
    opp.components.websocket_api.async_register_command(config_entries_progress)
    opp.components.websocket_api.async_register_command(system_options_list)
    opp.components.websocket_api.async_register_command(system_options_update)
    opp.components.websocket_api.async_register_command(ignore_config_flow)

    return True


class ConfigManagerEntryIndexView(OpenPeerPowerView):
    """View to get available config entries."""

    url = "/api/config/config_entries/entry"
    name = "api:config:config_entries:entry"

    async def get(self, request):
        """List available config entries."""
        opp = request.app["opp"]

        return self.json(
            [entry_json(entry) for entry in opp.config_entries.async_entries()]
        )


class ConfigManagerEntryResourceView(OpenPeerPowerView):
    """View to interact with a config entry."""

    url = "/api/config/config_entries/entry/{entry_id}"
    name = "api:config:config_entries:entry:resource"

    async def delete(self, request, entry_id):
        """Delete a config entry."""
        if not request["opp_user"].is_admin:
            raise Unauthorized(config_entry_id=entry_id, permission="remove")

        opp = request.app["opp"]

        try:
            result = await opp.config_entries.async_remove(entry_id)
        except config_entries.UnknownEntry:
            return self.json_message("Invalid entry specified", HTTP_NOT_FOUND)

        return self.json(result)


class ConfigManagerEntryResourceReloadView(OpenPeerPowerView):
    """View to reload a config entry."""

    url = "/api/config/config_entries/entry/{entry_id}/reload"
    name = "api:config:config_entries:entry:resource:reload"

    async def post(self, request, entry_id):
        """Reload a config entry."""
        if not request["opp_user"].is_admin:
            raise Unauthorized(config_entry_id=entry_id, permission="remove")

        opp = request.app["opp"]

        try:
            result = await opp.config_entries.async_reload(entry_id)
        except config_entries.OperationNotAllowed:
            return self.json_message("Entry cannot be reloaded", HTTP_FORBIDDEN)
        except config_entries.UnknownEntry:
            return self.json_message("Invalid entry specified", HTTP_NOT_FOUND)

        return self.json({"require_restart": not result})


class ConfigManagerFlowIndexView(FlowManagerIndexView):
    """View to create config flows."""

    url = "/api/config/config_entries/flow"
    name = "api:config:config_entries:flow"

    async def get(self, request):
        """Not implemented."""
        raise aiohttp.web_exceptions.HTTPMethodNotAllowed("GET", ["POST"])

    # pylint: disable=arguments-differ
    async def post(self, request):
        """Handle a POST request."""
        if not request["opp_user"].is_admin:
            raise Unauthorized(perm_category=CAT_CONFIG_ENTRIES, permission="add")

        # pylint: disable=no-value-for-parameter
        return await super().post(request)

    def _prepare_result_json(self, result):
        """Convert result to JSON."""
        if result["type"] != data_entry_flow.RESULT_TYPE_CREATE_ENTRY:
            return super()._prepare_result_json(result)

        data = result.copy()
        data["result"] = data["result"].entry_id
        data.pop("data")
        return data


class ConfigManagerFlowResourceView(FlowManagerResourceView):
    """View to interact with the flow manager."""

    url = "/api/config/config_entries/flow/{flow_id}"
    name = "api:config:config_entries:flow:resource"

    async def get(self, request, flow_id):
        """Get the current state of a data_entry_flow."""
        if not request["opp_user"].is_admin:
            raise Unauthorized(perm_category=CAT_CONFIG_ENTRIES, permission="add")

        return await super().get(request, flow_id)

    # pylint: disable=arguments-differ
    async def post(self, request, flow_id):
        """Handle a POST request."""
        if not request["opp_user"].is_admin:
            raise Unauthorized(perm_category=CAT_CONFIG_ENTRIES, permission="add")

        # pylint: disable=no-value-for-parameter
        return await super().post(request, flow_id)

    def _prepare_result_json(self, result):
        """Convert result to JSON."""
        if result["type"] != data_entry_flow.RESULT_TYPE_CREATE_ENTRY:
            return super()._prepare_result_json(result)

        data = result.copy()
        data["result"] = data["result"].entry_id
        data.pop("data")
        return data


class ConfigManagerAvailableFlowView(OpenPeerPowerView):
    """View to query available flows."""

    url = "/api/config/config_entries/flow_handlers"
    name = "api:config:config_entries:flow_handlers"

    async def get(self, request):
        """List available flow handlers."""
        opp = request.app["opp"]
        return self.json(await async_get_config_flows(opp))


class OptionManagerFlowIndexView(FlowManagerIndexView):
    """View to create option flows."""

    url = "/api/config/config_entries/options/flow"
    name = "api:config:config_entries:option:flow"

    # pylint: disable=arguments-differ
    async def post(self, request):
        """Handle a POST request.

        handler in request is entry_id.
        """
        if not request["opp_user"].is_admin:
            raise Unauthorized(perm_category=CAT_CONFIG_ENTRIES, permission=POLICY_EDIT)

        # pylint: disable=no-value-for-parameter
        return await super().post(request)


class OptionManagerFlowResourceView(FlowManagerResourceView):
    """View to interact with the option flow manager."""

    url = "/api/config/config_entries/options/flow/{flow_id}"
    name = "api:config:config_entries:options:flow:resource"

    async def get(self, request, flow_id):
        """Get the current state of a data_entry_flow."""
        if not request["opp_user"].is_admin:
            raise Unauthorized(perm_category=CAT_CONFIG_ENTRIES, permission=POLICY_EDIT)

        return await super().get(request, flow_id)

    # pylint: disable=arguments-differ
    async def post(self, request, flow_id):
        """Handle a POST request."""
        if not request["opp_user"].is_admin:
            raise Unauthorized(perm_category=CAT_CONFIG_ENTRIES, permission=POLICY_EDIT)

        # pylint: disable=no-value-for-parameter
        return await super().post(request, flow_id)


@websocket_api.require_admin
@websocket_api.websocket_command({"type": "config_entries/flow/progress"})
def config_entries_progress(opp, connection, msg):
    """List flows that are in progress but not started by a user.

    Example of a non-user initiated flow is a discovered Hue hub that
    requires user interaction to finish setup.
    """
    connection.send_result(
        msg["id"],
        [
            flw
            for flw in opp.config_entries.flow.async_progress()
            if flw["context"]["source"] != config_entries.SOURCE_USER
        ],
    )


@websocket_api.require_admin
@websocket_api.async_response
@websocket_api.websocket_command(
    {"type": "config_entries/system_options/list", "entry_id": str}
)
async def system_options_list(opp, connection, msg):
    """List all system options for a config entry."""
    entry_id = msg["entry_id"]
    entry = opp.config_entries.async_get_entry(entry_id)

    if entry:
        connection.send_result(msg["id"], entry.system_options.as_dict())


def send_entry_not_found(connection, msg_id):
    """Send Config entry not found error."""
    connection.send_error(
        msg_id, websocket_api.const.ERR_NOT_FOUND, "Config entry not found"
    )


def get_entry(opp, connection, entry_id, msg_id):
    """Get entry, send error message if it doesn't exist."""
    entry = opp.config_entries.async_get_entry(entry_id)
    if entry is None:
        send_entry_not_found(connection, msg_id)
    return entry


@websocket_api.require_admin
@websocket_api.async_response
@websocket_api.websocket_command(
    {
        "type": "config_entries/system_options/update",
        "entry_id": str,
        vol.Optional("disable_new_entities"): bool,
    }
)
async def system_options_update(opp, connection, msg):
    """Update config entry system options."""
    changes = dict(msg)
    changes.pop("id")
    changes.pop("type")
    changes.pop("entry_id")

    entry = get_entry(opp, connection, msg["entry_id"], msg["id"])
    if entry is None:
        return

    opp.config_entries.async_update_entry(entry, system_options=changes)
    connection.send_result(msg["id"], entry.system_options.as_dict())


@websocket_api.require_admin
@websocket_api.async_response
@websocket_api.websocket_command(
    {"type": "config_entries/update", "entry_id": str, vol.Optional("title"): str}
)
async def config_entry_update(opp, connection, msg):
    """Update config entry."""
    changes = dict(msg)
    changes.pop("id")
    changes.pop("type")
    changes.pop("entry_id")

    entry = get_entry(opp, connection, msg["entry_id"], msg["id"])
    if entry is None:
        return

    opp.config_entries.async_update_entry(entry, **changes)
    connection.send_result(msg["id"], entry_json(entry))


@websocket_api.require_admin
@websocket_api.async_response
@websocket_api.websocket_command(
    {
        "type": "config_entries/disable",
        "entry_id": str,
        # We only allow setting disabled_by user via API.
        "disabled_by": vol.Any("user", None),
    }
)
async def config_entry_disable(opp, connection, msg):
    """Disable config entry."""
    disabled_by = msg["disabled_by"]

    result = False
    try:
        result = await opp.config_entries.async_set_disabled_by(
            msg["entry_id"], disabled_by
        )
    except config_entries.OperationNotAllowed:
        # Failed to unload the config entry
        pass
    except config_entries.UnknownEntry:
        send_entry_not_found(connection, msg["id"])
        return

    result = {"require_restart": not result}

    connection.send_result(msg["id"], result)


@websocket_api.require_admin
@websocket_api.async_response
@websocket_api.websocket_command(
    {"type": "config_entries/ignore_flow", "flow_id": str, "title": str}
)
async def ignore_config_flow(opp, connection, msg):
    """Ignore a config flow."""
    flow = next(
        (
            flw
            for flw in opp.config_entries.flow.async_progress()
            if flw["flow_id"] == msg["flow_id"]
        ),
        None,
    )

    if flow is None:
        send_entry_not_found(connection, msg["id"])
        return

    if "unique_id" not in flow["context"]:
        connection.send_error(
            msg["id"], "no_unique_id", "Specified flow has no unique ID."
        )
        return

    await opp.config_entries.flow.async_init(
        flow["handler"],
        context={"source": config_entries.SOURCE_IGNORE},
        data={"unique_id": flow["context"]["unique_id"], "title": msg["title"]},
    )
    connection.send_result(msg["id"])


@callback
def entry_json(entry: config_entries.ConfigEntry) -> dict:
    """Return JSON value of a config entry."""
    handler = config_entries.HANDLERS.get(entry.domain)
    supports_options = (
        # Guard in case handler is no longer registered (custom component etc)
        handler is not None
        # pylint: disable=comparison-with-callable
        and handler.async_get_options_flow
        != config_entries.ConfigFlow.async_get_options_flow
    )
    return {
        "entry_id": entry.entry_id,
        "domain": entry.domain,
        "title": entry.title,
        "source": entry.source,
        "state": entry.state,
        "connection_class": entry.connection_class,
        "supports_options": supports_options,
        "supports_unload": entry.supports_unload,
        "disabled_by": entry.disabled_by,
    }
