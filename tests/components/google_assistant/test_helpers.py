"""Test Google Assistant helpers."""
from datetime import timedelta
from unittest.mock import Mock, call, patch

import pytest

from openpeerpower.components.google_assistant import helpers
from openpeerpower.components.google_assistant.const import (  # noqa: F401
    EVENT_COMMAND_RECEIVED,
    NOT_EXPOSE_LOCAL,
)
from openpeerpower.config import async_process_op_core_config
from openpeerpower.core import State
from openpeerpower.setup import async_setup_component
from openpeerpower.util import dt

from . import MockConfig

from tests.common import (
    async_capture_events,
    async_fire_time_changed,
    async_mock_service,
)


async def test_google_entity_sync_serialize_with_local_sdk(opp):
    """Test sync serialize attributes of a GoogleEntity."""
    opp.states.async_set("light.ceiling_lights", "off")
    opp.config.api = Mock(port=1234, use_ssl=True)
    await async_process_op_core_config(
        opp,
        {"external_url": "https://hostname:1234"},
    )

    opp.http = Mock(server_port=1234)
    config = MockConfig(
        opp=opp,
        local_sdk_webhook_id="mock-webhook-id",
        local_sdk_user_id="mock-user-id",
    )
    entity = helpers.GoogleEntity.opp, config, opp.states.get("light.ceiling_lights"))

    serialized = await entity.sync_serialize(None)
    assert "otherDeviceIds" not in serialized
    assert "customData" not in serialized

    config.async_enable_local_sdk()

    with patch("openpeerpower.helpers.instance_id.async_get", return_value="abcdef"):
        serialized = await entity.sync_serialize(None)
        assert serialized["otherDeviceIds"] == [{"deviceId": "light.ceiling_lights"}]
        assert serialized["customData"] == {
            "httpPort": 1234,
            "httpSSL": True,
            "proxyDeviceId": None,
            "webhookId": "mock-webhook-id",
            "baseUrl": "https://hostname:1234",
            "uuid": "abcdef",
        }

    for device_type in NOT_EXPOSE_LOCAL:
        with patch(
            "openpeerpower.components.google_assistant.helpers.get_google_type",
            return_value=device_type,
        ):
            serialized = await entity.sync_serialize(None)
            assert "otherDeviceIds" not in serialized
            assert "customData" not in serialized


async def test_config_local_sdk(opp, opp_client):
    """Test the local SDK."""
    command_events = async_capture_events(opp, EVENT_COMMAND_RECEIVED)
    turn_on_calls = async_mock_service(opp, "light", "turn_on")
    opp.states.async_set("light.ceiling_lights", "off")

    assert await async_setup_component(opp, "webhook", {})

    config = MockConfig(
        opp=opp,
        local_sdk_webhook_id="mock-webhook-id",
        local_sdk_user_id="mock-user-id",
    )

    client = await opp_client()

    config.async_enable_local_sdk()

    resp = await client.post(
        "/api/webhook/mock-webhook-id",
        json={
            "inputs": [
                {
                    "context": {"locale_country": "US", "locale_language": "en"},
                    "intent": "action.devices.EXECUTE",
                    "payload": {
                        "commands": [
                            {
                                "devices": [{"id": "light.ceiling_lights"}],
                                "execution": [
                                    {
                                        "command": "action.devices.commands.OnOff",
                                        "params": {"on": True},
                                    }
                                ],
                            }
                        ],
                        "structureData": {},
                    },
                }
            ],
            "requestId": "mock-req-id",
        },
    )
    assert resp.status == 200
    result = await resp.json()
    assert result["requestId"] == "mock-req-id"

    assert len(command_events) == 1
    assert command_events[0].context.user_id == config.local_sdk_user_id

    assert len(turn_on_calls) == 1
    assert turn_on_calls[0].context is command_events[0].context

    config.async_disable_local_sdk()

    # Webhook is no longer active
    resp = await client.post("/api/webhook/mock-webhook-id")
    assert resp.status == 200
    assert await resp.read() == b""


