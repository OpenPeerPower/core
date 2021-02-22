"""Test the Google Domains component."""
from datetime import timedelta

import pytest

from openpeerpower.components import google_domains
from openpeerpower.setup import async_setup_component
from openpeerpower.util.dt import utcnow

from tests.common import async_fire_time_changed

DOMAIN = "test.example.com"
USERNAME = "abc123"
PASSWORD = "xyz789"

UPDATE_URL = f"https://{USERNAME}:{PASSWORD}@domains.google.com/nic/update"


@pytest.fixture
def setup_google_domains.opp, aioclient_mock):
    """Fixture that sets up NamecheapDNS."""
    aioclient_mock.get(UPDATE_URL, params={"hostname": DOMAIN}, text="ok 0.0.0.0")

   .opp.loop.run_until_complete(
        async_setup_component(
           .opp,
            google_domains.DOMAIN,
            {
                "google_domains": {
                    "domain": DOMAIN,
                    "username": USERNAME,
                    "password": PASSWORD,
                }
            },
        )
    )


async def test_setup_opp, aioclient_mock):
    """Test setup works if update passes."""
    aioclient_mock.get(UPDATE_URL, params={"hostname": DOMAIN}, text="nochg 0.0.0.0")

    result = await async_setup_component(
       .opp,
        google_domains.DOMAIN,
        {
            "google_domains": {
                "domain": DOMAIN,
                "username": USERNAME,
                "password": PASSWORD,
            }
        },
    )
    assert result
    assert aioclient_mock.call_count == 1

    async_fire_time_changed.opp, utcnow() + timedelta(minutes=5))
    await opp.async_block_till_done()
    assert aioclient_mock.call_count == 2


async def test_setup_fails_if_update_fails.opp, aioclient_mock):
    """Test setup fails if first update fails."""
    aioclient_mock.get(UPDATE_URL, params={"hostname": DOMAIN}, text="nohost")

    result = await async_setup_component(
       .opp,
        google_domains.DOMAIN,
        {
            "google_domains": {
                "domain": DOMAIN,
                "username": USERNAME,
                "password": PASSWORD,
            }
        },
    )
    assert not result
    assert aioclient_mock.call_count == 1
