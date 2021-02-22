"""The tests for the Yamaha Media player platform."""
from unittest.mock import MagicMock, PropertyMock, call, patch

import pytest

import openpeerpower.components.media_player as mp
from openpeerpower.components.yamaha import media_player as yamaha
from openpeerpower.components.yamaha.const import DOMAIN
from openpeerpower.helpers.discovery import async_load_platform
from openpeerpower.setup import async_setup_component

CONFIG = {"media_player": {"platform": "yamaha", "host": "127.0.0.1"}}


def _create_zone_mock(name, url):
    zone = MagicMock()
    zone.ctrl_url = url
    zone.zone = name
    return zone


class FakeYamahaDevice:
    """A fake Yamaha device."""

    def __init__(self, ctrl_url, name, zones=None):
        """Initialize the fake Yamaha device."""
        self.ctrl_url = ctrl_url
        self.name = name
        self._zones = zones or []

    def zone_controllers(self):
        """Return controllers for all available zones."""
        return self._zones


@pytest.fixture(name="main_zone")
def main_zone_fixture():
    """Mock the main zone."""
    return _create_zone_mock("Main zone", "http://main")


@pytest.fixture(name="device")
def device_fixture(main_zone):
    """Mock the yamaha device."""
    device = FakeYamahaDevice("http://receiver", "Receiver", zones=[main_zone])
    with patch("rxv.RXV", return_value=device):
        yield device


async def test_setup_host.opp, device, main_zone):
    """Test set up integration with host."""
    assert await async_setup_component.opp, mp.DOMAIN, CONFIG)
    await opp.async_block_till_done()

    state = opp.states.get("media_player.yamaha_receiver_main_zone")

    assert state is not None
    assert state.state == "off"


async def test_setup_no_host.opp, device, main_zone):
    """Test set up integration without host."""
    with patch("rxv.find", return_value=[device]):
        assert await async_setup_component(
            opp. mp.DOMAIN, {"media_player": {"platform": "yamaha"}}
        )
        await opp.async_block_till_done()

    state = opp.states.get("media_player.yamaha_receiver_main_zone")

    assert state is not None
    assert state.state == "off"


async def test_setup_discovery.opp, device, main_zone):
    """Test set up integration via discovery."""
    discovery_info = {
        "name": "Yamaha Receiver",
        "model_name": "Yamaha",
        "control_url": "http://receiver",
        "description_url": "http://receiver/description",
    }
    await async_load_platform(
        opp. mp.DOMAIN, "yamaha", discovery_info, {mp.DOMAIN: {}}
    )
    await opp.async_block_till_done()

    state = opp.states.get("media_player.yamaha_receiver_main_zone")

    assert state is not None
    assert state.state == "off"


async def test_setup_zone_ignore.opp, device, main_zone):
    """Test set up integration without host."""
    assert await async_setup_component(
        opp.
        mp.DOMAIN,
        {
            "media_player": {
                "platform": "yamaha",
                "host": "127.0.0.1",
                "zone_ignore": "Main zone",
            }
        },
    )
    await opp.async_block_till_done()

    state = opp.states.get("media_player.yamaha_receiver_main_zone")

    assert state is None


async def test_enable_output.opp, device, main_zone):
    """Test enable output service."""
    assert await async_setup_component.opp, mp.DOMAIN, CONFIG)
    await opp.async_block_till_done()

    port = "hdmi1"
    enabled = True
    data = {
        "entity_id": "media_player.yamaha_receiver_main_zone",
        "port": port,
        "enabled": enabled,
    }

    await opp.services.async_call(DOMAIN, yamaha.SERVICE_ENABLE_OUTPUT, data, True)

    assert main_zone.enable_output.call_count == 1
    assert main_zone.enable_output.call_args == call(port, enabled)


async def test_select_scene.opp, device, main_zone, caplog):
    """Test select scene service."""
    scene_prop = PropertyMock(return_value=None)
    type(main_zone).scene = scene_prop

    assert await async_setup_component.opp, mp.DOMAIN, CONFIG)
    await opp.async_block_till_done()

    scene = "TV Viewing"
    data = {
        "entity_id": "media_player.yamaha_receiver_main_zone",
        "scene": scene,
    }

    await opp.services.async_call(DOMAIN, yamaha.SERVICE_SELECT_SCENE, data, True)

    assert scene_prop.call_count == 1
    assert scene_prop.call_args == call(scene)

    scene = "BD/DVD Movie Viewing"
    data["scene"] = scene

    await opp.services.async_call(DOMAIN, yamaha.SERVICE_SELECT_SCENE, data, True)

    assert scene_prop.call_count == 2
    assert scene_prop.call_args == call(scene)

    scene_prop.side_effect = AssertionError()

    missing_scene = "Missing scene"
    data["scene"] = missing_scene

    await opp.services.async_call(DOMAIN, yamaha.SERVICE_SELECT_SCENE, data, True)

    assert f"Scene '{missing_scene}' does not exist!" in caplog.text
