"""The test for the Template sensor platform."""
from datetime import timedelta
from os import path
from unittest.mock import patch

from openpeerpower import config
from openpeerpower.components.template import DOMAIN, SERVICE_RELOAD
from openpeerpower.setup import async_setup_component
from openpeerpower.util import dt as dt_util

from tests.common import async_fire_time_changed


async def test_reloadable(opp):
    """Test that we can reload."""
    opp.states.async_set("sensor.test_sensor", "mytest")

    await async_setup_component(
        opp,
        "sensor",
        {
            "sensor": {
                "platform": DOMAIN,
                "sensors": {
                    "state": {
                        "value_template": "{{ states.sensor.test_sensor.state }}"
                    },
                },
            }
        },
    )
    await opp.async_block_till_done()

    await opp.async_start()
    await opp.async_block_till_done()

    assert opp.states.get("sensor.state").state == "mytest"
    assert len(opp.states.async_all()) == 2

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "template/sensor_configuration.yaml",
    )
    with patch.object(config, "YAML_CONFIG_FILE", yaml_path):
        await opp.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await opp.async_block_till_done()

    assert len(opp.states.async_all()) == 3

    assert opp.states.get("sensor.state") is None
    assert opp.states.get("sensor.watching_tv_in_master_bedroom").state == "off"
    assert float(opp.states.get("sensor.combined_sensor_energy_usage").state) == 0


async def test_reloadable_can_remove(opp):
    """Test that we can reload and remove all template sensors."""
    opp.states.async_set("sensor.test_sensor", "mytest")

    await async_setup_component(
        opp,
        "sensor",
        {
            "sensor": {
                "platform": DOMAIN,
                "sensors": {
                    "state": {
                        "value_template": "{{ states.sensor.test_sensor.state }}"
                    },
                },
            }
        },
    )
    await opp.async_block_till_done()

    await opp.async_start()
    await opp.async_block_till_done()

    assert opp.states.get("sensor.state").state == "mytest"
    assert len(opp.states.async_all()) == 2

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "template/empty_configuration.yaml",
    )
    with patch.object(config, "YAML_CONFIG_FILE", yaml_path):
        await opp.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await opp.async_block_till_done()

    assert len(opp.states.async_all()) == 1


async def test_reloadable_stops_on_invalid_config(opp):
    """Test we stop the reload if configuration.yaml is completely broken."""
    opp.states.async_set("sensor.test_sensor", "mytest")

    await async_setup_component(
        opp,
        "sensor",
        {
            "sensor": {
                "platform": DOMAIN,
                "sensors": {
                    "state": {
                        "value_template": "{{ states.sensor.test_sensor.state }}"
                    },
                },
            }
        },
    )

    await opp.async_block_till_done()

    await opp.async_start()
    await opp.async_block_till_done()

    assert opp.states.get("sensor.state").state == "mytest"
    assert len(opp.states.async_all()) == 2

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "template/configuration.yaml.corrupt",
    )
    with patch.object(config, "YAML_CONFIG_FILE", yaml_path):
        await opp.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await opp.async_block_till_done()

    assert opp.states.get("sensor.state").state == "mytest"
    assert len(opp.states.async_all()) == 2


async def test_reloadable_handles_partial_valid_config(opp):
    """Test we can still setup valid sensors when configuration.yaml has a broken entry."""
    opp.states.async_set("sensor.test_sensor", "mytest")

    await async_setup_component(
        opp,
        "sensor",
        {
            "sensor": {
                "platform": DOMAIN,
                "sensors": {
                    "state": {
                        "value_template": "{{ states.sensor.test_sensor.state }}"
                    },
                },
            }
        },
    )

    await opp.async_block_till_done()

    await opp.async_start()
    await opp.async_block_till_done()

    assert opp.states.get("sensor.state").state == "mytest"
    assert len(opp.states.async_all()) == 2

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "template/broken_configuration.yaml",
    )
    with patch.object(config, "YAML_CONFIG_FILE", yaml_path):
        await opp.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await opp.async_block_till_done()

    assert len(opp.states.async_all()) == 3

    assert opp.states.get("sensor.state") is None
    assert opp.states.get("sensor.watching_tv_in_master_bedroom").state == "off"
    assert float(opp.states.get("sensor.combined_sensor_energy_usage").state) == 0


async def test_reloadable_multiple_platforms(opp):
    """Test that we can reload."""
    opp.states.async_set("sensor.test_sensor", "mytest")

    await async_setup_component(
        opp,
        "sensor",
        {
            "sensor": {
                "platform": DOMAIN,
                "sensors": {
                    "state": {
                        "value_template": "{{ states.sensor.test_sensor.state }}"
                    },
                },
            }
        },
    )
    await async_setup_component(
        opp,
        "binary_sensor",
        {
            "binary_sensor": {
                "platform": DOMAIN,
                "sensors": {
                    "state": {
                        "value_template": "{{ states.sensor.test_sensor.state }}"
                    },
                },
            }
        },
    )
    await opp.async_block_till_done()

    await opp.async_start()
    await opp.async_block_till_done()

    assert opp.states.get("sensor.state").state == "mytest"
    assert opp.states.get("binary_sensor.state").state == "off"

    assert len(opp.states.async_all()) == 3

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "template/sensor_configuration.yaml",
    )
    with patch.object(config, "YAML_CONFIG_FILE", yaml_path):
        await opp.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await opp.async_block_till_done()

    assert len(opp.states.async_all()) == 3

    assert opp.states.get("sensor.state") is None
    assert opp.states.get("sensor.watching_tv_in_master_bedroom").state == "off"
    assert float(opp.states.get("sensor.combined_sensor_energy_usage").state) == 0


async def test_reload_sensors_that_reference_other_template_sensors(opp):
    """Test that we can reload sensor that reference other template sensors."""

    await async_setup_component(
        opp,
        "sensor",
        {
            "sensor": {
                "platform": DOMAIN,
                "sensors": {
                    "state": {"value_template": "{{ 1 }}"},
                },
            }
        },
    )
    await opp.async_block_till_done()
    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "template/ref_configuration.yaml",
    )
    with patch.object(config, "YAML_CONFIG_FILE", yaml_path):
        await opp.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await opp.async_block_till_done()

    assert len(opp.states.async_all()) == 3
    await opp.async_block_till_done()

    next_time = dt_util.utcnow() + timedelta(seconds=1.2)
    with patch(
        "openpeerpower.helpers.ratelimit.dt_util.utcnow", return_value=next_time
    ):
        async_fire_time_changed(opp, next_time)
        await opp.async_block_till_done()

    assert opp.states.get("sensor.test1").state == "3"
    assert opp.states.get("sensor.test2").state == "1"
    assert opp.states.get("sensor.test3").state == "2"


def _get_fixtures_base_path():
    return path.dirname(path.dirname(path.dirname(__file__)))
