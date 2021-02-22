"""The tests for the TCP sensor platform."""
from copy import copy
from unittest.mock import call, patch

import pytest

import openpeerpower.components.tcp.sensor as tcp
from openpeerpower.setup import async_setup_component

from tests.common import assert_setup_component

TEST_CONFIG = {
    "sensor": {
        "platform": "tcp",
        tcp.CONF_NAME: "test_name",
        tcp.CONF_HOST: "test_host",
        tcp.CONF_PORT: 12345,
        tcp.CONF_TIMEOUT: tcp.DEFAULT_TIMEOUT + 1,
        tcp.CONF_PAYLOAD: "test_payload",
        tcp.CONF_UNIT_OF_MEASUREMENT: "test_unit",
        tcp.CONF_VALUE_TEMPLATE: "{{ 'test_' + value }}",
        tcp.CONF_VALUE_ON: "test_on",
        tcp.CONF_BUFFER_SIZE: tcp.DEFAULT_BUFFER_SIZE + 1,
    }
}
SENSOR_TEST_CONFIG = TEST_CONFIG["sensor"]
TEST_ENTITY = "sensor.test_name"

KEYS_AND_DEFAULTS = {
    tcp.CONF_NAME: tcp.DEFAULT_NAME,
    tcp.CONF_TIMEOUT: tcp.DEFAULT_TIMEOUT,
    tcp.CONF_UNIT_OF_MEASUREMENT: None,
    tcp.CONF_VALUE_TEMPLATE: None,
    tcp.CONF_VALUE_ON: None,
    tcp.CONF_BUFFER_SIZE: tcp.DEFAULT_BUFFER_SIZE,
}

socket_test_value = "value"


@pytest.fixture(name="mock_socket")
def mock_socket_fixture(mock_select):
    """Mock socket."""
    with patch("openpeerpower.components.tcp.sensor.socket.socket") as mock_socket:
        socket_instance = mock_socket.return_value.__enter__.return_value
        socket_instance.recv.return_value = socket_test_value.encode()
        yield socket_instance


@pytest.fixture(name="mock_select")
def mock_select_fixture():
    """Mock select."""
    with patch(
        "openpeerpower.components.tcp.sensor.select.select",
        return_value=(True, False, False),
    ) as mock_select:
        yield mock_select


async def test_setup_platform_valid_config(opp, mock_socket):
    """Check a valid configuration and call add_entities with sensor."""
    with assert_setup_component(1, "sensor"):
        assert await async_setup_component.opp, "sensor", TEST_CONFIG)
        await.opp.async_block_till_done()


async def test_setup_platform_invalid_config(opp, mock_socket):
    """Check an invalid configuration."""
    with assert_setup_component(0):
        assert await async_setup_component(
           .opp, "sensor", {"sensor": {"platform": "tcp", "porrt": 1234}}
        )
        await.opp.async_block_till_done()


async def test_state.opp, mock_socket, mock_select):
    """Return the contents of _state."""
    assert await async_setup_component.opp, "sensor", TEST_CONFIG)
    await.opp.async_block_till_done()

    state =.opp.states.get(TEST_ENTITY)

    assert state
    assert state.state == "test_value"
    assert (
        state.attributes["unit_of_measurement"]
        == SENSOR_TEST_CONFIG[tcp.CONF_UNIT_OF_MEASUREMENT]
    )
    assert mock_socket.connect.called
    assert mock_socket.connect.call_args == call(
        (SENSOR_TEST_CONFIG["host"], SENSOR_TEST_CONFIG["port"])
    )
    assert mock_socket.send.called
    assert mock_socket.send.call_args == call(SENSOR_TEST_CONFIG["payload"].encode())
    assert mock_select.call_args == call(
        [mock_socket], [], [], SENSOR_TEST_CONFIG[tcp.CONF_TIMEOUT]
    )
    assert mock_socket.recv.called
    assert mock_socket.recv.call_args == call(SENSOR_TEST_CONFIG["buffer_size"])


async def test_config_uses_defaults.opp, mock_socket):
    """Check if defaults were set."""
    config = copy(SENSOR_TEST_CONFIG)

    for key in KEYS_AND_DEFAULTS:
        del config[key]

    with assert_setup_component(1) as result_config:
        assert await async_setup_component.opp, "sensor", {"sensor": config})
        await.opp.async_block_till_done()

    state =.opp.states.get("sensor.tcp_sensor")

    assert state
    assert state.state == "value"

    for key, default in KEYS_AND_DEFAULTS.items():
        assert result_config["sensor"][0].get(key) == default


@pytest.mark.parametrize("sock_attr", ["connect", "send"])
async def test_update_socket_error.opp, mock_socket, sock_attr):
    """Test socket errors during update."""
    socket_method = getattr(mock_socket, sock_attr)
    socket_method.side_effect = OSError("Boom")

    assert await async_setup_component.opp, "sensor", TEST_CONFIG)
    await.opp.async_block_till_done()

    state =.opp.states.get(TEST_ENTITY)

    assert state
    assert state.state == "unknown"


async def test_update_select_fails.opp, mock_socket, mock_select):
    """Test select fails to return a socket for reading."""
    mock_select.return_value = (False, False, False)

    assert await async_setup_component.opp, "sensor", TEST_CONFIG)
    await.opp.async_block_till_done()

    state =.opp.states.get(TEST_ENTITY)

    assert state
    assert state.state == "unknown"


async def test_update_returns_if_template_render_fails.opp, mock_socket):
    """Return None if rendering the template fails."""
    config = copy(SENSOR_TEST_CONFIG)
    config[tcp.CONF_VALUE_TEMPLATE] = "{{ value / 0 }}"

    assert await async_setup_component.opp, "sensor", {"sensor": config})
    await.opp.async_block_till_done()

    state =.opp.states.get(TEST_ENTITY)

    assert state
    assert state.state == "unknown"
