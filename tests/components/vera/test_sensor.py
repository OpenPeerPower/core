"""Vera tests."""
from __future__ import annotations

from typing import Any, Callable
from unittest.mock import MagicMock

import pyvera as pv

from openpeerpower.const import ATTR_UNIT_OF_MEASUREMENT, LIGHT_LUX, PERCENTAGE
from openpeerpower.core import OpenPeerPower

from .common import ComponentFactory, new_simple_controller_config


async def run_sensor_test(
    opp: OpenPeerPower,
    vera_component_factory: ComponentFactory,
    category: int,
    class_property: str,
    assert_states: tuple[tuple[Any, Any]],
    assert_unit_of_measurement: str = None,
    setup_callback: Callable[[pv.VeraController], None] = None,
) -> None:
    """Test generic sensor."""
    vera_device: pv.VeraSensor = MagicMock(spec=pv.VeraSensor)
    vera_device.device_id = 1
    vera_device.vera_device_id = vera_device.device_id
    vera_device.comm_failure = False
    vera_device.name = "dev1"
    vera_device.category = category
    setattr(vera_device, class_property, "33")
    entity_id = "sensor.dev1_1"

    component_data = await vera_component_factory.configure_component(
        opp=opp,
        controller_config=new_simple_controller_config(
            devices=(vera_device,), setup_callback=setup_callback
        ),
    )
    update_callback = component_data.controller_data[0].update_callback

    for (initial_value, state_value) in assert_states:
        setattr(vera_device, class_property, initial_value)
        update_callback(vera_device)
        await opp.async_block_till_done()
        state = opp.states.get(entity_id)
        assert state.state == state_value
        if assert_unit_of_measurement:
            assert (
                state.attributes[ATTR_UNIT_OF_MEASUREMENT] == assert_unit_of_measurement
            )


async def test_temperature_sensor_f(
    opp: OpenPeerPower, vera_component_factory: ComponentFactory
) -> None:
    """Test function."""

    def setup_callback(controller: pv.VeraController) -> None:
        controller.temperature_units = "F"

    await run_sensor_test(
        opp=opp,
        vera_component_factory=vera_component_factory,
        category=pv.CATEGORY_TEMPERATURE_SENSOR,
        class_property="temperature",
        assert_states=(("33", "1"), ("44", "7")),
        setup_callback=setup_callback,
    )


async def test_temperature_sensor_c(
    opp: OpenPeerPower, vera_component_factory: ComponentFactory
) -> None:
    """Test function."""
    await run_sensor_test(
        opp=opp,
        vera_component_factory=vera_component_factory,
        category=pv.CATEGORY_TEMPERATURE_SENSOR,
        class_property="temperature",
        assert_states=(("33", "33"), ("44", "44")),
    )


async def test_light_sensor(
    opp: OpenPeerPower, vera_component_factory: ComponentFactory
) -> None:
    """Test function."""
    await run_sensor_test(
        opp=opp,
        vera_component_factory=vera_component_factory,
        category=pv.CATEGORY_LIGHT_SENSOR,
        class_property="light",
        assert_states=(("12", "12"), ("13", "13")),
        assert_unit_of_measurement=LIGHT_LUX,
    )


async def test_uv_sensor(
    opp: OpenPeerPower, vera_component_factory: ComponentFactory
) -> None:
    """Test function."""
    await run_sensor_test(
        opp=opp,
        vera_component_factory=vera_component_factory,
        category=pv.CATEGORY_UV_SENSOR,
        class_property="light",
        assert_states=(("12", "12"), ("13", "13")),
        assert_unit_of_measurement="level",
    )


async def test_humidity_sensor(
    opp: OpenPeerPower, vera_component_factory: ComponentFactory
) -> None:
    """Test function."""
    await run_sensor_test(
        opp=opp,
        vera_component_factory=vera_component_factory,
        category=pv.CATEGORY_HUMIDITY_SENSOR,
        class_property="humidity",
        assert_states=(("12", "12"), ("13", "13")),
        assert_unit_of_measurement=PERCENTAGE,
    )


async def test_power_meter_sensor(
    opp: OpenPeerPower, vera_component_factory: ComponentFactory
) -> None:
    """Test function."""
    await run_sensor_test(
        opp=opp,
        vera_component_factory=vera_component_factory,
        category=pv.CATEGORY_POWER_METER,
        class_property="power",
        assert_states=(("12", "12"), ("13", "13")),
        assert_unit_of_measurement="watts",
    )


async def test_trippable_sensor(
    opp: OpenPeerPower, vera_component_factory: ComponentFactory
) -> None:
    """Test function."""

    def setup_callback(controller: pv.VeraController) -> None:
        controller.get_devices()[0].is_trippable = True

    await run_sensor_test(
        opp=opp,
        vera_component_factory=vera_component_factory,
        category=999,
        class_property="is_tripped",
        assert_states=((True, "Tripped"), (False, "Not Tripped"), (True, "Tripped")),
        setup_callback=setup_callback,
    )


async def test_unknown_sensor(
    opp: OpenPeerPower, vera_component_factory: ComponentFactory
) -> None:
    """Test function."""

    def setup_callback(controller: pv.VeraController) -> None:
        controller.get_devices()[0].is_trippable = False

    await run_sensor_test(
        opp=opp,
        vera_component_factory=vera_component_factory,
        category=999,
        class_property="is_tripped",
        assert_states=((True, "Unknown"), (False, "Unknown"), (True, "Unknown")),
        setup_callback=setup_callback,
    )


async def test_scene_controller_sensor(
    opp: OpenPeerPower, vera_component_factory: ComponentFactory
) -> None:
    """Test function."""
    vera_device: pv.VeraSensor = MagicMock(spec=pv.VeraSensor)
    vera_device.device_id = 1
    vera_device.vera_device_id = vera_device.device_id
    vera_device.comm_failure = False
    vera_device.name = "dev1"
    vera_device.category = pv.CATEGORY_SCENE_CONTROLLER
    vera_device.get_last_scene_id = MagicMock(return_value="id0")
    vera_device.get_last_scene_time = MagicMock(return_value="0000")
    entity_id = "sensor.dev1_1"

    component_data = await vera_component_factory.configure_component(
        opp=opp,
        controller_config=new_simple_controller_config(devices=(vera_device,)),
    )
    update_callback = component_data.controller_data[0].update_callback

    vera_device.get_last_scene_time.return_value = "1111"
    update_callback(vera_device)
    await opp.async_block_till_done()
    assert opp.states.get(entity_id).state == "id0"
