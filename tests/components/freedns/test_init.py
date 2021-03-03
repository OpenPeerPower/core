"""Test the FreeDNS component."""
import pytest

from openpeerpower.components import freedns
from openpeerpower.setup import async_setup_component
from openpeerpower.util.dt import utcnow

from tests.common import async_fire_time_changed

ACCESS_TOKEN = "test_token"
UPDATE_INTERVAL = freedns.DEFAULT_INTERVAL
UPDATE_URL = freedns.UPDATE_URL


@pytest.fixture
def setup_freedns(opp, aioclient_mock):
    """Fixture that sets up FreeDNS."""
    params = {}
    params[ACCESS_TOKEN] = ""
    aioclient_mock.get(
        UPDATE_URL, params=params, text="Successfully updated 1 domains."
    )

    opp.loop.run_until_complete(
        async_setup_component(
            opp,
            freedns.DOMAIN,
            {
                freedns.DOMAIN: {
                    "access_token": ACCESS_TOKEN,
                    "scan_interval": UPDATE_INTERVAL,
                }
            },
        )
    )


async def test_setup(opp, aioclient_mock):
    """Test setup works if update passes."""
    params = {}
    params[ACCESS_TOKEN] = ""
    aioclient_mock.get(
        UPDATE_URL, params=params, text="ERROR: Address has not changed."
    )

    result = await async_setup_component(
        opp,
        freedns.DOMAIN,
        {
            freedns.DOMAIN: {
                "access_token": ACCESS_TOKEN,
                "scan_interval": UPDATE_INTERVAL,
            }
        },
    )
    assert result
    assert aioclient_mock.call_count == 1

    async_fire_time_changed(opp, utcnow() + UPDATE_INTERVAL)
    await opp.async_block_till_done()
    assert aioclient_mock.call_count == 2


async def test_setup_fails_if_wrong_token(opp, aioclient_mock):
    """Test setup fails if first update fails through wrong token."""
    params = {}
    params[ACCESS_TOKEN] = ""
    aioclient_mock.get(UPDATE_URL, params=params, text="ERROR: Invalid update URL (2)")

    result = await async_setup_component(
        opp,
        freedns.DOMAIN,
        {
            freedns.DOMAIN: {
                "access_token": ACCESS_TOKEN,
                "scan_interval": UPDATE_INTERVAL,
            }
        },
    )
    assert not result
    assert aioclient_mock.call_count == 1
