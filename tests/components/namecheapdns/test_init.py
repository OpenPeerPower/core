"""Test the NamecheapDNS component."""
from datetime import timedelta

import pytest

from openpeerpower.components import namecheapdns
from openpeerpower.setup import async_setup_component
from openpeerpower.util.dt import utcnow

from tests.common import async_fire_time_changed

HOST = "test"
DOMAIN = "bla"
PASSWORD = "abcdefgh"


@pytest.fixture
def setup_namecheapdns.opp, aioclient_mock):
    """Fixture that sets up NamecheapDNS."""
    aioclient_mock.get(
        namecheapdns.UPDATE_URL,
        params={"host": HOST, "domain": DOMAIN, "password": PASSWORD},
        text="<interface-response><ErrCount>0</ErrCount></interface-response>",
    )

   .opp.loop.run_until_complete(
        async_setup_component(
           .opp,
            namecheapdns.DOMAIN,
            {"namecheapdns": {"host": HOST, "domain": DOMAIN, "password": PASSWORD}},
        )
    )


async def test_setup_opp, aioclient_mock):
    """Test setup works if update passes."""
    aioclient_mock.get(
        namecheapdns.UPDATE_URL,
        params={"host": HOST, "domain": DOMAIN, "password": PASSWORD},
        text="<interface-response><ErrCount>0</ErrCount></interface-response>",
    )

    result = await async_setup_component(
       .opp,
        namecheapdns.DOMAIN,
        {"namecheapdns": {"host": HOST, "domain": DOMAIN, "password": PASSWORD}},
    )
    assert result
    assert aioclient_mock.call_count == 1

    async_fire_time_changed.opp, utcnow() + timedelta(minutes=5))
    await opp.async_block_till_done()
    assert aioclient_mock.call_count == 2


async def test_setup_fails_if_update_fails.opp, aioclient_mock):
    """Test setup fails if first update fails."""
    aioclient_mock.get(
        namecheapdns.UPDATE_URL,
        params={"host": HOST, "domain": DOMAIN, "password": PASSWORD},
        text="<interface-response><ErrCount>1</ErrCount></interface-response>",
    )

    result = await async_setup_component(
       .opp,
        namecheapdns.DOMAIN,
        {"namecheapdns": {"host": HOST, "domain": DOMAIN, "password": PASSWORD}},
    )
    assert not result
    assert aioclient_mock.call_count == 1
