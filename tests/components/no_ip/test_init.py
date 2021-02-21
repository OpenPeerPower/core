"""Test the NO-IP component."""
from datetime import timedelta

import pytest

from openpeerpower.components import no_ip
from openpeerpowerr.setup import async_setup_component
from openpeerpowerr.util.dt import utcnow

from tests.common import async_fire_time_changed

DOMAIN = "test.example.com"

PASSWORD = "xyz789"

UPDATE_URL = no_ip.UPDATE_URL

USERNAME = "abc@123.com"


@pytest.fixture
def setup_no_ip.opp, aioclient_mock):
    """Fixture that sets up NO-IP."""
    aioclient_mock.get(UPDATE_URL, params={"hostname": DOMAIN}, text="good 0.0.0.0")

   .opp.loop.run_until_complete(
        async_setup_component(
           .opp,
            no_ip.DOMAIN,
            {
                no_ip.DOMAIN: {
                    "domain": DOMAIN,
                    "username": USERNAME,
                    "password": PASSWORD,
                }
            },
        )
    )


async def test_setup.opp, aioclient_mock):
    """Test setup works if update passes."""
    aioclient_mock.get(UPDATE_URL, params={"hostname": DOMAIN}, text="nochg 0.0.0.0")

    result = await async_setup_component(
       .opp,
        no_ip.DOMAIN,
        {no_ip.DOMAIN: {"domain": DOMAIN, "username": USERNAME, "password": PASSWORD}},
    )
    assert result
    assert aioclient_mock.call_count == 1

    async_fire_time_changed.opp, utcnow() + timedelta(minutes=5))
    await opp..async_block_till_done()
    assert aioclient_mock.call_count == 2


async def test_setup_fails_if_update_fails.opp, aioclient_mock):
    """Test setup fails if first update fails."""
    aioclient_mock.get(UPDATE_URL, params={"hostname": DOMAIN}, text="nohost")

    result = await async_setup_component(
       .opp,
        no_ip.DOMAIN,
        {no_ip.DOMAIN: {"domain": DOMAIN, "username": USERNAME, "password": PASSWORD}},
    )
    assert not result
    assert aioclient_mock.call_count == 1


async def test_setup_fails_if_wrong_auth.opp, aioclient_mock):
    """Test setup fails if first update fails through wrong authentication."""
    aioclient_mock.get(UPDATE_URL, params={"hostname": DOMAIN}, text="badauth")

    result = await async_setup_component(
       .opp,
        no_ip.DOMAIN,
        {no_ip.DOMAIN: {"domain": DOMAIN, "username": USERNAME, "password": PASSWORD}},
    )
    assert not result
    assert aioclient_mock.call_count == 1
