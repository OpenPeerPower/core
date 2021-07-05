"""Test sensor of Airly integration."""
from datetime import timedelta

from openpeerpower.components.airly.sensor import ATTRIBUTION
from openpeerpower.const import (
    ATTR_ATTRIBUTION,
    ATTR_DEVICE_CLASS,
    ATTR_ENTITY_ID,
    ATTR_ICON,
    ATTR_UNIT_OF_MEASUREMENT,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_PRESSURE,
    DEVICE_CLASS_TEMPERATURE,
    PERCENTAGE,
    PRESSURE_HPA,
    STATE_UNAVAILABLE,
    TEMP_CELSIUS,
)
from openpeerpower.helpers import entity_registry as er
from openpeerpower.setup import async_setup_component
from openpeerpower.util.dt import utcnow

from . import API_POINT_URL

from tests.common import async_fire_time_changed, load_fixture
from tests.components.airly import init_integration


async def test_sensor(opp, aioclient_mock):
    """Test states of the sensor."""
    await init_integration(opp, aioclient_mock)
    registry = er.async_get(opp)

    state = opp.states.get("sensor.home_humidity")
    assert state
    assert state.state == "92.8"
    assert state.attributes.get(ATTR_ATTRIBUTION) == ATTRIBUTION
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == PERCENTAGE
    assert state.attributes.get(ATTR_DEVICE_CLASS) == DEVICE_CLASS_HUMIDITY

    entry = registry.async_get("sensor.home_humidity")
    assert entry
    assert entry.unique_id == "123-456-humidity"

    state = opp.states.get("sensor.home_pm1")
    assert state
    assert state.state == "9"
    assert state.attributes.get(ATTR_ATTRIBUTION) == ATTRIBUTION
    assert (
        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        == CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
    )
    assert state.attributes.get(ATTR_ICON) == "mdi:blur"

    entry = registry.async_get("sensor.home_pm1")
    assert entry
    assert entry.unique_id == "123-456-pm1"

    state = opp.states.get("sensor.home_pressure")
    assert state
    assert state.state == "1001"
    assert state.attributes.get(ATTR_ATTRIBUTION) == ATTRIBUTION
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == PRESSURE_HPA
    assert state.attributes.get(ATTR_DEVICE_CLASS) == DEVICE_CLASS_PRESSURE

    entry = registry.async_get("sensor.home_pressure")
    assert entry
    assert entry.unique_id == "123-456-pressure"

    state = opp.states.get("sensor.home_temperature")
    assert state
    assert state.state == "14.2"
    assert state.attributes.get(ATTR_ATTRIBUTION) == ATTRIBUTION
    assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == TEMP_CELSIUS
    assert state.attributes.get(ATTR_DEVICE_CLASS) == DEVICE_CLASS_TEMPERATURE

    entry = registry.async_get("sensor.home_temperature")
    assert entry
    assert entry.unique_id == "123-456-temperature"


async def test_availability(opp, aioclient_mock):
    """Ensure that we mark the entities unavailable correctly when service is offline."""
    await init_integration(opp, aioclient_mock)

    state = opp.states.get("sensor.home_humidity")
    assert state
    assert state.state != STATE_UNAVAILABLE
    assert state.state == "92.8"

    aioclient_mock.clear_requests()
    aioclient_mock.get(API_POINT_URL, exc=ConnectionError())
    future = utcnow() + timedelta(minutes=60)
    async_fire_time_changed(opp, future)
    await opp.async_block_till_done()

    state = opp.states.get("sensor.home_humidity")
    assert state
    assert state.state == STATE_UNAVAILABLE

    aioclient_mock.clear_requests()
    aioclient_mock.get(API_POINT_URL, text=load_fixture("airly_valid_station.json"))
    future = utcnow() + timedelta(minutes=120)
    async_fire_time_changed(opp, future)
    await opp.async_block_till_done()

    state = opp.states.get("sensor.home_humidity")
    assert state
    assert state.state != STATE_UNAVAILABLE
    assert state.state == "92.8"


async def test_manual_update_entity(opp, aioclient_mock):
    """Test manual update entity via service homeasasistant/update_entity."""
    await init_integration(opp, aioclient_mock)

    call_count = aioclient_mock.call_count
    await async_setup_component(opp, "openpeerpower", {})
    await opp.services.async_call(
        "openpeerpower",
        "update_entity",
        {ATTR_ENTITY_ID: ["sensor.home_humidity"]},
        blocking=True,
    )

    assert aioclient_mock.call_count == call_count + 1
