"""The tests for Netatmo component."""
import asyncio
from datetime import timedelta
from time import time
from unittest.mock import AsyncMock, patch

import pyatmo

from openpeerpower import config_entries
from openpeerpower.components.netatmo import DOMAIN
from openpeerpower.const import CONF_WEBHOOK_ID
from openpeerpower.core import CoreState
from openpeerpower.setup import async_setup_component
from openpeerpower.util import dt

from .common import (
    FAKE_WEBHOOK_ACTIVATION,
    fake_post_request,
    selected_platforms,
    simulate_webhook,
)

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.components.cloud import mock_cloud

# Fake webhook thermostat mode change to "Max"
FAKE_WEBHOOK = {
    "room_id": "2746182631",
    "home": {
        "id": "91763b24c43d3e344f424e8b",
        "name": "MYHOME",
        "country": "DE",
        "rooms": [
            {
                "id": "2746182631",
                "name": "Livingroom",
                "type": "livingroom",
                "therm_setpoint_mode": "max",
                "therm_setpoint_end_time": 1612749189,
            }
        ],
        "modules": [
            {"id": "12:34:56:00:01:ae", "name": "Livingroom", "type": "NATherm1"}
        ],
    },
    "mode": "max",
    "event_type": "set_point",
    "push_type": "display_change",
}


async def test_setup_component(opp):
    """Test setup and teardown of the netatmo component."""
    config_entry = MockConfigEntry(
        domain="netatmo",
        data={
            "auth_implementation": "cloud",
            "token": {
                "refresh_token": "mock-refresh-token",
                "access_token": "mock-access-token",
                "type": "Bearer",
                "expires_in": 60,
                "expires_at": time() + 1000,
                "scope": "read_station",
            },
        },
    )
    config_entry.add_to_opp(opp)

    with patch(
        "openpeerpower.components.netatmo.api.AsyncConfigEntryNetatmoAuth",
    ) as mock_auth, patch(
        "openpeerpower.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation",
    ) as mock_impl, patch(
        "openpeerpower.components.webhook.async_generate_url"
    ) as mock_webhook:
        mock_auth.return_value.async_post_request.side_effect = fake_post_request
        mock_auth.return_value.async_addwebhook.side_effect = AsyncMock()
        mock_auth.return_value.async_dropwebhook.side_effect = AsyncMock()
        assert await async_setup_component(opp, "netatmo", {})

    await opp.async_block_till_done()

    mock_auth.assert_called_once()
    mock_impl.assert_called_once()
    mock_webhook.assert_called_once()

    assert config_entry.state is config_entries.ConfigEntryState.LOADED
    assert opp.config_entries.async_entries(DOMAIN)
    assert len(opp.states.async_all()) > 0

    for config_entry in opp.config_entries.async_entries("netatmo"):
        await opp.config_entries.async_remove(config_entry.entry_id)

    await opp.async_block_till_done()
    assert len(opp.states.async_all()) == 0
    assert not opp.config_entries.async_entries(DOMAIN)


async def test_setup_component_with_config(opp, config_entry):
    """Test setup of the netatmo component with dev account."""
    fake_post_hits = 0

    async def fake_post(*args, **kwargs):
        """Fake error during requesting backend data."""
        nonlocal fake_post_hits
        fake_post_hits += 1
        return await fake_post_request(*args, **kwargs)

    with patch(
        "openpeerpower.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation",
    ) as mock_impl, patch(
        "openpeerpower.components.webhook.async_generate_url"
    ) as mock_webhook, patch(
        "openpeerpower.components.netatmo.api.AsyncConfigEntryNetatmoAuth",
    ) as mock_auth, patch(
        "openpeerpower.components.netatmo.PLATFORMS", ["sensor"]
    ):
        mock_auth.return_value.async_post_request.side_effect = fake_post
        mock_auth.return_value.async_addwebhook.side_effect = AsyncMock()
        mock_auth.return_value.async_dropwebhook.side_effect = AsyncMock()

        assert await async_setup_component(
            opp, "netatmo", {"netatmo": {"client_id": "123", "client_secret": "abc"}}
        )

        await opp.async_block_till_done()

        assert fake_post_hits == 3
        mock_impl.assert_called_once()
        mock_webhook.assert_called_once()

    assert opp.config_entries.async_entries(DOMAIN)
    assert len(opp.states.async_all()) > 0


async def test_setup_component_with_webhook(opp, config_entry, netatmo_auth):
    """Test setup and teardown of the netatmo component with webhook registration."""
    with selected_platforms(["camera", "climate", "light", "sensor"]):
        await opp.config_entries.async_setup(config_entry.entry_id)

        await opp.async_block_till_done()

    webhook_id = config_entry.data[CONF_WEBHOOK_ID]
    await simulate_webhook(opp, webhook_id, FAKE_WEBHOOK_ACTIVATION)

    assert len(opp.states.async_all()) > 0

    webhook_id = config_entry.data[CONF_WEBHOOK_ID]
    await simulate_webhook(opp, webhook_id, FAKE_WEBHOOK_ACTIVATION)

    # Assert webhook is established successfully
    climate_entity_livingroom = "climate.netatmo_livingroom"
    assert opp.states.get(climate_entity_livingroom).state == "auto"
    await simulate_webhook(opp, webhook_id, FAKE_WEBHOOK)
    assert opp.states.get(climate_entity_livingroom).state == "heat"

    for config_entry in opp.config_entries.async_entries("netatmo"):
        await opp.config_entries.async_remove(config_entry.entry_id)

    await opp.async_block_till_done()
    assert len(opp.states.async_all()) == 0
    assert len(opp.config_entries.async_entries(DOMAIN)) == 0


