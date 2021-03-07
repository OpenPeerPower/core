"""Test the onboarding views."""
import asyncio
import os
from unittest.mock import patch

import pytest

from openpeerpower.components import onboarding
from openpeerpower.components.onboarding import const, views
from openpeerpower.const import HTTP_FORBIDDEN
from openpeerpower.setup import async_setup_component

from . import mock_storage

from tests.common import CLIENT_ID, CLIENT_REDIRECT_URI, register_auth_provider
from tests.components.met.conftest import mock_weather  # noqa: F401


@pytest.fixture(autouse=True)
def always_mock_weather(mock_weather):  # noqa: F811
    """Mock the Met weather provider."""
    pass


@pytest.fixture(autouse=True)
def auth_active(opp):
    """Ensure auth is always active."""
    opp.loop.run_until_complete(register_auth_provider(opp, {"type": "openpeerpower"}))


@pytest.fixture(name="rpi")
async def rpi_fixture(opp, aioclient_mock, mock_supervisor):
    """Mock core info with rpi."""
    aioclient_mock.get(
        "http://127.0.0.1/core/info",
        json={
            "result": "ok",
            "data": {"version_latest": "1.0.0", "machine": "raspberrypi3"},
        },
    )
    assert await async_setup_component(opp, "oppio", {})
    await opp.async_block_till_done()


@pytest.fixture(name="no_rpi")
async def no_rpi_fixture(opp, aioclient_mock, mock_supervisor):
    """Mock core info with rpi."""
    aioclient_mock.get(
        "http://127.0.0.1/core/info",
        json={
            "result": "ok",
            "data": {"version_latest": "1.0.0", "machine": "odroid-n2"},
        },
    )
    assert await async_setup_component(opp, "oppio", {})
    await opp.async_block_till_done()


@pytest.fixture(name="mock_supervisor")
async def mock_supervisor_fixture(opp, aioclient_mock):
    """Mock supervisor."""
    aioclient_mock.post("http://127.0.0.1/openpeerpower/options", json={"result": "ok"})
    aioclient_mock.post("http://127.0.0.1/supervisor/options", json={"result": "ok"})
    with patch.dict(os.environ, {"OPPIO": "127.0.0.1"}), patch(
        "openpeerpower.components.oppio.OppIO.is_connected",
        return_value=True,
    ), patch("openpeerpower.components.oppio.OppIO.get_info", return_value={},), patch(
        "openpeerpower.components.oppio.OppIO.get_host_info",
        return_value={},
    ), patch(
        "openpeerpower.components.oppio.OppIO.get_supervisor_info",
        return_value={},
    ), patch(
        "openpeerpower.components.oppio.OppIO.get_os_info",
        return_value={},
    ), patch(
        "openpeerpower.components.oppio.OppIO.get_ingress_panels",
        return_value={"panels": {}},
    ), patch.dict(
        os.environ, {"OPPIO_TOKEN": "123456"}
    ):
        yield


async def test_onboarding_progress(opp, opp_storage, aiohttp_client):
    """Test fetching progress."""
    mock_storage(opp_storage, {"done": ["hello"]})

    assert await async_setup_component(opp, "onboarding", {})
    await opp.async_block_till_done()

    client = await aiohttp_client(opp.http.app)

    with patch.object(views, "STEPS", ["hello", "world"]):
        resp = await client.get("/api/onboarding")

    assert resp.status == 200
    data = await resp.json()
    assert len(data) == 2
    assert data[0] == {"step": "hello", "done": True}
    assert data[1] == {"step": "world", "done": False}


async def test_onboarding_user_already_done(opp, opp_storage, aiohttp_client):
    """Test creating a new user when user step already done."""
    mock_storage(opp_storage, {"done": [views.STEP_USER]})

    with patch.object(onboarding, "STEPS", ["hello", "world"]):
        assert await async_setup_component(opp, "onboarding", {})
        await opp.async_block_till_done()

    client = await aiohttp_client(opp.http.app)

    resp = await client.post(
        "/api/onboarding/users",
        json={
            "client_id": CLIENT_ID,
            "name": "Test Name",
            "username": "test-user",
            "password": "test-pass",
            "language": "en",
        },
    )

    assert resp.status == HTTP_FORBIDDEN


