"""Test different accessory types: Sensors."""
from openpeerpower.components.homekit import get_accessory
from openpeerpower.components.homekit.const import (
    DEVICE_CLASS_MOTION,
    PROP_CELSIUS,
    THRESHOLD_CO,
    THRESHOLD_CO2,
)
from openpeerpower.components.homekit.type_sensors import (
    BINARY_SENSOR_SERVICE_MAP,
    AirQualitySensor,
    BinarySensor,
    CarbonDioxideSensor,
    CarbonMonoxideSensor,
    HumiditySensor,
    LightSensor,
    TemperatureSensor,
)
from openpeerpower.const import (
    ATTR_DEVICE_CLASS,
    ATTR_UNIT_OF_MEASUREMENT,
    EVENT_OPENPEERPOWER_START,
    PERCENTAGE,
    STATE_HOME,
    STATE_NOT_HOME,
    STATE_OFF,
    STATE_ON,
    STATE_UNKNOWN,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
from openpeerpower.core import CoreState
from openpeerpower.helpers import entity_registry as er


async def test_temperature(opp, hk_driver):
    """Test if accessory is updated after state change."""
    entity_id = "sensor.temperature"

    opp.states.async_set(entity_id, None)
    await opp.async_block_till_done()
    acc = TemperatureSensor(opp, hk_driver, "Temperature", entity_id, 2, None)
    await acc.run()
    await opp.async_block_till_done()

    assert acc.aid == 2
    assert acc.category == 10  # Sensor

    assert acc.char_temp.value == 0.0
    for key, value in PROP_CELSIUS.items():
        assert acc.char_temp.properties[key] == value

    opp.states.async_set(
        entity_id, STATE_UNKNOWN, {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS}
    )
    await opp.async_block_till_done()
    assert acc.char_temp.value == 0.0

    opp.states.async_set(entity_id, "20", {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS})
    await opp.async_block_till_done()
    assert acc.char_temp.value == 20

    opp.states.async_set(entity_id, "75.2", {ATTR_UNIT_OF_MEASUREMENT: TEMP_FAHRENHEIT})
    await opp.async_block_till_done()
    assert acc.char_temp.value == 24


async def test_humidity(opp, hk_driver):
    """Test if accessory is updated after state change."""
    entity_id = "sensor.humidity"

    opp.states.async_set(entity_id, None)
    await opp.async_block_till_done()
    acc = HumiditySensor(opp, hk_driver, "Humidity", entity_id, 2, None)
    await acc.run()
    await opp.async_block_till_done()

    assert acc.aid == 2
    assert acc.category == 10  # Sensor

    assert acc.char_humidity.value == 0

    opp.states.async_set(entity_id, STATE_UNKNOWN)
    await opp.async_block_till_done()
    assert acc.char_humidity.value == 0

    opp.states.async_set(entity_id, "20")
    await opp.async_block_till_done()
    assert acc.char_humidity.value == 20


async def test_air_quality(opp, hk_driver):
    """Test if accessory is updated after state change."""
    entity_id = "sensor.air_quality"

    opp.states.async_set(entity_id, None)
    await opp.async_block_till_done()
    acc = AirQualitySensor(opp, hk_driver, "Air Quality", entity_id, 2, None)
    await acc.run()
    await opp.async_block_till_done()

    assert acc.aid == 2
    assert acc.category == 10  # Sensor

    assert acc.char_density.value == 0
    assert acc.char_quality.value == 0

    opp.states.async_set(entity_id, STATE_UNKNOWN)
    await opp.async_block_till_done()
    assert acc.char_density.value == 0
    assert acc.char_quality.value == 0

    opp.states.async_set(entity_id, "34")
    await opp.async_block_till_done()
    assert acc.char_density.value == 34
    assert acc.char_quality.value == 1

    opp.states.async_set(entity_id, "200")
    await opp.async_block_till_done()
    assert acc.char_density.value == 200
    assert acc.char_quality.value == 5


async def test_co(opp, hk_driver):
    """Test if accessory is updated after state change."""
    entity_id = "sensor.co"

    opp.states.async_set(entity_id, None)
    await opp.async_block_till_done()
    acc = CarbonMonoxideSensor(opp, hk_driver, "CO", entity_id, 2, None)
    await acc.run()
    await opp.async_block_till_done()

    assert acc.aid == 2
    assert acc.category == 10  # Sensor

    assert acc.char_level.value == 0
    assert acc.char_peak.value == 0
    assert acc.char_detected.value == 0

    opp.states.async_set(entity_id, STATE_UNKNOWN)
    await opp.async_block_till_done()
    assert acc.char_level.value == 0
    assert acc.char_peak.value == 0
    assert acc.char_detected.value == 0

    value = 32
    assert value > THRESHOLD_CO
    opp.states.async_set(entity_id, str(value))
    await opp.async_block_till_done()
    assert acc.char_level.value == 32
    assert acc.char_peak.value == 32
    assert acc.char_detected.value == 1

    value = 10
    assert value < THRESHOLD_CO
    opp.states.async_set(entity_id, str(value))
    await opp.async_block_till_done()
    assert acc.char_level.value == 10
    assert acc.char_peak.value == 32
    assert acc.char_detected.value == 0


async def test_co2(opp, hk_driver):
    """Test if accessory is updated after state change."""
    entity_id = "sensor.co2"

    opp.states.async_set(entity_id, None)
    await opp.async_block_till_done()
    acc = CarbonDioxideSensor(opp, hk_driver, "CO2", entity_id, 2, None)
    await acc.run()
    await opp.async_block_till_done()

    assert acc.aid == 2
    assert acc.category == 10  # Sensor

    assert acc.char_level.value == 0
    assert acc.char_peak.value == 0
    assert acc.char_detected.value == 0

    opp.states.async_set(entity_id, STATE_UNKNOWN)
    await opp.async_block_till_done()
    assert acc.char_level.value == 0
    assert acc.char_peak.value == 0
    assert acc.char_detected.value == 0

    value = 1100
    assert value > THRESHOLD_CO2
    opp.states.async_set(entity_id, str(value))
    await opp.async_block_till_done()
    assert acc.char_level.value == 1100
    assert acc.char_peak.value == 1100
    assert acc.char_detected.value == 1

    value = 800
    assert value < THRESHOLD_CO2
    opp.states.async_set(entity_id, str(value))
    await opp.async_block_till_done()
    assert acc.char_level.value == 800
    assert acc.char_peak.value == 1100
    assert acc.char_detected.value == 0


async def test_light(opp, hk_driver):
    """Test if accessory is updated after state change."""
    entity_id = "sensor.light"

    opp.states.async_set(entity_id, None)
    await opp.async_block_till_done()
    acc = LightSensor(opp, hk_driver, "Light", entity_id, 2, None)
    await acc.run()
    await opp.async_block_till_done()

    assert acc.aid == 2
    assert acc.category == 10  # Sensor

    assert acc.char_light.value == 0.0001

    opp.states.async_set(entity_id, STATE_UNKNOWN)
    await opp.async_block_till_done()
    assert acc.char_light.value == 0.0001

    opp.states.async_set(entity_id, "300")
    await opp.async_block_till_done()
    assert acc.char_light.value == 300


async def test_binary(opp, hk_driver):
    """Test if accessory is updated after state change."""
    entity_id = "binary_sensor.opening"

    opp.states.async_set(entity_id, STATE_UNKNOWN, {ATTR_DEVICE_CLASS: "opening"})
    await opp.async_block_till_done()

    acc = BinarySensor(opp, hk_driver, "Window Opening", entity_id, 2, None)
    await acc.run()
    await opp.async_block_till_done()

    assert acc.aid == 2
    assert acc.category == 10  # Sensor

    assert acc.char_detected.value == 0

    opp.states.async_set(entity_id, STATE_ON, {ATTR_DEVICE_CLASS: "opening"})
    await opp.async_block_till_done()
    assert acc.char_detected.value == 1

    opp.states.async_set(entity_id, STATE_OFF, {ATTR_DEVICE_CLASS: "opening"})
    await opp.async_block_till_done()
    assert acc.char_detected.value == 0

    opp.states.async_set(entity_id, STATE_HOME, {ATTR_DEVICE_CLASS: "opening"})
    await opp.async_block_till_done()
    assert acc.char_detected.value == 1

    opp.states.async_set(entity_id, STATE_NOT_HOME, {ATTR_DEVICE_CLASS: "opening"})
    await opp.async_block_till_done()
    assert acc.char_detected.value == 0

    opp.states.async_remove(entity_id)
    await opp.async_block_till_done()
    assert acc.char_detected.value == 0


async def test_motion_uses_bool(opp, hk_driver):
    """Test if accessory is updated after state change."""
    entity_id = "binary_sensor.motion"

    opp.states.async_set(
        entity_id, STATE_UNKNOWN, {ATTR_DEVICE_CLASS: DEVICE_CLASS_MOTION}
    )
    await opp.async_block_till_done()

    acc = BinarySensor(opp, hk_driver, "Motion Sensor", entity_id, 2, None)
    await acc.run()
    await opp.async_block_till_done()

    assert acc.aid == 2
    assert acc.category == 10  # Sensor

    assert acc.char_detected.value is False

    opp.states.async_set(entity_id, STATE_ON, {ATTR_DEVICE_CLASS: DEVICE_CLASS_MOTION})
    await opp.async_block_till_done()
    assert acc.char_detected.value is True

    opp.states.async_set(entity_id, STATE_OFF, {ATTR_DEVICE_CLASS: DEVICE_CLASS_MOTION})
    await opp.async_block_till_done()
    assert acc.char_detected.value is False

    opp.states.async_set(
        entity_id, STATE_HOME, {ATTR_DEVICE_CLASS: DEVICE_CLASS_MOTION}
    )
    await opp.async_block_till_done()
    assert acc.char_detected.value is True

    opp.states.async_set(
        entity_id, STATE_NOT_HOME, {ATTR_DEVICE_CLASS: DEVICE_CLASS_MOTION}
    )
    await opp.async_block_till_done()
    assert acc.char_detected.value is False

    opp.states.async_remove(entity_id)
    await opp.async_block_till_done()
    assert acc.char_detected.value is False


async def test_binary_device_classes(opp, hk_driver):
    """Test if services and characteristics are assigned correctly."""
    entity_id = "binary_sensor.demo"

    for device_class, (service, char, _) in BINARY_SENSOR_SERVICE_MAP.items():
        opp.states.async_set(entity_id, STATE_OFF, {ATTR_DEVICE_CLASS: device_class})
        await opp.async_block_till_done()

        acc = BinarySensor(opp, hk_driver, "Binary Sensor", entity_id, 2, None)
        assert acc.get_service(service).display_name == service
        assert acc.char_detected.display_name == char


async def test_sensor_restore(opp, hk_driver, events):
    """Test setting up an entity from state in the event registry."""
    opp.state = CoreState.not_running

    registry = er.async_get(opp)

    registry.async_get_or_create(
        "sensor",
        "generic",
        "1234",
        suggested_object_id="temperature",
        device_class="temperature",
    )
    registry.async_get_or_create(
        "sensor",
        "generic",
        "12345",
        suggested_object_id="humidity",
        device_class="humidity",
        unit_of_measurement=PERCENTAGE,
    )
    opp.bus.async_fire(EVENT_OPENPEERPOWER_START, {})
    await opp.async_block_till_done()

    acc = get_accessory(opp, hk_driver, opp.states.get("sensor.temperature"), 2, {})
    assert acc.category == 10

    acc = get_accessory(opp, hk_driver, opp.states.get("sensor.humidity"), 2, {})
    assert acc.category == 10
