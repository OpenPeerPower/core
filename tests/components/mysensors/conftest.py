"""Provide common mysensors fixtures."""
import pytest

from openpeerpower.components.mqtt import DOMAIN as MQTT_DOMAIN


@pytest.fixture(name="mqtt")
async def mock_mqtt_fixture(opp):
    """Mock the MQTT integration."""
    opp.config.components.add(MQTT_DOMAIN)
