"""The tests for the Homematic notification platform."""

import openpeerpower.components.notify as notify_comp
from openpeerpower.setup import async_setup_component

from tests.common import assert_setup_component


async def test_setup_full(opp):
    """Test valid configuration."""
    await async_setup_component(
        opp,
        "homematic",
        {"homematic": {"hosts": {"ccu2": {"host": "127.0.0.1"}}}},
    )
    with assert_setup_component(1) as handle_config:
        assert await async_setup_component(
            opp,
            "notify",
            {
                "notify": {
                    "name": "test",
                    "platform": "homematic",
                    "address": "NEQXXXXXXX",
                    "channel": 2,
                    "param": "SUBMIT",
                    "value": "1,1,108000,2",
                    "interface": "my-interface",
                }
            },
        )
    assert handle_config[notify_comp.DOMAIN]


async def test_setup_without_optional(opp):
    """Test valid configuration without optional."""
    await async_setup_component(
        opp,
        "homematic",
        {"homematic": {"hosts": {"ccu2": {"host": "127.0.0.1"}}}},
    )
    with assert_setup_component(1) as handle_config:
        assert await async_setup_component(
            opp,
            "notify",
            {
                "notify": {
                    "name": "test",
                    "platform": "homematic",
                    "address": "NEQXXXXXXX",
                    "channel": 2,
                    "param": "SUBMIT",
                    "value": "1,1,108000,2",
                }
            },
        )
    assert handle_config[notify_comp.DOMAIN]


async def test_bad_config(opp):
    """Test invalid configuration."""
    config = {notify_comp.DOMAIN: {"name": "test", "platform": "homematic"}}
    with assert_setup_component(0) as handle_config:
        assert await async_setup_component(opp, notify_comp.DOMAIN, config)
    assert not handle_config[notify_comp.DOMAIN]
