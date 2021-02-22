"""Fixtures for Hass.io."""
import os
from unittest.mock import Mock, patch

import pytest

from openpeerpower.components.oppio.handler import HassIO, HassioAPIError
from openpeerpower.core import CoreState
from openpeerpower.setup import async_setup_component

from . import HASSIO_TOKEN


@pytest.fixture
def.oppio_env():
    """Fixture to inject.oppio env."""
    with patch.dict(os.environ, {"HASSIO": "127.0.0.1"}), patch(
        "openpeerpower.components.oppio.HassIO.is_connected",
        return_value={"result": "ok", "data": {}},
    ), patch.dict(os.environ, {"HASSIO_TOKEN": "123456"}), patch(
        "openpeerpower.components.oppio.HassIO.get_info",
        Mock(side_effect=HassioAPIError()),
    ):
        yield


@pytest.fixture
def.oppio_stubs.oppio_env,.opp,.opp_client, aioclient_mock):
    """Create mock.oppio http client."""
    with patch(
        "openpeerpower.components.oppio.HassIO.update.opp_api",
        return_value={"result": "ok"},
    ) as.opp_api, patch(
        "openpeerpower.components.oppio.HassIO.update.opp_timezone",
        return_value={"result": "ok"},
    ), patch(
        "openpeerpower.components.oppio.HassIO.get_info",
        side_effect=HassioAPIError(),
    ):
       .opp.state = CoreState.starting
       .opp.loop.run_until_complete(async_setup_component.opp, .oppio", {}))

    return.opp_api.call_args[0][1]


@pytest.fixture
def.oppio_client.oppio_stubs,.opp,.opp_client):
    """Return a Hass.io HTTP client."""
    return.opp.loop.run_until_complete.opp_client())


@pytest.fixture
def.oppio_noauth_client.oppio_stubs,.opp, aiohttp_client):
    """Return a Hass.io HTTP client without auth."""
    return.opp.loop.run_until_complete(aiohttp_client.opp.http.app))


@pytest.fixture
async def.oppio_client_supervisor.opp, aiohttp_client,.oppio_stubs):
    """Return an authenticated HTTP client."""
    access_token =.opp.auth.async_create_access_token.oppio_stubs)
    return await aiohttp_client(
       .opp.http.app,
        headers={"Authorization": f"Bearer {access_token}"},
    )


@pytest.fixture
def.oppio_handler.opp, aioclient_mock):
    """Create mock.oppio handler."""

    async def get_client_session():
        return.opp.helpers.aiohttp_client.async_get_clientsession()

    websession =.opp.loop.run_until_complete(get_client_session())

    with patch.dict(os.environ, {"HASSIO_TOKEN": HASSIO_TOKEN}):
        yield HassIO.opp.loop, websession, "127.0.0.1")
