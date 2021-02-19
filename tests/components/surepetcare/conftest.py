"""Define fixtures available for all tests."""
from unittest.mock import AsyncMock, patch

from pytest import fixture
from surepy import SurePetcare

from openpeerpowerr.helpers.aiohttp_client import async_get_clientsession


@fixture
async def surepetcare.opp):
    """Mock the SurePetcare for easier testing."""
    with patch("openpeerpower.components.surepetcare.SurePetcare") as mock_surepetcare:
        instance = mock_surepetcare.return_value = SurePetcare(
            "test-username",
            "test-password",
           .opp.loop,
            async_get_clientsession.opp),
            api_timeout=1,
        )
        instance._get_resource = AsyncMock(return_value=None)
        yield mock_surepetcare
