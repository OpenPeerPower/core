"""Tests for WebSocket API commands."""
import datetime
from unittest.mock import ANY, patch

from async_timeout import timeout
import pytest
import voluptuous as vol

from openpeerpower.bootstrap import SIGNAL_BOOTSTRAP_INTEGRATONS
from openpeerpower.components.websocket_api import const
from openpeerpower.components.websocket_api.auth import (
    TYPE_AUTH,
    TYPE_AUTH_OK,
    TYPE_AUTH_REQUIRED,
)
from openpeerpower.components.websocket_api.const import URL
from openpeerpower.core import Context, OpenPeerPower, callback
from openpeerpower.exceptions import OpenPeerPowerError
from openpeerpower.helpers import entity
from openpeerpower.helpers.dispatcher import async_dispatcher_send
from openpeerpower.loader import async_get_integration
from openpeerpower.setup import DATA_SETUP_TIME, async_setup_component

from tests.common import MockEntity, MockEntityPlatform, async_mock_service


async def test_call_service(opp, websocket_client):
    """Test call service command."""
    calls = async_mock_service(opp, "domain_test", "test_service")

    await websocket_client.send_json(
        {
            "id": 5,
            "type": "call_service",
            "domain": "domain_test",
            "service": "test_service",
            "service_data": {"hello": "world"},
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    assert len(calls) == 1
    call = calls[0]

    assert call.domain == "domain_test"
    assert call.service == "test_service"
    assert call.data == {"hello": "world"}
    assert call.context.as_dict() == msg["result"]["context"]


@pytest.mark.parametrize("command", ("call_service", "call_service_action"))
async def test_call_service_blocking(opp, websocket_client, command):
    """Test call service commands block, except for openpeerpower restart / stop."""
    with patch(
        "openpeerpower.core.ServiceRegistry.async_call", autospec=True
    ) as mock_call:
        await websocket_client.send_json(
            {
                "id": 5,
                "type": "call_service",
                "domain": "domain_test",
                "service": "test_service",
                "service_data": {"hello": "world"},
            },
        )
        msg = await websocket_client.receive_json()

    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]
    mock_call.assert_called_once_with(
        ANY,
        "domain_test",
        "test_service",
        {"hello": "world"},
        blocking=True,
        context=ANY,
        target=ANY,
    )

    with patch(
        "openpeerpower.core.ServiceRegistry.async_call", autospec=True
    ) as mock_call:
        await websocket_client.send_json(
            {
                "id": 6,
                "type": "call_service",
                "domain": "openpeerpower",
                "service": "test_service",
            },
        )
        msg = await websocket_client.receive_json()

    assert msg["id"] == 6
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]
    mock_call.assert_called_once_with(
        ANY,
        "openpeerpower",
        "test_service",
        ANY,
        blocking=True,
        context=ANY,
        target=ANY,
    )

    with patch(
        "openpeerpower.core.ServiceRegistry.async_call", autospec=True
    ) as mock_call:
        await websocket_client.send_json(
            {
                "id": 7,
                "type": "call_service",
                "domain": "openpeerpower",
                "service": "restart",
            },
        )
        msg = await websocket_client.receive_json()

    assert msg["id"] == 7
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]
    mock_call.assert_called_once_with(
        ANY, "openpeerpower", "restart", ANY, blocking=True, context=ANY, target=ANY
    )


