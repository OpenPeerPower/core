"""Test qwikswitch sensors."""
import asyncio
from unittest.mock import Mock

from aiohttp.client_exceptions import ClientError
import pytest
from yarl import URL

from openpeerpower.components.qwikswitch import DOMAIN as QWIKSWITCH
from openpeerpower.setup import async_setup_component

from tests.test_util.aiohttp import AiohttpClientMockResponse, MockLongPollSideEffect


@pytest.fixture
def qs_devices():
    """Return a set of devices as a response."""
    return [
        {
            "id": "@a00001",
            "name": "Switch 1",
            "type": "rel",
            "val": "OFF",
            "time": "1522777506",
            "rssi": "51%",
        },
        {
            "id": "@a00002",
            "name": "Light 2",
            "type": "rel",
            "val": "ON",
            "time": "1522777507",
            "rssi": "45%",
        },
        {
            "id": "@a00003",
            "name": "Dim 3",
            "type": "dim",
            "val": "280c00",
            "time": "1522777544",
            "rssi": "62%",
        },
    ]


EMPTY_PACKET = {"cmd": ""}


async def test_binary_sensor_device(opp, aioclient_mock, qs_devices):
    """Test a binary sensor device."""
    config = {
        "qwikswitch": {
            "sensors": {"name": "s1", "id": "@a00001", "channel": 1, "type": "imod"}
        }
    }
    aioclient_mock.get("http://127.0.0.1:2020/&device", json=qs_devices)
    listen_mock = MockLongPollSideEffect()
    aioclient_mock.get("http://127.0.0.1:2020/&listen", side_effect=listen_mock)
    assert await async_setup_component(opp, QWIKSWITCH, config)
    await opp.async_start()
    await opp.async_block_till_done()

    # verify initial state is off per the 'val' in qs_devices
    state_obj = opp.states.get("binary_sensor.s1")
    assert state_obj.state == "off"

    # receive turn on command from network
    listen_mock.queue_response(
        json={"id": "@a00001", "cmd": "STATUS.ACK", "data": "4e0e1601", "rssi": "61%"}
    )
    await asyncio.sleep(0.01)
    await opp.async_block_till_done()
    state_obj = opp.states.get("binary_sensor.s1")
    assert state_obj.state == "on"

    # receive turn off command from network
    listen_mock.queue_response(
        json={"id": "@a00001", "cmd": "STATUS.ACK", "data": "4e0e1701", "rssi": "61%"},
    )
    await asyncio.sleep(0.01)
    await opp.async_block_till_done()
    state_obj = opp.states.get("binary_sensor.s1")
    assert state_obj.state == "off"

    listen_mock.stop()


async def test_sensor_device(opp, aioclient_mock, qs_devices):
    """Test a sensor device."""
    config = {
        "qwikswitch": {
            "sensors": {
                "name": "ss1",
                "id": "@a00001",
                "channel": 1,
                "type": "qwikcord",
            }
        }
    }
    aioclient_mock.get("http://127.0.0.1:2020/&device", json=qs_devices)
    listen_mock = MockLongPollSideEffect()
    aioclient_mock.get("http://127.0.0.1:2020/&listen", side_effect=listen_mock)
    assert await async_setup_component(opp, QWIKSWITCH, config)
    await opp.async_start()
    await opp.async_block_till_done()

    state_obj = opp.states.get("sensor.ss1")
    assert state_obj.state == "None"

    # receive command that sets the sensor value
    listen_mock.queue_response(
        json={"id": "@a00001", "name": "ss1", "type": "rel", "val": "4733800001a00000"},
    )
    await asyncio.sleep(0.01)
    await opp.async_block_till_done()
    state_obj = opp.states.get("sensor.ss1")
    assert state_obj.state == "416"

    listen_mock.stop()