async def test_setup_without_https(opp, config_entry, caplog):
    """Test if set up with cloud link and without https."""
    opp.config.components.add("cloud")
    with patch(
        "openpeerpower.helpers.network.get_url",
        return_value="http://example.nabu.casa",
    ), patch(
        "openpeerpower.components.netatmo.api.AsyncConfigEntryNetatmoAuth"
    ) as mock_auth, patch(
        "openpeerpower.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation",
    ), patch(
        "openpeerpower.components.webhook.async_generate_url"
    ) as mock_async_generate_url:
        mock_auth.return_value.async_post_request.side_effect = fake_post_request
        mock_async_generate_url.return_value = "http://example.com"
        assert await async_setup_component(
            opp, "netatmo", {"netatmo": {"client_id": "123", "client_secret": "abc"}}
        )

        await opp.async_block_till_done()
        mock_auth.assert_called_once()
        mock_async_generate_url.assert_called_once()

    assert "https and port 443 is required to register the webhook" in caplog.text


async def test_setup_with_cloud(opp, config_entry):
    """Test if set up with active cloud subscription."""
    await mock_cloud(opp)
    await opp.async_block_till_done()

    with patch(
        "openpeerpower.components.cloud.async_is_logged_in", return_value=True
    ), patch(
        "openpeerpower.components.cloud.async_active_subscription", return_value=True
    ), patch(
        "openpeerpower.components.cloud.async_create_cloudhook",
        return_value="https://hooks.nabu.casa/ABCD",
    ) as fake_create_cloudhook, patch(
        "openpeerpower.components.cloud.async_delete_cloudhook"
    ) as fake_delete_cloudhook, patch(
        "openpeerpower.components.netatmo.api.AsyncConfigEntryNetatmoAuth"
    ) as mock_auth, patch(
        "openpeerpower.components.netatmo.PLATFORMS", []
    ), patch(
        "openpeerpower.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation",
    ), patch(
        "openpeerpower.components.webhook.async_generate_url"
    ):
        mock_auth.return_value.async_post_request.side_effect = fake_post_request
        assert await async_setup_component(
            opp, "netatmo", {"netatmo": {"client_id": "123", "client_secret": "abc"}}
        )
        assert opp.components.cloud.async_active_subscription() is True
        fake_create_cloudhook.assert_called_once()

        assert (
            opp.config_entries.async_entries("netatmo")[0].data["cloudhook_url"]
            == "https://hooks.nabu.casa/ABCD"
        )

        await opp.async_block_till_done()
        assert opp.config_entries.async_entries(DOMAIN)

        for config_entry in opp.config_entries.async_entries("netatmo"):
            await opp.config_entries.async_remove(config_entry.entry_id)
            fake_delete_cloudhook.assert_called_once()

        await opp.async_block_till_done()
        assert not opp.config_entries.async_entries(DOMAIN)


async def test_setup_with_cloudhook(opp):
    """Test if set up with active cloud subscription and cloud hook."""
    config_entry = MockConfigEntry(
        domain="netatmo",
        data={
            "auth_implementation": "cloud",
            "cloudhook_url": "https://hooks.nabu.casa/ABCD",
            "token": {
                "refresh_token": "mock-refresh-token",
                "access_token": "mock-access-token",
                "type": "Bearer",
                "expires_in": 60,
                "expires_at": time() + 1000,
                "scope": "read_station",
            },
        },
    )
    config_entry.add_to_opp(opp)

    await mock_cloud(opp)
    await opp.async_block_till_done()

    with patch(
        "openpeerpower.components.cloud.async_is_logged_in", return_value=True
    ), patch(
        "openpeerpower.components.cloud.async_active_subscription", return_value=True
    ), patch(
        "openpeerpower.components.cloud.async_create_cloudhook",
        return_value="https://hooks.nabu.casa/ABCD",
    ) as fake_create_cloudhook, patch(
        "openpeerpower.components.cloud.async_delete_cloudhook"
    ) as fake_delete_cloudhook, patch(
        "openpeerpower.components.netatmo.api.AsyncConfigEntryNetatmoAuth"
    ) as mock_auth, patch(
        "openpeerpower.components.netatmo.PLATFORMS", []
    ), patch(
        "openpeerpower.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation",
    ), patch(
        "openpeerpower.components.webhook.async_generate_url"
    ):
        mock_auth.return_value.async_post_request.side_effect = fake_post_request
        mock_auth.return_value.async_addwebhook.side_effect = AsyncMock()
        mock_auth.return_value.async_dropwebhook.side_effect = AsyncMock()
        assert await async_setup_component(opp, "netatmo", {})
        assert opp.components.cloud.async_active_subscription() is True

        assert (
            opp.config_entries.async_entries("netatmo")[0].data["cloudhook_url"]
            == "https://hooks.nabu.casa/ABCD"
        )

        await opp.async_block_till_done()
        assert opp.config_entries.async_entries(DOMAIN)
        fake_create_cloudhook.assert_not_called()

        for config_entry in opp.config_entries.async_entries("netatmo"):
            await opp.config_entries.async_remove(config_entry.entry_id)
            fake_delete_cloudhook.assert_called_once()

        await opp.async_block_till_done()
        assert not opp.config_entries.async_entries(DOMAIN)