async def test_call_service_target(opp, websocket_client):
    """Test call service command with target."""
    calls = async_mock_service(opp, "domain_test", "test_service")

    await websocket_client.send_json(
        {
            "id": 5,
            "type": "call_service",
            "domain": "domain_test",
            "service": "test_service",
            "service_data": {"hello": "world"},
            "target": {
                "entity_id": ["entity.one", "entity.two"],
                "device_id": "deviceid",
            },
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    assert len(calls) == 1
    call = calls[0]

    assert call.domain == "domain_test"
    assert call.service == "test_service"
    assert call.data == {
        "hello": "world",
        "entity_id": ["entity.one", "entity.two"],
        "device_id": ["deviceid"],
    }
    assert call.context.as_dict() == msg["result"]["context"]


async def test_call_service_target_template(opp, websocket_client):
    """Test call service command with target does not allow template."""
    await websocket_client.send_json(
        {
            "id": 5,
            "type": "call_service",
            "domain": "domain_test",
            "service": "test_service",
            "service_data": {"hello": "world"},
            "target": {
                "entity_id": "{{ 1 }}",
            },
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == const.ERR_INVALID_FORMAT


async def test_call_service_not_found(opp, websocket_client):
    """Test call service command."""
    await websocket_client.send_json(
        {
            "id": 5,
            "type": "call_service",
            "domain": "domain_test",
            "service": "test_service",
            "service_data": {"hello": "world"},
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == const.ERR_NOT_FOUND


async def test_call_service_child_not_found(opp, websocket_client):
    """Test not reporting not found errors if it's not the called service."""

    async def serv_handler(call):
        await opp.services.async_call("non", "existing")

    opp.services.async_register("domain_test", "test_service", serv_handler)

    await websocket_client.send_json(
        {
            "id": 5,
            "type": "call_service",
            "domain": "domain_test",
            "service": "test_service",
            "service_data": {"hello": "world"},
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == const.ERR_HOME_ASSISTANT_ERROR


async def test_call_service_schema_validation_error(
    opp: OpenPeerPower, websocket_client
):
    """Test call service command with invalid service data."""

    calls = []
    service_schema = vol.Schema(
        {
            vol.Required("message"): str,
        }
    )

    @callback
    def service_call(call):
        calls.append(call)

    opp.services.async_register(
        "domain_test",
        "test_service",
        service_call,
        schema=service_schema,
    )

    await websocket_client.send_json(
        {
            "id": 5,
            "type": "call_service",
            "domain": "domain_test",
            "service": "test_service",
            "service_data": {},
        }
    )
    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == const.ERR_INVALID_FORMAT

    await websocket_client.send_json(
        {
            "id": 6,
            "type": "call_service",
            "domain": "domain_test",
            "service": "test_service",
            "service_data": {"extra_key": "not allowed"},
        }
    )
    msg = await websocket_client.receive_json()
    assert msg["id"] == 6
    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == const.ERR_INVALID_FORMAT

    await websocket_client.send_json(
        {
            "id": 7,
            "type": "call_service",
            "domain": "domain_test",
            "service": "test_service",
            "service_data": {"message": []},
        }
    )
    msg = await websocket_client.receive_json()
    assert msg["id"] == 7
    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == const.ERR_INVALID_FORMAT

    assert len(calls) == 0


async def test_call_service_error(opp, websocket_client):
    """Test call service command with error."""

    @callback
    def ha_error_call(_):
        raise OpenPeerPowerError("error_message")

    opp.services.async_register("domain_test", "ha_error", ha_error_call)

    async def unknown_error_call(_):
        raise ValueError("value_error")

    opp.services.async_register("domain_test", "unknown_error", unknown_error_call)

    await websocket_client.send_json(
        {
            "id": 5,
            "type": "call_service",
            "domain": "domain_test",
            "service": "ha_error",
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"] is False
    assert msg["error"]["code"] == "open_peer_power_error"
    assert msg["error"]["message"] == "error_message"

    await websocket_client.send_json(
        {
            "id": 6,
            "type": "call_service",
            "domain": "domain_test",
            "service": "unknown_error",
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 6
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"] is False
    assert msg["error"]["code"] == "unknown_error"
    assert msg["error"]["message"] == "value_error"


async def test_subscribe_unsubscribe_events(opp, websocket_client):
    """Test subscribe/unsubscribe events command."""
    init_count = sum(opp.bus.async_listeners().values())

    await websocket_client.send_json(
        {"id": 5, "type": "subscribe_events", "event_type": "test_event"}
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    # Verify we have a new listener
    assert sum(opp.bus.async_listeners().values()) == init_count + 1

    opp.bus.async_fire("ignore_event")
    opp.bus.async_fire("test_event", {"hello": "world"})
    opp.bus.async_fire("ignore_event")

    with timeout(3):
        msg = await websocket_client.receive_json()

    assert msg["id"] == 5
    assert msg["type"] == "event"
    event = msg["event"]

    assert event["event_type"] == "test_event"
    assert event["data"] == {"hello": "world"}
    assert event["origin"] == "LOCAL"

    await websocket_client.send_json(
        {"id": 6, "type": "unsubscribe_events", "subscription": 5}
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 6
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    # Check our listener got unsubscribed
    assert sum(opp.bus.async_listeners().values()) == init_count


async def test_get_states(opp, websocket_client):
    """Test get_states command."""
    opp.states.async_set("greeting.hello", "world")
    opp.states.async_set("greeting.bye", "universe")

    await websocket_client.send_json({"id": 5, "type": "get_states"})

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    states = []
    for state in opp.states.async_all():
        states.append(state.as_dict())

    assert msg["result"] == states


async def test_get_services(opp, websocket_client):
    """Test get_services command."""
    await websocket_client.send_json({"id": 5, "type": "get_services"})

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]
    assert msg["result"] == opp.services.async_services()


async def test_get_config(opp, websocket_client):
    """Test get_config command."""
    await websocket_client.send_json({"id": 5, "type": "get_config"})

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    if "components" in msg["result"]:
        msg["result"]["components"] = set(msg["result"]["components"])
    if "whitelist_external_dirs" in msg["result"]:
        msg["result"]["whitelist_external_dirs"] = set(
            msg["result"]["whitelist_external_dirs"]
        )
    if "allowlist_external_dirs" in msg["result"]:
        msg["result"]["allowlist_external_dirs"] = set(
            msg["result"]["allowlist_external_dirs"]
        )
    if "allowlist_external_urls" in msg["result"]:
        msg["result"]["allowlist_external_urls"] = set(
            msg["result"]["allowlist_external_urls"]
        )

    assert msg["result"] == opp.config.as_dict()


async def test_ping(websocket_client):
    """Test get_panels command."""
    await websocket_client.send_json({"id": 5, "type": "ping"})

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == "pong"


async def test_call_service_context_with_user(opp, aiohttp_client, opp_access_token):
    """Test that the user is set in the service call context."""
    assert await async_setup_component(opp, "websocket_api", {})

    calls = async_mock_service(opp, "domain_test", "test_service")
    client = await aiohttp_client(opp.http.app)

    async with client.ws_connect(URL) as ws:
        auth_msg = await ws.receive_json()
        assert auth_msg["type"] == TYPE_AUTH_REQUIRED

        await ws.send_json({"type": TYPE_AUTH, "access_token": opp_access_token})

        auth_msg = await ws.receive_json()
        assert auth_msg["type"] == TYPE_AUTH_OK

        await ws.send_json(
            {
                "id": 5,
                "type": "call_service",
                "domain": "domain_test",
                "service": "test_service",
                "service_data": {"hello": "world"},
            }
        )

        msg = await ws.receive_json()
        assert msg["success"]

        refresh_token = await opp.auth.async_validate_access_token(opp_access_token)

        assert len(calls) == 1
        call = calls[0]
        assert call.domain == "domain_test"
        assert call.service == "test_service"
        assert call.data == {"hello": "world"}
        assert call.context.user_id == refresh_token.user.id


async def test_subscribe_requires_admin(websocket_client, opp_admin_user):
    """Test subscribing events without being admin."""
    opp_admin_user.groups = []
    await websocket_client.send_json(
        {"id": 5, "type": "subscribe_events", "event_type": "test_event"}
    )

    msg = await websocket_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == const.ERR_UNAUTHORIZED


async def test_states_filters_visible(opp, opp_admin_user, websocket_client):
    """Test we only get entities that we're allowed to see."""
    opp_admin_user.mock_policy({"entities": {"entity_ids": {"test.entity": True}}})
    opp.states.async_set("test.entity", "hello")
    opp.states.async_set("test.not_visible_entity", "invisible")
    await websocket_client.send_json({"id": 5, "type": "get_states"})

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    assert len(msg["result"]) == 1
    assert msg["result"][0]["entity_id"] == "test.entity"


async def test_get_states_not_allows_nan(opp, websocket_client):
    """Test get_states command not allows NaN floats."""
    opp.states.async_set("greeting.hello", "world", {"hello": float("NaN")})

    await websocket_client.send_json({"id": 5, "type": "get_states"})

    msg = await websocket_client.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == const.ERR_UNKNOWN_ERROR


async def test_subscribe_unsubscribe_events_whitelist(
    opp, websocket_client, opp_admin_user
):
    """Test subscribe/unsubscribe events on whitelist."""
    opp_admin_user.groups = []

    await websocket_client.send_json(
        {"id": 5, "type": "subscribe_events", "event_type": "not-in-whitelist"}
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == "unauthorized"

    await websocket_client.send_json(
        {"id": 6, "type": "subscribe_events", "event_type": "themes_updated"}
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 6
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    opp.bus.async_fire("themes_updated")

    with timeout(3):
        msg = await websocket_client.receive_json()

    assert msg["id"] == 6
    assert msg["type"] == "event"
    event = msg["event"]
    assert event["event_type"] == "themes_updated"
    assert event["origin"] == "LOCAL"


async def test_subscribe_unsubscribe_events_state_changed(
    opp, websocket_client, opp_admin_user
):
    """Test subscribe/unsubscribe state_changed events."""
    opp_admin_user.groups = []
    opp_admin_user.mock_policy({"entities": {"entity_ids": {"light.permitted": True}}})

    await websocket_client.send_json(
        {"id": 7, "type": "subscribe_events", "event_type": "state_changed"}
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 7
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    opp.states.async_set("light.not_permitted", "on")
    opp.states.async_set("light.permitted", "on")

    msg = await websocket_client.receive_json()
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"]["event_type"] == "state_changed"
    assert msg["event"]["data"]["entity_id"] == "light.permitted"


async def test_render_template_renders_template(opp, websocket_client):
    """Test simple template is rendered and updated."""
    opp.states.async_set("light.test", "on")

    await websocket_client.send_json(
        {
            "id": 5,
            "type": "render_template",
            "template": "State is: {{ states('light.test') }}",
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == "event"
    event = msg["event"]
    assert event == {
        "result": "State is: on",
        "listeners": {
            "all": False,
            "domains": [],
            "entities": ["light.test"],
            "time": False,
        },
    }

    opp.states.async_set("light.test", "off")
    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == "event"
    event = msg["event"]
    assert event == {
        "result": "State is: off",
        "listeners": {
            "all": False,
            "domains": [],
            "entities": ["light.test"],
            "time": False,
        },
    }


async def test_render_template_manual_entity_ids_no_longer_needed(
    opp, websocket_client
):
    """Test that updates to specified entity ids cause a template rerender."""
    opp.states.async_set("light.test", "on")

    await websocket_client.send_json(
        {
            "id": 5,
            "type": "render_template",
            "template": "State is: {{ states('light.test') }}",
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == "event"
    event = msg["event"]
    assert event == {
        "result": "State is: on",
        "listeners": {
            "all": False,
            "domains": [],
            "entities": ["light.test"],
            "time": False,
        },
    }

    opp.states.async_set("light.test", "off")
    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == "event"
    event = msg["event"]
    assert event == {
        "result": "State is: off",
        "listeners": {
            "all": False,
            "domains": [],
            "entities": ["light.test"],
            "time": False,
        },
    }


@pytest.mark.parametrize(
    "template",
    [
        "{{ my_unknown_func() + 1 }}",
        "{{ my_unknown_var }}",
        "{{ my_unknown_var + 1 }}",
        "{{ now() | unknown_filter }}",
    ],
)
async def test_render_template_with_error(opp, websocket_client, caplog, template):
    """Test a template with an error."""
    await websocket_client.send_json(
        {"id": 5, "type": "render_template", "template": template, "strict": True}
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == const.ERR_TEMPLATE_ERROR

    assert "Template variable error" not in caplog.text
    assert "TemplateError" not in caplog.text


@pytest.mark.parametrize(
    "template",
    [
        "{{ my_unknown_func() + 1 }}",
        "{{ my_unknown_var }}",
        "{{ my_unknown_var + 1 }}",
        "{{ now() | unknown_filter }}",
    ],
)
async def test_render_template_with_timeout_and_error(
    opp, websocket_client, caplog, template
):
    """Test a template with an error with a timeout."""
    await websocket_client.send_json(
        {
            "id": 5,
            "type": "render_template",
            "template": template,
            "timeout": 5,
            "strict": True,
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == const.ERR_TEMPLATE_ERROR

    assert "Template variable error" not in caplog.text
    assert "TemplateError" not in caplog.text


async def test_render_template_error_in_template_code(opp, websocket_client, caplog):
    """Test a template that will throw in template.py."""
    await websocket_client.send_json(
        {"id": 5, "type": "render_template", "template": "{{ now() | random }}"}
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == const.ERR_TEMPLATE_ERROR

    assert "TemplateError" not in caplog.text


async def test_render_template_with_delayed_error(opp, websocket_client, caplog):
    """Test a template with an error that only happens after a state change."""
    opp.states.async_set("sensor.test", "on")
    await opp.async_block_till_done()

    template_str = """
{% if states.sensor.test.state %}
   on
{% else %}
   {{ explode + 1 }}
{% endif %}
    """

    await websocket_client.send_json(
        {"id": 5, "type": "render_template", "template": template_str}
    )
    await opp.async_block_till_done()

    msg = await websocket_client.receive_json()

    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    opp.states.async_remove("sensor.test")
    await opp.async_block_till_done()

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == "event"
    event = msg["event"]
    assert event == {
        "result": "on",
        "listeners": {
            "all": False,
            "domains": [],
            "entities": ["sensor.test"],
            "time": False,
        },
    }

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == const.ERR_TEMPLATE_ERROR

    assert "TemplateError" not in caplog.text


async def test_render_template_with_timeout(opp, websocket_client, caplog):
    """Test a template that will timeout."""

    slow_template_str = """
{% for var in range(1000) -%}
  {% for var in range(1000) -%}
    {{ var }}
  {%- endfor %}
{%- endfor %}
"""

    await websocket_client.send_json(
        {
            "id": 5,
            "type": "render_template",
            "timeout": 0.000001,
            "template": slow_template_str,
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == const.ERR_TEMPLATE_ERROR

    assert "TemplateError" not in caplog.text


async def test_render_template_returns_with_match_all(opp, websocket_client):
    """Test that a template that would match with all entities still return success."""
    await websocket_client.send_json(
        {"id": 5, "type": "render_template", "template": "State is: {{ 42 }}"}
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]


async def test_manifest_list(opp, websocket_client):
    """Test loading manifests."""
    http = await async_get_integration(opp, "http")
    websocket_api = await async_get_integration(opp, "websocket_api")

    await websocket_client.send_json({"id": 5, "type": "manifest/list"})

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]
    assert sorted(msg["result"], key=lambda manifest: manifest["domain"]) == [
        http.manifest,
        websocket_api.manifest,
    ]


async def test_manifest_get(opp, websocket_client):
    """Test getting a manifest."""
    hue = await async_get_integration(opp, "hue")

    await websocket_client.send_json(
        {"id": 6, "type": "manifest/get", "integration": "hue"}
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 6
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]
    assert msg["result"] == hue.manifest

    # Non existing
    await websocket_client.send_json(
        {"id": 7, "type": "manifest/get", "integration": "non_existing"}
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 7
    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == "not_found"


async def test_entity_source_admin(opp, websocket_client, opp_admin_user):
    """Check that we fetch sources correctly."""
    platform = MockEntityPlatform(opp)

    await platform.async_add_entities(
        [MockEntity(name="Entity 1"), MockEntity(name="Entity 2")]
    )

    # Fetch all
    await websocket_client.send_json({"id": 6, "type": "entity/source"})

    msg = await websocket_client.receive_json()
    assert msg["id"] == 6
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]
    assert msg["result"] == {
        "test_domain.entity_1": {
            "source": entity.SOURCE_PLATFORM_CONFIG,
            "domain": "test_platform",
        },
        "test_domain.entity_2": {
            "source": entity.SOURCE_PLATFORM_CONFIG,
            "domain": "test_platform",
        },
    }

    # Fetch one
    await websocket_client.send_json(
        {"id": 7, "type": "entity/source", "entity_id": ["test_domain.entity_2"]}
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 7
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]
    assert msg["result"] == {
        "test_domain.entity_2": {
            "source": entity.SOURCE_PLATFORM_CONFIG,
            "domain": "test_platform",
        },
    }

    # Fetch two
    await websocket_client.send_json(
        {
            "id": 8,
            "type": "entity/source",
            "entity_id": ["test_domain.entity_2", "test_domain.entity_1"],
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 8
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]
    assert msg["result"] == {
        "test_domain.entity_1": {
            "source": entity.SOURCE_PLATFORM_CONFIG,
            "domain": "test_platform",
        },
        "test_domain.entity_2": {
            "source": entity.SOURCE_PLATFORM_CONFIG,
            "domain": "test_platform",
        },
    }

    # Fetch non existing
    await websocket_client.send_json(
        {
            "id": 9,
            "type": "entity/source",
            "entity_id": ["test_domain.entity_2", "test_domain.non_existing"],
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 9
    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == const.ERR_NOT_FOUND

    # Mock policy
    opp_admin_user.groups = []
    opp_admin_user.mock_policy(
        {"entities": {"entity_ids": {"test_domain.entity_2": True}}}
    )

    # Fetch all
    await websocket_client.send_json({"id": 10, "type": "entity/source"})

    msg = await websocket_client.receive_json()
    assert msg["id"] == 10
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]
    assert msg["result"] == {
        "test_domain.entity_2": {
            "source": entity.SOURCE_PLATFORM_CONFIG,
            "domain": "test_platform",
        },
    }

    # Fetch unauthorized
    await websocket_client.send_json(
        {"id": 11, "type": "entity/source", "entity_id": ["test_domain.entity_1"]}
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 11
    assert msg["type"] == const.TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == const.ERR_UNAUTHORIZED


async def test_subscribe_trigger(opp, websocket_client):
    """Test subscribing to a trigger."""
    init_count = sum(opp.bus.async_listeners().values())

    await websocket_client.send_json(
        {
            "id": 5,
            "type": "subscribe_trigger",
            "trigger": {"platform": "event", "event_type": "test_event"},
            "variables": {"hello": "world"},
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    # Verify we have a new listener
    assert sum(opp.bus.async_listeners().values()) == init_count + 1

    context = Context()

    opp.bus.async_fire("ignore_event")
    opp.bus.async_fire("test_event", {"hello": "world"}, context=context)
    opp.bus.async_fire("ignore_event")

    with timeout(3):
        msg = await websocket_client.receive_json()

    assert msg["id"] == 5
    assert msg["type"] == "event"
    assert msg["event"]["context"]["id"] == context.id
    assert msg["event"]["variables"]["trigger"]["platform"] == "event"

    event = msg["event"]["variables"]["trigger"]["event"]

    assert event["event_type"] == "test_event"
    assert event["data"] == {"hello": "world"}
    assert event["origin"] == "LOCAL"

    await websocket_client.send_json(
        {"id": 6, "type": "unsubscribe_events", "subscription": 5}
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 6
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    # Check our listener got unsubscribed
    assert sum(opp.bus.async_listeners().values()) == init_count


async def test_test_condition(opp, websocket_client):
    """Test testing a condition."""
    opp.states.async_set("hello.world", "paulus")

    await websocket_client.send_json(
        {
            "id": 5,
            "type": "test_condition",
            "condition": {
                "condition": "state",
                "entity_id": "hello.world",
                "state": "paulus",
            },
            "variables": {"hello": "world"},
        }
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 5
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]
    assert msg["result"]["result"] is True


async def test_execute_script(opp, websocket_client):
    """Test testing a condition."""
    calls = async_mock_service(opp, "domain_test", "test_service")

    await websocket_client.send_json(
        {
            "id": 5,
            "type": "execute_script",
            "sequence": [
                {
                    "service": "domain_test.test_service",
                    "data": {"hello": "world"},
                }
            ],
        }
    )

    msg_no_var = await websocket_client.receive_json()
    assert msg_no_var["id"] == 5
    assert msg_no_var["type"] == const.TYPE_RESULT
    assert msg_no_var["success"]

    await websocket_client.send_json(
        {
            "id": 6,
            "type": "execute_script",
            "sequence": {
                "service": "domain_test.test_service",
                "data": {"hello": "{{ name }}"},
            },
            "variables": {"name": "From variable"},
        }
    )

    msg_var = await websocket_client.receive_json()
    assert msg_var["id"] == 6
    assert msg_var["type"] == const.TYPE_RESULT
    assert msg_var["success"]

    await opp.async_block_till_done()
    await opp.async_block_till_done()

    assert len(calls) == 2

    call = calls[0]
    assert call.domain == "domain_test"
    assert call.service == "test_service"
    assert call.data == {"hello": "world"}
    assert call.context.as_dict() == msg_no_var["result"]["context"]

    call = calls[1]
    assert call.domain == "domain_test"
    assert call.service == "test_service"
    assert call.data == {"hello": "From variable"}
    assert call.context.as_dict() == msg_var["result"]["context"]


async def test_subscribe_unsubscribe_bootstrap_integrations(
    opp, websocket_client, opp_admin_user
):
    """Test subscribe/unsubscribe bootstrap_integrations."""
    await websocket_client.send_json(
        {"id": 7, "type": "subscribe_bootstrap_integrations"}
    )

    msg = await websocket_client.receive_json()
    assert msg["id"] == 7
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]

    message = {"august": 12.5, "isy994": 12.8}

    async_dispatcher_send(opp, SIGNAL_BOOTSTRAP_INTEGRATONS, message)
    msg = await websocket_client.receive_json()
    assert msg["id"] == 7
    assert msg["type"] == "event"
    assert msg["event"] == message


async def test_integration_setup_info(opp, websocket_client, opp_admin_user):
    """Test subscribe/unsubscribe bootstrap_integrations."""
    opp.data[DATA_SETUP_TIME] = {
        "august": datetime.timedelta(seconds=12.5),
        "isy994": datetime.timedelta(seconds=12.8),
    }
    await websocket_client.send_json({"id": 7, "type": "integration/setup_info"})

    msg = await websocket_client.receive_json()
    assert msg["id"] == 7
    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]
    assert msg["result"] == [
        {"domain": "august", "seconds": 12.5},
        {"domain": "isy994", "seconds": 12.8},
    ]
