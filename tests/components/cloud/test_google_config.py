"""Test the Cloud Google Config."""
from unittest.mock import AsyncMock, Mock, patch

import pytest

from openpeerpower.components.cloud import GACTIONS_SCHEMA
from openpeerpower.components.cloud.google_config import CloudGoogleConfig
from openpeerpower.components.google_assistant import helpers as ga_helpers
from openpeerpower.const import EVENT_OPENPEERPOWER_STARTED, HTTP_NOT_FOUND
from openpeerpowerr.core import CoreState, State
from openpeerpowerr.helpers.entity_registry import EVENT_ENTITY_REGISTRY_UPDATED
from openpeerpowerr.util.dt import utcnow

from tests.common import async_fire_time_changed


@pytest.fixture
def mock_conf.opp, cloud_prefs):
    """Mock Google conf."""
    return CloudGoogleConfig(
       .opp,
        GACTIONS_SCHEMA({}),
        "mock-user-id",
        cloud_prefs,
        Mock(claims={"cognito:username": "abcdefghjkl"}),
    )


async def test_google_update_report_state(mock_conf,.opp, cloud_prefs):
    """Test Google config responds to updating preference."""
    await mock_conf.async_initialize()
    await mock_conf.async_connect_agent_user("mock-user-id")

    with patch.object(mock_conf, "async_sync_entities") as mock_sync, patch(
        "openpeerpower.components.google_assistant.report_state.async_enable_report_state"
    ) as mock_report_state:
        await cloud_prefs.async_update(google_report_state=True)
        await.opp.async_block_till_done()

    assert len(mock_sync.mock_calls) == 1
    assert len(mock_report_state.mock_calls) == 1


async def test_sync_entities(aioclient_mock,.opp, cloud_prefs):
    """Test sync devices."""
    config = CloudGoogleConfig(
       .opp,
        GACTIONS_SCHEMA({}),
        "mock-user-id",
        cloud_prefs,
        Mock(auth=Mock(async_check_token=AsyncMock())),
    )

    with patch(
        "opp_nabucasa.cloud_api.async_google_actions_request_sync",
        return_value=Mock(status=HTTP_NOT_FOUND),
    ) as mock_request_sync:
        assert await config.async_sync_entities("user") == HTTP_NOT_FOUND
        assert len(mock_request_sync.mock_calls) == 1


async def test_google_update_expose_trigger_sync(
   .opp, legacy_patchable_time, cloud_prefs
):
    """Test Google config responds to updating exposed entities."""
    config = CloudGoogleConfig(
       .opp,
        GACTIONS_SCHEMA({}),
        "mock-user-id",
        cloud_prefs,
        Mock(claims={"cognito:username": "abcdefghjkl"}),
    )
    await config.async_initialize()
    await config.async_connect_agent_user("mock-user-id")

    with patch.object(config, "async_sync_entities") as mock_sync, patch.object(
        ga_helpers, "SYNC_DELAY", 0
    ):
        await cloud_prefs.async_update_google_entity_config(
            entity_id="light.kitchen", should_expose=True
        )
        await.opp.async_block_till_done()
        async_fire_time_changed.opp, utcnow())
        await.opp.async_block_till_done()

    assert len(mock_sync.mock_calls) == 1

    with patch.object(config, "async_sync_entities") as mock_sync, patch.object(
        ga_helpers, "SYNC_DELAY", 0
    ):
        await cloud_prefs.async_update_google_entity_config(
            entity_id="light.kitchen", should_expose=False
        )
        await cloud_prefs.async_update_google_entity_config(
            entity_id="binary_sensor.door", should_expose=True
        )
        await cloud_prefs.async_update_google_entity_config(
            entity_id="sensor.temp", should_expose=True
        )
        await.opp.async_block_till_done()
        async_fire_time_changed.opp, utcnow())
        await.opp.async_block_till_done()

    assert len(mock_sync.mock_calls) == 1


async def test_google_entity_registry_sync.opp, mock_cloud_login, cloud_prefs):
    """Test Google config responds to entity registry."""
    config = CloudGoogleConfig(
       .opp, GACTIONS_SCHEMA({}), "mock-user-id", cloud_prefs,.opp.data["cloud"]
    )
    await config.async_initialize()
    await config.async_connect_agent_user("mock-user-id")

    with patch.object(
        config, "async_schedule_google_sync_all"
    ) as mock_sync, patch.object(ga_helpers, "SYNC_DELAY", 0):
        # Created entity
       .opp.bus.async_fire(
            EVENT_ENTITY_REGISTRY_UPDATED,
            {"action": "create", "entity_id": "light.kitchen"},
        )
        await.opp.async_block_till_done()

        assert len(mock_sync.mock_calls) == 1

        # Removed entity
       .opp.bus.async_fire(
            EVENT_ENTITY_REGISTRY_UPDATED,
            {"action": "remove", "entity_id": "light.kitchen"},
        )
        await.opp.async_block_till_done()

        assert len(mock_sync.mock_calls) == 2

        # Entity registry updated with relevant changes
       .opp.bus.async_fire(
            EVENT_ENTITY_REGISTRY_UPDATED,
            {
                "action": "update",
                "entity_id": "light.kitchen",
                "changes": ["entity_id"],
            },
        )
        await.opp.async_block_till_done()

        assert len(mock_sync.mock_calls) == 3

        # Entity registry updated with non-relevant changes
       .opp.bus.async_fire(
            EVENT_ENTITY_REGISTRY_UPDATED,
            {"action": "update", "entity_id": "light.kitchen", "changes": ["icon"]},
        )
        await.opp.async_block_till_done()

        assert len(mock_sync.mock_calls) == 3

        # When opp is not started yet we wait till started
       .opp.state = CoreState.starting
       .opp.bus.async_fire(
            EVENT_ENTITY_REGISTRY_UPDATED,
            {"action": "create", "entity_id": "light.kitchen"},
        )
        await.opp.async_block_till_done()

        assert len(mock_sync.mock_calls) == 3

    with patch.object(config, "async_sync_entities_all") as mock_sync:
       .opp.bus.async_fire(EVENT_OPENPEERPOWER_STARTED)
        await.opp.async_block_till_done()
        assert len(mock_sync.mock_calls) == 1


async def test_google_config_expose_entity_prefs(mock_conf, cloud_prefs):
    """Test Google config should expose using prefs."""
    entity_conf = {"should_expose": False}
    await cloud_prefs.async_update(
        google_entity_configs={"light.kitchen": entity_conf},
        google_default_expose=["light"],
    )

    state = State("light.kitchen", "on")

    assert not mock_conf.should_expose(state)
    entity_conf["should_expose"] = True
    assert mock_conf.should_expose(state)

    entity_conf["should_expose"] = None
    assert mock_conf.should_expose(state)

    await cloud_prefs.async_update(
        google_default_expose=["sensor"],
    )
    assert not mock_conf.should_expose(state)


def test_enabled_requires_valid_sub.opp, mock_expired_cloud_login, cloud_prefs):
    """Test that google config enabled requires a valid Cloud sub."""
    assert cloud_prefs.google_enabled
    assert.opp.data["cloud"].is_logged_in
    assert.opp.data["cloud"].subscription_expired

    config = CloudGoogleConfig(
       .opp, GACTIONS_SCHEMA({}), "mock-user-id", cloud_prefs,.opp.data["cloud"]
    )

    assert not config.enabled
