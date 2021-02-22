"""Test significant change helper."""
import pytest

from openpeerpower.components.sensor import DEVICE_CLASS_BATTERY
from openpeerpower.const import ATTR_DEVICE_CLASS, STATE_UNAVAILABLE, STATE_UNKNOWN
from openpeerpower.core import State
from openpeerpower.helpers import significant_change


@pytest.fixture(name="checker")
async def checker_fixture.opp):
    """Checker fixture."""
    checker = await significant_change.create_checker.opp, "test")

    def async_check_significant_change(
        .opp, old_state, _old_attrs, new_state, _new_attrs, **kwargs
    ):
        return abs(float(old_state) - float(new_state)) > 4

   .opp.data[significant_change.DATA_FUNCTIONS][
        "test_domain"
    ] = async_check_significant_change
    return checker


async def test_signicant_change.opp, checker):
    """Test initialize helper works."""
    ent_id = "test_domain.test_entity"
    attrs = {ATTR_DEVICE_CLASS: DEVICE_CLASS_BATTERY}

    assert checker.async_is_significant_change(State(ent_id, "100", attrs))

    # Same state is not significant.
    assert not checker.async_is_significant_change(State(ent_id, "100", attrs))

    # State under 5 difference is not significant. (per test mock)
    assert not checker.async_is_significant_change(State(ent_id, "96", attrs))

    # Make sure we always compare against last significant change
    assert checker.async_is_significant_change(State(ent_id, "95", attrs))

    # State turned unknown
    assert checker.async_is_significant_change(State(ent_id, STATE_UNKNOWN, attrs))

    # State turned unavailable
    assert checker.async_is_significant_change(State(ent_id, "100", attrs))
    assert checker.async_is_significant_change(State(ent_id, STATE_UNAVAILABLE, attrs))


async def test_significant_change_extra.opp, checker):
    """Test extra significant checker works."""
    ent_id = "test_domain.test_entity"
    attrs = {ATTR_DEVICE_CLASS: DEVICE_CLASS_BATTERY}

    assert checker.async_is_significant_change(State(ent_id, "100", attrs), extra_arg=1)
    assert checker.async_is_significant_change(State(ent_id, "200", attrs), extra_arg=1)

    # Reset the last significiant change to 100 to repeat test but with
    # extra checker installed.
    assert checker.async_is_significant_change(State(ent_id, "100", attrs), extra_arg=1)

    def extra_significant_check(
       .opp, old_state, old_attrs, old_extra_arg, new_state, new_attrs, new_extra_arg
    ):
        return old_extra_arg != new_extra_arg

    checker.extra_significant_check = extra_significant_check

    # This is normally a significant change (100 -> 200), but the extra arg check marks it
    # as insignificant.
    assert not checker.async_is_significant_change(
        State(ent_id, "200", attrs), extra_arg=1
    )
    assert checker.async_is_significant_change(State(ent_id, "200", attrs), extra_arg=2)
