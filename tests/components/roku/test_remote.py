"""The tests for the Roku remote platform."""
from unittest.mock import patch

from openpeerpower.components.remote import (
    ATTR_COMMAND,
    DOMAIN as REMOTE_DOMAIN,
    SERVICE_SEND_COMMAND,
)
from openpeerpower.const import ATTR_ENTITY_ID, SERVICE_TURN_OFF, SERVICE_TURN_ON
from openpeerpowerr.helpers.typing import OpenPeerPowerType

from tests.components.roku import UPNP_SERIAL, setup_integration
from tests.test_util.aiohttp import AiohttpClientMocker

MAIN_ENTITY_ID = f"{REMOTE_DOMAIN}.my_roku_3"

# pylint: disable=redefined-outer-name


async def test_setup(
   .opp: OpenPeerPowerType, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test setup with basic config."""
    await setup_integration.opp, aioclient_mock)
    assert.opp.states.get(MAIN_ENTITY_ID)


async def test_unique_id(
   .opp: OpenPeerPowerType, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test unique id."""
    await setup_integration.opp, aioclient_mock)

    entity_registry = await.opp.helpers.entity_registry.async_get_registry()

    main = entity_registry.async_get(MAIN_ENTITY_ID)
    assert main.unique_id == UPNP_SERIAL


async def test_main_services(
   .opp: OpenPeerPowerType, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test platform services."""
    await setup_integration.opp, aioclient_mock)

    with patch("openpeerpower.components.roku.Roku.remote") as remote_mock:
        await.opp.services.async_call(
            REMOTE_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: MAIN_ENTITY_ID},
            blocking=True,
        )
        remote_mock.assert_called_once_with("poweroff")

    with patch("openpeerpower.components.roku.Roku.remote") as remote_mock:
        await.opp.services.async_call(
            REMOTE_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: MAIN_ENTITY_ID},
            blocking=True,
        )
        remote_mock.assert_called_once_with("poweron")

    with patch("openpeerpower.components.roku.Roku.remote") as remote_mock:
        await.opp.services.async_call(
            REMOTE_DOMAIN,
            SERVICE_SEND_COMMAND,
            {ATTR_ENTITY_ID: MAIN_ENTITY_ID, ATTR_COMMAND: ["home"]},
            blocking=True,
        )
        remote_mock.assert_called_once_with("home")