async def test_onboarding_user(opp, opp_storage, aiohttp_client):
    """Test creating a new user."""
    assert await async_setup_component(opp, "person", {})
    assert await async_setup_component(opp, "onboarding", {})
    await opp.async_block_till_done()

    client = await aiohttp_client(opp.http.app)

    resp = await client.post(
        "/api/onboarding/users",
        json={
            "client_id": CLIENT_ID,
            "name": "Test Name",
            "username": "test-user",
            "password": "test-pass",
            "language": "en",
        },
    )

    assert resp.status == 200
    assert const.STEP_USER in opp_storage[const.DOMAIN]["data"]["done"]

    data = await resp.json()
    assert "auth_code" in data

    users = await opp.auth.async_get_users()
    assert len(users) == 1
    user = users[0]
    assert user.name == "Test Name"
    assert len(user.credentials) == 1
    assert user.credentials[0].data["username"] == "test-user"
    assert len(opp.data["person"][1].async_items()) == 1

    # Validate refresh token 1
    resp = await client.post(
        "/auth/token",
        data={
            "client_id": CLIENT_ID,
            "grant_type": "authorization_code",
            "code": data["auth_code"],
        },
    )

    assert resp.status == 200
    tokens = await resp.json()

    assert (
        await opp.auth.async_validate_access_token(tokens["access_token"]) is not None
    )

    # Validate created areas
    area_registry = await opp.helpers.area_registry.async_get_registry()
    assert len(area_registry.areas) == 3
    assert sorted([area.name for area in area_registry.async_list_areas()]) == [
        "Bedroom",
        "Kitchen",
        "Living Room",
    ]


async def test_onboarding_user_invalid_name(opp, opp_storage, aiohttp_client):
    """Test not providing name."""
    mock_storage(opp_storage, {"done": []})

    assert await async_setup_component(opp, "onboarding", {})
    await opp.async_block_till_done()

    client = await aiohttp_client(opp.http.app)

    resp = await client.post(
        "/api/onboarding/users",
        json={
            "client_id": CLIENT_ID,
            "username": "test-user",
            "password": "test-pass",
            "language": "en",
        },
    )

    assert resp.status == 400


async def test_onboarding_user_race(opp, opp_storage, aiohttp_client):
    """Test race condition on creating new user."""
    mock_storage(opp_storage, {"done": ["hello"]})

    assert await async_setup_component(opp, "onboarding", {})
    await opp.async_block_till_done()

    client = await aiohttp_client(opp.http.app)

    resp1 = client.post(
        "/api/onboarding/users",
        json={
            "client_id": CLIENT_ID,
            "name": "Test 1",
            "username": "1-user",
            "password": "1-pass",
            "language": "en",
        },
    )
    resp2 = client.post(
        "/api/onboarding/users",
        json={
            "client_id": CLIENT_ID,
            "name": "Test 2",
            "username": "2-user",
            "password": "2-pass",
            "language": "es",
        },
    )

    res1, res2 = await asyncio.gather(resp1, resp2)

    assert sorted([res1.status, res2.status]) == [200, HTTP_FORBIDDEN]


async def test_onboarding_integration(opp, opp_storage, opp_client, opp_admin_user):
    """Test finishing integration step."""
    mock_storage(opp_storage, {"done": [const.STEP_USER]})

    assert await async_setup_component(opp, "onboarding", {})
    await opp.async_block_till_done()

    client = await opp_client()

    resp = await client.post(
        "/api/onboarding/integration",
        json={"client_id": CLIENT_ID, "redirect_uri": CLIENT_REDIRECT_URI},
    )

    assert resp.status == 200
    data = await resp.json()
    assert "auth_code" in data

    # Validate refresh token
    resp = await client.post(
        "/auth/token",
        data={
            "client_id": CLIENT_ID,
            "grant_type": "authorization_code",
            "code": data["auth_code"],
        },
    )

    assert resp.status == 200
    assert const.STEP_INTEGRATION in opp_storage[const.DOMAIN]["data"]["done"]
    tokens = await resp.json()

    assert (
        await opp.auth.async_validate_access_token(tokens["access_token"]) is not None
    )

    # Onboarding refresh token and new refresh token
    for user in await opp.auth.async_get_users():
        assert len(user.refresh_tokens) == 2, user