async def test_switch_device(opp, aioclient_mock, qs_devices):
    """Test a switch device."""

    async def get_devices_json(method, url, data):
        return AiohttpClientMockResponse(method=method, url=url, json=qs_devices)

    config = {"qwikswitch": {"switches": ["@a00001"]}}
    aioclient_mock.get("http://127.0.0.1:2020/&device", side_effect=get_devices_json)
    listen_mock = MockLongPollSideEffect()
    aioclient_mock.get("http://127.0.0.1:2020/&listen", side_effect=listen_mock)
    assert await async_setup_component(opp, QWIKSWITCH, config)
    await opp.async_start()
    await opp.async_block_till_done()

    # verify initial state is off per the 'val' in qs_devices
    state_obj = opp.states.get("switch.switch_1")
    assert state_obj.state == "off"

    # ask.opp to turn on and verify command is sent to device
    aioclient_mock.mock_calls.clear()
    aioclient_mock.get("http://127.0.0.1:2020/@a00001=100", json={"data": "OK"})
    await opp.services.async_call(
        "switch", "turn_on", {"entity_id": "switch.switch_1"}, blocking=True
    )
    await asyncio.sleep(0.01)
    assert (
        "GET",
        URL("http://127.0.0.1:2020/@a00001=100"),
        None,
        None,
    ) in aioclient_mock.mock_calls
    # verify state is on
    state_obj = opp.states.get("switch.switch_1")
    assert state_obj.state == "on"

    # ask.opp to turn off and verify command is sent to device
    aioclient_mock.mock_calls.clear()
    aioclient_mock.get("http://127.0.0.1:2020/@a00001=0", json={"data": "OK"})
    await opp.services.async_call(
        "switch", "turn_off", {"entity_id": "switch.switch_1"}, blocking=True
    )
    assert (
        "GET",
        URL("http://127.0.0.1:2020/@a00001=0"),
        None,
        None,
    ) in aioclient_mock.mock_calls
    # verify state is off
    state_obj = opp.states.get("switch.switch_1")
    assert state_obj.state == "off"

    # check if setting the value in the network show in opp
    qs_devices[0]["val"] = "ON"
    listen_mock.queue_response(json=EMPTY_PACKET)
    await opp.async_block_till_done()
    state_obj = opp.states.get("switch.switch_1")
    assert state_obj.state == "on"

    listen_mock.stop()


async def test_light_device(opp, aioclient_mock, qs_devices):
    """Test a light device."""

    async def get_devices_json(method, url, data):
        return AiohttpClientMockResponse(method=method, url=url, json=qs_devices)

    config = {"qwikswitch": {}}
    aioclient_mock.get("http://127.0.0.1:2020/&device", side_effect=get_devices_json)
    listen_mock = MockLongPollSideEffect()
    aioclient_mock.get("http://127.0.0.1:2020/&listen", side_effect=listen_mock)
    assert await async_setup_component(opp, QWIKSWITCH, config)
    await opp.async_start()
    await opp.async_block_till_done()

    # verify initial state is on per the 'val' in qs_devices
    state_obj = opp.states.get("light.dim_3")
    assert state_obj.state == "on"
    assert state_obj.attributes["brightness"] == 255

    # ask.opp to turn off and verify command is sent to device
    aioclient_mock.mock_calls.clear()
    aioclient_mock.get("http://127.0.0.1:2020/@a00003=0", json={"data": "OK"})
    await opp.services.async_call(
        "light", "turn_off", {"entity_id": "light.dim_3"}, blocking=True
    )
    await asyncio.sleep(0.01)
    assert (
        "GET",
        URL("http://127.0.0.1:2020/@a00003=0"),
        None,
        None,
    ) in aioclient_mock.mock_calls
    state_obj = opp.states.get("light.dim_3")
    assert state_obj.state == "off"

    # change brightness in network and check that.opp updates
    qs_devices[2]["val"] = "280c55"  # half dimmed
    listen_mock.queue_response(json=EMPTY_PACKET)
    await asyncio.sleep(0.01)
    await opp.async_block_till_done()
    state_obj = opp.states.get("light.dim_3")
    assert state_obj.state == "on"
    assert 16 < state_obj.attributes["brightness"] < 240

    # turn off in the network and see that it is off in opp as well
    qs_devices[2]["val"] = "280c78"  # off
    listen_mock.queue_response(json=EMPTY_PACKET)
    await asyncio.sleep(0.01)
    await opp.async_block_till_done()
    state_obj = opp.states.get("light.dim_3")
    assert state_obj.state == "off"

    # ask.opp to turn on and verify command is sent to device
    aioclient_mock.mock_calls.clear()
    aioclient_mock.get("http://127.0.0.1:2020/@a00003=100", json={"data": "OK"})
    await opp.services.async_call(
        "light", "turn_on", {"entity_id": "light.dim_3"}, blocking=True
    )
    assert (
        "GET",
        URL("http://127.0.0.1:2020/@a00003=100"),
        None,
        None,
    ) in aioclient_mock.mock_calls
    await opp.async_block_till_done()
    state_obj = opp.states.get("light.dim_3")
    assert state_obj.state == "on"

    listen_mock.stop()


