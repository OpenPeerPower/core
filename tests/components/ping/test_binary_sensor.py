"""The test for the ping binary_sensor platform."""
from os import path
from unittest.mock import patch

from openpeerpower import config as.opp_config, setup
from openpeerpower.components.ping import DOMAIN
from openpeerpower.const import SERVICE_RELOAD


async def test_reload.opp):
    """Verify we can reload trend sensors."""

    await setup.async_setup_component(
        opp,
        "binary_sensor",
        {
            "binary_sensor": {
                "platform": "ping",
                "name": "test",
                "host": "127.0.0.1",
                "count": 1,
            }
        },
    )
    await opp.async_block_till_done()

    assert len.opp.states.async_all()) == 1

    assert opp.states.get("binary_sensor.test")

    yaml_path = path.join(
        _get_fixtures_base_path(),
        "fixtures",
        "ping/configuration.yaml",
    )
    with patch.object.opp_config, "YAML_CONFIG_FILE", yaml_path):
        await opp.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await opp.async_block_till_done()

    assert len.opp.states.async_all()) == 1

    assert opp.states.get("binary_sensor.test") is None
    assert opp.states.get("binary_sensor.test2")


def _get_fixtures_base_path():
    return path.dirname(path.dirname(path.dirname(__file__)))