async def test_config_local_sdk_if_disabled(opp, opp_client):
    """Test the local SDK."""
    assert await async_setup_component(opp, "webhook", {})

    config = MockConfig(
        opp=opp,
        local_sdk_webhook_id="mock-webhook-id",
        local_sdk_user_id="mock-user-id",
        enabled=False,
    )

    client = await opp_client()

    config.async_enable_local_sdk()

    resp = await client.post(
        "/api/webhook/mock-webhook-id", json={"requestId": "mock-req-id"}
    )
    assert resp.status == 200
    result = await resp.json()
    assert result == {
        "payload": {"errorCode": "deviceTurnedOff"},
        "requestId": "mock-req-id",
    }

    config.async_disable_local_sdk()

    # Webhook is no longer active
    resp = await client.post("/api/webhook/mock-webhook-id")
    assert resp.status == 200
    assert await resp.read() == b""


async def test_agent_user_id_storage(opp, opp_storage):
    """Test a disconnect message."""

    opp.storage["google_assistant"] = {
        "version": 1,
        "key": "google_assistant",
        "data": {"agent_user_ids": {"agent_1": {}}},
    }

    store = helpers.GoogleConfigStore(opp)
    await store.async_load()

    assert opp_storage["google_assistant"] == {
        "version": 1,
        "key": "google_assistant",
        "data": {"agent_user_ids": {"agent_1": {}}},
    }

    async def _check_after_delay(data):
        async_fire_time_changed(opp, dt.utcnow() + timedelta(seconds=2))
        await opp.async_block_till_done()

        assert opp_storage["google_assistant"] == {
            "version": 1,
            "key": "google_assistant",
            "data": data,
        }

    store.add_agent_user_id("agent_2")
    await _check_after_delay({"agent_user_ids": {"agent_1": {}, "agent_2": {}}})

    store.pop_agent_user_id("agent_1")
    await _check_after_delay({"agent_user_ids": {"agent_2": {}}})


async def test_agent_user_id_connect():
    """Test the connection and disconnection of users."""
    config = MockConfig()
    store = config._store

    await config.async_connect_agent_user("agent_2")
    assert store.add_agent_user_id.call_args == call("agent_2")

    await config.async_connect_agent_user("agent_1")
    assert store.add_agent_user_id.call_args == call("agent_1")

    await config.async_disconnect_agent_user("agent_2")
    assert store.pop_agent_user_id.call_args == call("agent_2")

    await config.async_disconnect_agent_user("agent_1")
    assert store.pop_agent_user_id.call_args == call("agent_1")


@pytest.mark.parametrize("agents", [{}, {"1"}, {"1", "2"}])
async def test_report_state_all(agents):
    """Test a disconnect message."""
    config = MockConfig(agent_user_ids=agents)
    data = {}
    with patch.object(config, "async_report_state") as mock:
        await config.async_report_state_all(data)
        assert sorted(mock.mock_calls) == sorted(
            [call(data, agent) for agent in agents]
        )


@pytest.mark.parametrize(
    "agents, result",
    [({}, 204), ({"1": 200}, 200), ({"1": 200, "2": 300}, 300)],
)
async def test_sync_entities_all(agents, result):
    """Test sync entities ."""
    config = MockConfig(agent_user_ids=set(agents.keys()))
    with patch.object(
        config,
        "async_sync_entities",
        side_effect=lambda agent_user_id: agents[agent_user_id],
    ) as mock:
        res = await config.async_sync_entities_all()
        assert sorted(mock.mock_calls) == sorted([call(agent) for agent in agents])
        assert res == result


def test_supported_features_string(caplog):
    """Test bad supported features."""
    entity = helpers.GoogleEntity(
        None, None, State("test.entity_id", "on", {"supported_features": "invalid"})
    )
    assert entity.is_supported() is False
    assert "Entity test.entity_id contains invalid supported_features value invalid"
