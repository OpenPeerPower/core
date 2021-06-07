"""Test the sma sensor platform."""
from openpeerpower.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    ENERGY_KILO_WATT_HOUR,
    POWER_WATT,
)

from . import MOCK_CUSTOM_SENSOR


async def test_sensors(opp, init_integration):
    """Test states of the sensors."""
    state = opp.states.get("sensor.grid_power")
    assert state
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == POWER_WATT

    state = opp.states.get(f"sensor.{MOCK_CUSTOM_SENSOR['name']}")
    assert state
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == ENERGY_KILO_WATT_HOUR
