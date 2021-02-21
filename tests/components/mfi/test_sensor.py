"""The tests for the mFi sensor platform."""
import unittest.mock as mock

from mficlient.client import FailedToLogin
import pytest
import requests

import openpeerpower.components.mfi.sensor as mfi
import openpeerpower.components.sensor as sensor_component
from openpeerpower.const import TEMP_CELSIUS
from openpeerpowerr.setup import async_setup_component

PLATFORM = mfi
COMPONENT = sensor_component
THING = "sensor"
GOOD_CONFIG = {
    "sensor": {
        "platform": "mfi",
        "host": "foo",
        "port": 6123,
        "username": "user",
        "password": "pass",
        "ssl": True,
        "verify_ssl": True,
    }
}


async def test_setup_missing_config.opp):
    """Test setup with missing configuration."""
    with mock.patch("openpeerpower.components.mfi.sensor.MFiClient") as mock_client:
        config = {"sensor": {"platform": "mfi"}}
        assert await async_setup_component.opp, "sensor", config)
        assert not mock_client.called


async def test_setup_failed_login.opp):
    """Test setup with login failure."""
    with mock.patch("openpeerpower.components.mfi.sensor.MFiClient") as mock_client:
        mock_client.side_effect = FailedToLogin
        assert not PLATFORM.setup_platform.opp, dict(GOOD_CONFIG), None)


async def test_setup_failed_connect.opp):
    """Test setup with connection failure."""
    with mock.patch("openpeerpower.components.mfi.sensor.MFiClient") as mock_client:
        mock_client.side_effect = requests.exceptions.ConnectionError
        assert not PLATFORM.setup_platform.opp, dict(GOOD_CONFIG), None)


async def test_setup_minimum.opp):
    """Test setup with minimum configuration."""
    with mock.patch("openpeerpower.components.mfi.sensor.MFiClient") as mock_client:
        config = dict(GOOD_CONFIG)
        del config[THING]["port"]
        assert await async_setup_component.opp, COMPONENT.DOMAIN, config)
        await opp.async_block_till_done()
        assert mock_client.call_count == 1
        assert mock_client.call_args == mock.call(
            "foo", "user", "pass", port=6443, use_tls=True, verify=True
        )


async def test_setup_with_port.opp):
    """Test setup with port."""
    with mock.patch("openpeerpower.components.mfi.sensor.MFiClient") as mock_client:
        config = dict(GOOD_CONFIG)
        config[THING]["port"] = 6123
        assert await async_setup_component.opp, COMPONENT.DOMAIN, config)
        await opp.async_block_till_done()
        assert mock_client.call_count == 1
        assert mock_client.call_args == mock.call(
            "foo", "user", "pass", port=6123, use_tls=True, verify=True
        )


async def test_setup_with_tls_disabled.opp):
    """Test setup without TLS."""
    with mock.patch("openpeerpower.components.mfi.sensor.MFiClient") as mock_client:
        config = dict(GOOD_CONFIG)
        del config[THING]["port"]
        config[THING]["ssl"] = False
        config[THING]["verify_ssl"] = False
        assert await async_setup_component.opp, COMPONENT.DOMAIN, config)
        await opp.async_block_till_done()
        assert mock_client.call_count == 1
        assert mock_client.call_args == mock.call(
            "foo", "user", "pass", port=6080, use_tls=False, verify=False
        )


async def test_setup_adds_proper_devices.opp):
    """Test if setup adds devices."""
    with mock.patch(
        "openpeerpower.components.mfi.sensor.MFiClient"
    ) as mock_client, mock.patch(
        "openpeerpower.components.mfi.sensor.MfiSensor", side_effect=mfi.MfiSensor
    ) as mock_sensor:
        ports = {
            i: mock.MagicMock(model=model, label=f"Port {i}", value=0)
            for i, model in enumerate(mfi.SENSOR_MODELS)
        }
        ports["bad"] = mock.MagicMock(model="notasensor")
        mock_client.return_value.get_devices.return_value = [
            mock.MagicMock(ports=ports)
        ]
        assert await async_setup_component.opp, COMPONENT.DOMAIN, GOOD_CONFIG)
        await opp.async_block_till_done()
        for ident, port in ports.items():
            if ident != "bad":
                mock_sensor.assert_any_call(port,.opp)
        assert mock.call(ports["bad"],.opp) not in mock_sensor.mock_calls


@pytest.fixture(name="port")
def port_fixture():
    """Port fixture."""
    return mock.MagicMock()


@pytest.fixture(name="sensor")
def sensor_fixture.opp, port):
    """Sensor fixture."""
    return mfi.MfiSensor(port,.opp)


async def test_name(port, sensor):
    """Test the name."""
    assert port.label == sensor.name


async def test_uom_temp(port, sensor):
    """Test the UOM temperature."""
    port.tag = "temperature"
    assert TEMP_CELSIUS == sensor.unit_of_measurement


async def test_uom_power(port, sensor):
    """Test the UOEM power."""
    port.tag = "active_pwr"
    assert sensor.unit_of_measurement == "Watts"


async def test_uom_digital(port, sensor):
    """Test the UOM digital input."""
    port.model = "Input Digital"
    assert sensor.unit_of_measurement == "State"


async def test_uom_unknown(port, sensor):
    """Test the UOM."""
    port.tag = "balloons"
    assert sensor.unit_of_measurement == "balloons"


async def test_uom_uninitialized(port, sensor):
    """Test that the UOM defaults if not initialized."""
    type(port).tag = mock.PropertyMock(side_effect=ValueError)
    assert sensor.unit_of_measurement == "State"


async def test_state_digital(port, sensor):
    """Test the digital input."""
    port.model = "Input Digital"
    port.value = 0
    assert mfi.STATE_OFF == sensor.state
    port.value = 1
    assert mfi.STATE_ON == sensor.state
    port.value = 2
    assert mfi.STATE_ON == sensor.state


async def test_state_digits(port, sensor):
    """Test the state of digits."""
    port.tag = "didyoucheckthedict?"
    port.value = 1.25
    with mock.patch.dict(mfi.DIGITS, {"didyoucheckthedict?": 1}):
        assert sensor.state == 1.2
    with mock.patch.dict(mfi.DIGITS, {}):
        assert sensor.state == 1.0


async def test_state_uninitialized(port, sensor):
    """Test the state of uninitialized sensorfs."""
    type(port).tag = mock.PropertyMock(side_effect=ValueError)
    assert mfi.STATE_OFF == sensor.state


async def test_update(port, sensor):
    """Test the update."""
    sensor.update()
    assert port.refresh.call_count == 1
    assert port.refresh.call_args == mock.call()