async def test_button(opp, aioclient_mock, qs_devices):
    """Test that buttons fire an event."""

    async def get_devices_json(method, url, data):
        return AiohttpClientMockResponse(method=method, url=url, json=qs_devices)

    config = {"qwikswitch": {"button_events": "TOGGLE"}}
    aioclient_mock.get("http://127.0.0.1:2020/&device", side_effect=get_devices_json)
    listen_mock = MockLongPollSideEffect()
    aioclient_mock.get("http://127.0.0.1:2020/&listen", side_effect=listen_mock)
    assert await async_setup_component(opp, QWIKSWITCH, config)
    await opp.async_start()
    await opp.async_block_till_done()

    button_pressed = Mock()
    opp.bus.async_listen_once("qwikswitch.button.@a00002", button_pressed)
    listen_mock.queue_response(
        json={"id": "@a00002", "cmd": "TOGGLE"},
    )
    await asyncio.sleep(0.01)
    await opp.async_block_till_done()
    button_pressed.assert_called_once()

    listen_mock.stop()


async def test_failed_update_devices(opp, aioclient_mock):
    """Test that code behaves correctly when unable to get the devices."""

    config = {"qwikswitch": {}}
    aioclient_mock.get("http://127.0.0.1:2020/&device", exc=ClientError())
    listen_mock = MockLongPollSideEffect()
    aioclient_mock.get("http://127.0.0.1:2020/&listen", side_effect=listen_mock)
    assert not await async_setup_component(opp, QWIKSWITCH, config)
    await opp.async_start()
    await opp.async_block_till_done()
    listen_mock.stop()


async def test_single_invalid_sensor(opp, aioclient_mock, qs_devices):
    """Test that a single misconfigured sensor doesn't block the others."""

    config = {
        "qwikswitch": {
            "sensors": [
                {"name": "ss1", "id": "@a00001", "channel": 1, "type": "qwikcord"},
                {"name": "ss2", "id": "@a00002", "channel": 1, "type": "ERROR_TYPE"},
                {"name": "ss3", "id": "@a00003", "channel": 1, "type": "qwikcord"},
            ]
        }
    }
    aioclient_mock.get("http://127.0.0.1:2020/&device", json=qs_devices)
    listen_mock = MockLongPollSideEffect()
    aioclient_mock.get("http://127.0.0.1:2020/&listen", side_effect=listen_mock)
    assert await async_setup_component(opp, QWIKSWITCH, config)
    await opp.async_start()
    await opp.async_block_till_done()
    await asyncio.sleep(0.01)
    assert opp.states.get("sensor.ss1")
    assert not opp.states.get("sensor.ss2")
    assert opp.states.get("sensor.ss3")
    listen_mock.stop()


