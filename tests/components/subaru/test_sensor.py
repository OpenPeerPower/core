"""Test Subaru sensors."""
from openpeerpower.components.subaru.const import VEHICLE_NAME
from openpeerpower.components.subaru.sensor import (
    API_GEN_2_SENSORS,
    EV_SENSORS,
    SAFETY_SENSORS,
    SENSOR_FIELD,
    SENSOR_TYPE,
)
from openpeerpower.util import slugify
from openpeerpower.util.unit_system import IMPERIAL_SYSTEM

from .api_responses import (
    EXPECTED_STATE_EV_IMPERIAL,
    EXPECTED_STATE_EV_METRIC,
    EXPECTED_STATE_EV_UNAVAILABLE,
    TEST_VIN_2_EV,
    VEHICLE_DATA,
    VEHICLE_STATUS_EV,
)

from tests.components.subaru.conftest import setup_subaru_integration

VEHICLE_NAME = VEHICLE_DATA[TEST_VIN_2_EV][VEHICLE_NAME]


async def test_sensors_ev_imperial(opp):
    """Test sensors supporting imperial units."""
    opp.config.units = IMPERIAL_SYSTEM
    await setup_subaru_integration(
        opp,
        vehicle_list=[TEST_VIN_2_EV],
        vehicle_data=VEHICLE_DATA[TEST_VIN_2_EV],
        vehicle_status=VEHICLE_STATUS_EV,
    )
    _assert_data(opp, EXPECTED_STATE_EV_IMPERIAL)


async def test_sensors_ev_metric(opp, ev_entry):
    """Test sensors supporting metric units."""
    _assert_data(opp, EXPECTED_STATE_EV_METRIC)


async def test_sensors_missing_vin_data(opp):
    """Test for missing VIN dataset."""
    await setup_subaru_integration(
        opp,
        vehicle_list=[TEST_VIN_2_EV],
        vehicle_data=VEHICLE_DATA[TEST_VIN_2_EV],
        vehicle_status=None,
    )
    _assert_data(opp, EXPECTED_STATE_EV_UNAVAILABLE)


def _assert_data(opp, expected_state):
    sensor_list = EV_SENSORS
    sensor_list.extend(API_GEN_2_SENSORS)
    sensor_list.extend(SAFETY_SENSORS)
    expected_states = {}
    for item in sensor_list:
        expected_states[
            f"sensor.{slugify(f'{VEHICLE_NAME} {item[SENSOR_TYPE]}')}"
        ] = expected_state[item[SENSOR_FIELD]]

    for sensor in expected_states:
        actual = opp.states.get(sensor)
        assert actual.state == expected_states[sensor]
