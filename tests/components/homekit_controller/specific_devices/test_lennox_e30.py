"""
Regression tests for Aqara Gateway V3.

https://github.com/openpeerpower/core/issues/20885
"""

from openpeerpower.components.climate.const import (
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_TARGET_TEMPERATURE_RANGE,
)
from openpeerpower.helpers import device_registry as dr, entity_registry as er

from tests.components.homekit_controller.common import (
    Helper,
    setup_accessories_from_file,
    setup_test_accessories,
)


async def test_lennox_e30_setup(opp):
    """Test that a Lennox E30 can be correctly setup in HA."""
    accessories = await setup_accessories_from_file(opp, "lennox_e30.json")
    config_entry, pairing = await setup_test_accessories(opp, accessories)

    entity_registry = er.async_get(opp)

    climate = entity_registry.async_get("climate.lennox")
    assert climate.unique_id == "homekit-XXXXXXXX-100"

    climate_helper = Helper(
        opp, "climate.lennox", pairing, accessories[0], config_entry
    )
    climate_state = await climate_helper.poll_and_get_state()
    assert climate_state.attributes["friendly_name"] == "Lennox"
    assert climate_state.attributes["supported_features"] == (
        SUPPORT_TARGET_TEMPERATURE | SUPPORT_TARGET_TEMPERATURE_RANGE
    )

    device_registry = dr.async_get(opp)

    device = device_registry.async_get(climate.device_id)
    assert device.manufacturer == "Lennox"
    assert device.name == "Lennox"
    assert device.model == "E30 2B"
    assert device.sw_version == "3.40.XX"

    # The fixture contains a single accessory - so its a single device
    # and no bridge
    assert device.via_device_id is None
