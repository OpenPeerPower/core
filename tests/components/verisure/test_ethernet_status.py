"""Test Verisure ethernet status."""
from contextlib import contextmanager
from unittest.mock import patch

from openpeerpower.components.verisure import DOMAIN as VERISURE_DOMAIN
from openpeerpower.const import STATE_UNAVAILABLE
from openpeerpower.setup import async_setup_component

CONFIG = {
    "verisure": {
        "username": "test",
        "password": "test",
        "alarm": False,
        "door_window": False,
        "hygrometers": False,
        "mouse": False,
        "smartplugs": False,
        "thermometers": False,
        "smartcam": False,
    }
}


@contextmanager
def mock_hub(config, response):
    """Extensively mock out a verisure hub."""
    hub_prefix = "openpeerpower.components.verisure.binary_sensor.hub"
    verisure_prefix = "verisure.Session"
    with patch(verisure_prefix) as session, patch(hub_prefix) as hub:
        session.login.return_value = True

        hub.config = config["verisure"]
        hub.get.return_value = response
        hub.get_first.return_value = response.get("ethernetConnectedNow", None)

        yield hub


async def setup_verisure.opp, config, response):
    """Set up mock verisure."""
    with mock_hub(config, response):
        await async_setup_component.opp, VERISURE_DOMAIN, config)
        await opp.async_block_till_done()


async def test_verisure_no_ethernet_status.opp):
    """Test no data from API."""
    await setup_verisure.opp, CONFIG, {})
    assert len.opp.states.async_all()) == 1
    entity_id = opp.states.async_entity_ids()[0]
    assert.opp.states.get(entity_id).state == STATE_UNAVAILABLE


async def test_verisure_ethernet_status_disconnected.opp):
    """Test disconnected."""
    await setup_verisure.opp, CONFIG, {"ethernetConnectedNow": False})
    assert len.opp.states.async_all()) == 1
    entity_id = opp.states.async_entity_ids()[0]
    assert.opp.states.get(entity_id).state == "off"


async def test_verisure_ethernet_status_connected.opp):
    """Test connected."""
    await setup_verisure.opp, CONFIG, {"ethernetConnectedNow": True})
    assert len.opp.states.async_all()) == 1
    entity_id = opp.states.async_entity_ids()[0]
    assert.opp.states.get(entity_id).state == "on"
