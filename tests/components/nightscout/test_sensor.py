"""The sensor tests for the Nightscout platform."""

from openpeerpower.components.nightscout.const import (
    ATTR_DATE,
    ATTR_DELTA,
    ATTR_DEVICE,
    ATTR_DIRECTION,
)
from openpeerpower.const import ATTR_ICON, STATE_UNAVAILABLE

from tests.components.nightscout import (
    GLUCOSE_READINGS,
    init_integration,
    init_integration_empty_response,
    init_integration_unavailable,
)


async def test_sensor_state(opp):
    """Test sensor state data."""
    await init_integration(opp)

    test_glucose_sensor = opp.states.get("sensor.blood_sugar")
    assert test_glucose_sensor.state == str(
        GLUCOSE_READINGS[0].sgv  # pylint: disable=maybe-no-member
    )


async def test_sensor_error(opp):
    """Test sensor state data."""
    await init_integration_unavailable(opp)

    test_glucose_sensor = opp.states.get("sensor.blood_sugar")
    assert test_glucose_sensor.state == STATE_UNAVAILABLE


async def test_sensor_empty_response(opp):
    """Test sensor state data."""
    await init_integration_empty_response(opp)

    test_glucose_sensor = opp.states.get("sensor.blood_sugar")
    assert test_glucose_sensor.state == STATE_UNAVAILABLE


async def test_sensor_attributes(opp):
    """Test sensor attributes."""
    await init_integration(opp)

    test_glucose_sensor = opp.states.get("sensor.blood_sugar")
    reading = GLUCOSE_READINGS[0]
    assert reading is not None

    attr = test_glucose_sensor.attributes
    assert attr[ATTR_DATE] == reading.date  # pylint: disable=maybe-no-member
    assert attr[ATTR_DELTA] == reading.delta  # pylint: disable=maybe-no-member
    assert attr[ATTR_DEVICE] == reading.device  # pylint: disable=maybe-no-member
    assert attr[ATTR_DIRECTION] == reading.direction  # pylint: disable=maybe-no-member
    assert attr[ATTR_ICON] == "mdi:arrow-bottom-right"
