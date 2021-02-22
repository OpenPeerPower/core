"""Tests for the Mazda Connected Services integration."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

from pymazda import Client as MazdaAPI

from openpeerpower.components.mazda.const import DOMAIN
from openpeerpower.const import CONF_EMAIL, CONF_PASSWORD, CONF_REGION
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers import aiohttp_client

from tests.common import MockConfigEntry, load_fixture

FIXTURE_USER_INPUT = {
    CONF_EMAIL: "example@example.com",
    CONF_PASSWORD: "password",
    CONF_REGION: "MNAO",
}


async def init_integration.opp: OpenPeerPower, use_nickname=True) -> MockConfigEntry:
    """Set up the Mazda Connected Services integration in Open Peer Power."""
    get_vehicles_fixture = json.loads(load_fixture("mazda/get_vehicles.json"))
    if not use_nickname:
        get_vehicles_fixture[0].pop("nickname")

    get_vehicle_status_fixture = json.loads(
        load_fixture("mazda/get_vehicle_status.json")
    )

    config_entry = MockConfigEntry(domain=DOMAIN, data=FIXTURE_USER_INPUT)
    config_entry.add_to.opp.opp)

    client_mock = MagicMock(
        MazdaAPI(
            FIXTURE_USER_INPUT[CONF_EMAIL],
            FIXTURE_USER_INPUT[CONF_PASSWORD],
            FIXTURE_USER_INPUT[CONF_REGION],
            aiohttp_client.async_get_clientsession.opp),
        )
    )
    client_mock.get_vehicles = AsyncMock(return_value=get_vehicles_fixture)
    client_mock.get_vehicle_status = AsyncMock(return_value=get_vehicle_status_fixture)

    with patch(
        "openpeerpower.components.mazda.config_flow.MazdaAPI",
        return_value=client_mock,
    ), patch("openpeerpower.components.mazda.MazdaAPI", return_value=client_mock):
        assert await.opp.config_entries.async_setup(config_entry.entry_id)
        await.opp.async_block_till_done()

    return config_entry
