"""The tests for the Switch component."""
import pytest

from openpeerpower import core
from openpeerpower.components import switch
from openpeerpower.const import CONF_PLATFORM
from openpeerpower.setup import async_setup_component

from tests.components.switch import common


@pytest.fixture(autouse=True)
def entities(opp):
    """Initialize the test switch."""
    platform = getattr(opp.components, "test.switch")
    platform.init()
    yield platform.ENTITIES


async def test_methods(opp, entities):
    """Test is_on, turn_on, turn_off methods."""
    switch_1, switch_2, switch_3 = entities
    assert await async_setup_component(
        opp, switch.DOMAIN, {switch.DOMAIN: {CONF_PLATFORM: "test"}}
    )
    await opp.async_block_till_done()
    assert switch.is_on(opp, switch_1.entity_id)
    assert not switch.is_on(opp, switch_2.entity_id)
    assert not switch.is_on(opp, switch_3.entity_id)

    await common.async_turn_off(opp, switch_1.entity_id)
    await common.async_turn_on(opp, switch_2.entity_id)

    assert not switch.is_on(opp, switch_1.entity_id)
    assert switch.is_on(opp, switch_2.entity_id)

    # Turn all off
    await common.async_turn_off(opp)

    assert not switch.is_on(opp, switch_1.entity_id)
    assert not switch.is_on(opp, switch_2.entity_id)
    assert not switch.is_on(opp, switch_3.entity_id)

    # Turn all on
    await common.async_turn_on(opp)

    assert switch.is_on(opp, switch_1.entity_id)
    assert switch.is_on(opp, switch_2.entity_id)
    assert switch.is_on(opp, switch_3.entity_id)


async def test_switch_context(opp, entities, opp_admin_user):
    """Test that switch context works."""
    assert await async_setup_component(opp, "switch", {"switch": {"platform": "test"}})

    await opp.async_block_till_done()

    state = opp.states.get("switch.ac")
    assert state is not None

    await opp.services.async_call(
        "switch",
        "toggle",
        {"entity_id": state.entity_id},
        True,
        core.Context(user_id=opp_admin_user.id),
    )

    state2 = opp.states.get("switch.ac")
    assert state2 is not None
    assert state.state != state2.state
    assert state2.context.user_id == opp_admin_user.id


def test_deprecated_base_class(caplog):
    """Test deprecated base class."""

    class CustomSwitch(switch.SwitchDevice):
        pass

    CustomSwitch()
    assert "SwitchDevice is deprecated, modify CustomSwitch" in caplog.text
