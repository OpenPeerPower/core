"""The test for the Melissa Climate component."""
from unittest.mock import AsyncMock, patch

from openpeerpower.components import melissa

VALID_CONFIG = {"melissa": {"username": "********", "password": "********"}}


async def test_setup_opp):
    """Test setting up the Melissa component."""
    with patch("melissa.AsyncMelissa") as mocked_melissa, patch.object(
        melissa, "async_load_platform"
    ):
        mocked_melissa.return_value.async_connect = AsyncMock()
        await melissa.async_setup(opp, VALID_CONFIG)

        mocked_melissa.assert_called_with(username="********", password="********")

        assert melissa.DATA_MELISSA in opp.data
        assert isinstance(
            opp.data[melissa.DATA_MELISSA],
            type(mocked_melissa.return_value),
        )