async def test_non_binary_sensor_with_binary_args(
    opp, aioclient_mock, qs_devices, caplog
):
    """Test that the system logs a warning when a non-binary device has binary specific args."""

    config = {
        "qwikswitch": {
            "sensors": [
                {
                    "name": "ss1",
                    "id": "@a00001",
                    "channel": 1,
                    "type": "qwikcord",
                    "invert": True,
                },
            ]
        }
    }
    aioclient_mock.get("http://127.0.0.1:2020/&device", json=qs_devices)
    listen_mock = MockLongPollSideEffect()
    aioclient_mock.get("http://127.0.0.1:2020/&listen", side_effect=listen_mock)
    assert await async_setup_component(opp, QWIKSWITCH, config)
    await opp.async_start()
    await opp.async_block_till_done()
    await asyncio.sleep(0.01)
    await opp.async_block_till_done()
    assert opp.states.get("sensor.ss1")
    assert "invert should only be used for binary_sensors" in caplog.text
    listen_mock.stop()


async def test_non_relay_switch(opp, aioclient_mock, qs_devices, caplog):
    """Test that the system logs a warning when a switch is configured for a device that is not a relay."""

    config = {"qwikswitch": {"switches": ["@a00003"]}}
    aioclient_mock.get("http://127.0.0.1:2020/&device", json=qs_devices)
    listen_mock = MockLongPollSideEffect()
    aioclient_mock.get("http://127.0.0.1:2020/&listen", side_effect=listen_mock)
    assert await async_setup_component(opp, QWIKSWITCH, config)
    await opp.async_start()
    await opp.async_block_till_done()
    await asyncio.sleep(0.01)
    await opp.async_block_till_done()
    assert not opp.states.get("switch.dim_3")
    assert "You specified a switch that is not a relay @a00003" in caplog.text
    listen_mock.stop()


async def test_unknown_device(opp, aioclient_mock, qs_devices, caplog):
    """Test that the system logs a warning when a network device has unknown type."""

    config = {"qwikswitch": {}}
    qs_devices[1]["type"] = "ERROR_TYPE"
    aioclient_mock.get("http://127.0.0.1:2020/&device", json=qs_devices)
    listen_mock = MockLongPollSideEffect()
    aioclient_mock.get("http://127.0.0.1:2020/&listen", side_effect=listen_mock)
    assert await async_setup_component(opp, QWIKSWITCH, config)
    await opp.async_start()
    await opp.async_block_till_done()
    await asyncio.sleep(0.01)
    await opp.async_block_till_done()
    assert opp.states.get("light.switch_1")
    assert not opp.states.get("light.light_2")
    assert opp.states.get("light.dim_3")
    assert "Ignored unknown QSUSB device" in caplog.text
    listen_mock.stop()


async def test_no_discover_info(opp, opp_storage, aioclient_mock, caplog):
    """Test that discovery with no discovery_info does not result in errors."""
    config = {
        "qwikswitch": {},
        "light": {"platform": "qwikswitch"},
        "switch": {"platform": "qwikswitch"},
        "sensor": {"platform": "qwikswitch"},
        "binary_sensor": {"platform": "qwikswitch"},
    }
    aioclient_mock.get(
        "http://127.0.0.1:2020/&device",
        json=[
            {
                "id": "@a00001",
                "name": "Switch 1",
                "type": "ERROR_TYPE",
                "val": "OFF",
                "time": "1522777506",
                "rssi": "51%",
            },
        ],
    )
    listen_mock = MockLongPollSideEffect()
    aioclient_mock.get("http://127.0.0.1:2020/&listen", side_effect=listen_mock)
    assert await async_setup_component(opp, "light", config)
    assert await async_setup_component(opp, "switch", config)
    assert await async_setup_component(opp, "sensor", config)
    assert await async_setup_component(opp, "binary_sensor", config)
    await opp.async_start()
    await opp.async_block_till_done()
    assert "Error while setting up qwikswitch platform" not in caplog.text
    listen_mock.stop()
