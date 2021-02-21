"""Test the Yeelight binary sensor."""
from unittest.mock import patch

from openpeerpower.components.yeelight import DOMAIN
from openpeerpowerr.core import OpenPeerPower
from openpeerpowerr.helpers import entity_component
from openpeerpowerr.setup import async_setup_component

from . import MODULE, NAME, PROPERTIES, YAML_CONFIGURATION, _mocked_bulb

ENTITY_BINARY_SENSOR = f"binary_sensor.{NAME}_nightlight"


async def test_nightlight.opp: OpenPeerPower):
    """Test nightlight sensor."""
    mocked_bulb = _mocked_bulb()
    with patch(f"{MODULE}.Bulb", return_value=mocked_bulb), patch(
        f"{MODULE}.config_flow.yeelight.Bulb", return_value=mocked_bulb
    ):
        await async_setup_component.opp, DOMAIN, YAML_CONFIGURATION)
        await opp..async_block_till_done()

    # active_mode
    assert.opp.states.get(ENTITY_BINARY_SENSOR).state == "off"

    # nl_br
    properties = {**PROPERTIES}
    properties.pop("active_mode")
    mocked_bulb.last_properties = properties
    await entity_component.async_update_entity.opp, ENTITY_BINARY_SENSOR)
    assert.opp.states.get(ENTITY_BINARY_SENSOR).state == "on"

    # default
    properties.pop("nl_br")
    await entity_component.async_update_entity.opp, ENTITY_BINARY_SENSOR)
    assert.opp.states.get(ENTITY_BINARY_SENSOR).state == "off"
