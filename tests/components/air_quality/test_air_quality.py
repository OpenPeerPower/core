"""The tests for the Air Quality component."""
from openpeerpower.components.air_quality import (
    ATTR_ATTRIBUTION,
    ATTR_N2O,
    ATTR_OZONE,
    ATTR_PM_10,
)
from openpeerpower.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
)
from openpeerpower.setup import async_setup_component


async def test_state.opp):
    """Test Air Quality state."""
    config = {"air_quality": {"platform": "demo"}}

    assert await async_setup_component.opp, "air_quality", config)
    await opp.async_block_till_done()

    state = opp.states.get("air_quality.demo_air_quality_home")
    assert state is not None

    assert state.state == "14"


async def test_attributes.opp):
    """Test Air Quality attributes."""
    config = {"air_quality": {"platform": "demo"}}

    assert await async_setup_component.opp, "air_quality", config)
    await opp.async_block_till_done()

    state = opp.states.get("air_quality.demo_air_quality_office")
    assert state is not None

    data = state.attributes
    assert data.get(ATTR_PM_10) == 16
    assert data.get(ATTR_N2O) is None
    assert data.get(ATTR_OZONE) is None
    assert data.get(ATTR_ATTRIBUTION) == "Powered by Open Peer Power"
    assert (
        data.get(ATTR_UNIT_OF_MEASUREMENT) == CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
    )