async def test_onboarding_integration_missing_credential(
    opp, opp_storage, opp_client, opp_access_token
):
    """Test that we fail integration step if user is missing credentials."""
    mock_storage(opp_storage, {"done": [const.STEP_USER]})

    assert await async_setup_component(opp, "onboarding", {})
    await opp.async_block_till_done()

    refresh_token = await opp.auth.async_validate_access_token(opp_access_token)
    refresh_token.credential = None

    client = await opp_client()

    resp = await client.post(
        "/api/onboarding/integration",
        json={"client_id": CLIENT_ID, "redirect_uri": CLIENT_REDIRECT_URI},
    )

    assert resp.status == 403


async def test_onboarding_integration_invalid_redirect_uri(
    opp, opp_storage, opp_client
):
    """Test finishing integration step."""
    mock_storage(opp_storage, {"done": [const.STEP_USER]})

    assert await async_setup_component(opp, "onboarding", {})
    await opp.async_block_till_done()

    client = await opp_client()

    resp = await client.post(
        "/api/onboarding/integration",
        json={"client_id": CLIENT_ID, "redirect_uri": "http://invalid-redirect.uri"},
    )

    assert resp.status == 400

    # We will still mark the last step as done because there is nothing left.
    assert const.STEP_INTEGRATION in opp_storage[const.DOMAIN]["data"]["done"]

    # Only refresh token from onboarding should be there
    for user in await opp.auth.async_get_users():
        assert len(user.refresh_tokens) == 1, user


async def test_onboarding_integration_requires_auth(opp, opp_storage, aiohttp_client):
    """Test finishing integration step."""
    mock_storage(opp_storage, {"done": [const.STEP_USER]})

    assert await async_setup_component(opp, "onboarding", {})
    await opp.async_block_till_done()

    client = await aiohttp_client(opp.http.app)

    resp = await client.post(
        "/api/onboarding/integration", json={"client_id": CLIENT_ID}
    )

    assert resp.status == 401


async def test_onboarding_core_sets_up_met(opp, opp_storage, opp_client):
    """Test finishing the core step."""
    mock_storage(opp_storage, {"done": [const.STEP_USER]})

    assert await async_setup_component(opp, "onboarding", {})
    await opp.async_block_till_done()

    client = await opp_client()

    resp = await client.post("/api/onboarding/core_config")

    assert resp.status == 200

    await opp.async_block_till_done()
    assert len(opp.states.async_entity_ids("weather")) == 1


async def test_onboarding_core_sets_up_rpi_power(
    opp, opp_storage, opp_client, aioclient_mock, rpi
):
    """Test that the core step sets up rpi_power on RPi."""
    mock_storage(opp_storage, {"done": [const.STEP_USER]})
    await async_setup_component(opp, "persistent_notification", {})

    assert await async_setup_component(opp, "onboarding", {})
    await opp.async_block_till_done()

    client = await opp_client()

    with patch(
        "openpeerpower.components.rpi_power.config_flow.new_under_voltage"
    ), patch("openpeerpower.components.rpi_power.binary_sensor.new_under_voltage"):
        resp = await client.post("/api/onboarding/core_config")

        assert resp.status == 200

        await opp.async_block_till_done()

    rpi_power_state = opp.states.get("binary_sensor.rpi_power_status")
    assert rpi_power_state


async def test_onboarding_core_no_rpi_power(
    opp, opp_storage, opp_client, aioclient_mock, no_rpi
):
    """Test that the core step do not set up rpi_power on non RPi."""
    mock_storage(opp_storage, {"done": [const.STEP_USER]})
    await async_setup_component(opp, "persistent_notification", {})

    assert await async_setup_component(opp, "onboarding", {})
    await opp.async_block_till_done()

    client = await opp_client()

    with patch(
        "openpeerpower.components.rpi_power.config_flow.new_under_voltage"
    ), patch("openpeerpower.components.rpi_power.binary_sensor.new_under_voltage"):
        resp = await client.post("/api/onboarding/core_config")

        assert resp.status == 200

        await opp.async_block_till_done()

    rpi_power_state = opp.states.get("binary_sensor.rpi_power_status")
    assert not rpi_power_state