async def test_setup_component_api_error(opp):
    """Test error on setup of the netatmo component."""
    config_entry = MockConfigEntry(
        domain="netatmo",
        data={
            "auth_implementation": "cloud",
            "token": {
                "refresh_token": "mock-refresh-token",
                "access_token": "mock-access-token",
                "type": "Bearer",
                "expires_in": 60,
                "expires_at": time() + 1000,
                "scope": "read_station",
            },
        },
    )
    config_entry.add_to_opp(opp)

    with patch(
        "openpeerpower.components.netatmo.api.AsyncConfigEntryNetatmoAuth",
    ) as mock_auth, patch(
        "openpeerpower.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation",
    ) as mock_impl, patch(
        "openpeerpower.components.webhook.async_generate_url"
    ):
        mock_auth.return_value.async_post_request.side_effect = (
            pyatmo.exceptions.ApiError()
        )

        mock_auth.return_value.async_addwebhook.side_effect = AsyncMock()
        mock_auth.return_value.async_dropwebhook.side_effect = AsyncMock()
        assert await async_setup_component(opp, "netatmo", {})

    await opp.async_block_till_done()

    mock_auth.assert_called_once()
    mock_impl.assert_called_once()


async def test_setup_component_api_timeout(opp):
    """Test timeout on setup of the netatmo component."""
    config_entry = MockConfigEntry(
        domain="netatmo",
        data={
            "auth_implementation": "cloud",
            "token": {
                "refresh_token": "mock-refresh-token",
                "access_token": "mock-access-token",
                "type": "Bearer",
                "expires_in": 60,
                "expires_at": time() + 1000,
                "scope": "read_station",
            },
        },
    )
    config_entry.add_to_opp(opp)

    with patch(
        "openpeerpower.components.netatmo.api.AsyncConfigEntryNetatmoAuth",
    ) as mock_auth, patch(
        "openpeerpower.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation",
    ) as mock_impl, patch(
        "openpeerpower.components.webhook.async_generate_url"
    ):
        mock_auth.return_value.async_post_request.side_effect = (
            asyncio.exceptions.TimeoutError()
        )

        mock_auth.return_value.async_addwebhook.side_effect = AsyncMock()
        mock_auth.return_value.async_dropwebhook.side_effect = AsyncMock()
        assert await async_setup_component(opp, "netatmo", {})

    await opp.async_block_till_done()

    mock_auth.assert_called_once()
    mock_impl.assert_called_once()


async def test_setup_component_with_delay(opp, config_entry):
    """Test setup of the netatmo component with delayed startup."""
    opp.state = CoreState.not_running

    with patch(
        "pyatmo.AbstractAsyncAuth.async_addwebhook", side_effect=AsyncMock()
    ) as mock_addwebhook, patch(
        "pyatmo.AbstractAsyncAuth.async_dropwebhook", side_effect=AsyncMock()
    ) as mock_dropwebhook, patch(
        "openpeerpower.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation",
    ) as mock_impl, patch(
        "openpeerpower.components.webhook.async_generate_url"
    ) as mock_webhook, patch(
        "pyatmo.AbstractAsyncAuth.async_post_request", side_effect=fake_post_request
    ) as mock_post_request, patch(
        "openpeerpower.components.netatmo.PLATFORMS", ["light"]
    ):

        assert await async_setup_component(
            opp, "netatmo", {"netatmo": {"client_id": "123", "client_secret": "abc"}}
        )

        await opp.async_block_till_done()

        assert mock_post_request.call_count == 5

        mock_impl.assert_called_once()
        mock_webhook.assert_not_called()

        await opp.async_start()
        await opp.async_block_till_done()
        mock_webhook.assert_called_once()

        # Fake webhook activation
        await simulate_webhook(
            opp, config_entry.data[CONF_WEBHOOK_ID], FAKE_WEBHOOK_ACTIVATION
        )
        await opp.async_block_till_done()

        mock_addwebhook.assert_called_once()
        mock_dropwebhook.assert_not_awaited()

        async_fire_time_changed(
            opp,
            dt.utcnow() + timedelta(seconds=60),
        )
        await opp.async_block_till_done()

        assert opp.config_entries.async_entries(DOMAIN)
        assert len(opp.states.async_all()) > 0

        await opp.async_stop()
        mock_dropwebhook.assert_called_once()
