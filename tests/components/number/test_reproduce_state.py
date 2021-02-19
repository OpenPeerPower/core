"""Test reproduce state for Number entities."""
from openpeerpower.components.number.const import (
    ATTR_MAX,
    ATTR_MIN,
    DOMAIN,
    SERVICE_SET_VALUE,
)
from openpeerpowerr.core import State

from tests.common import async_mock_service

VALID_NUMBER1 = "19.0"
VALID_NUMBER2 = "99.9"


async def test_reproducing_states.opp, caplog):
    """Test reproducing Number states."""

   .opp.states.async_set(
        "number.test_number", VALID_NUMBER1, {ATTR_MIN: 5, ATTR_MAX: 100}
    )

    # These calls should do nothing as entities already in desired state
    await.opp.helpers.state.async_reproduce_state(
        [
            State("number.test_number", VALID_NUMBER1),
            # Should not raise
            State("number.non_existing", "234"),
        ],
    )

    assert.opp.states.get("number.test_number").state == VALID_NUMBER1

    # Test reproducing with different state
    calls = async_mock_service.opp, DOMAIN, SERVICE_SET_VALUE)
    await.opp.helpers.state.async_reproduce_state(
        [
            State("number.test_number", VALID_NUMBER2),
            # Should not raise
            State("number.non_existing", "234"),
        ],
    )

    assert len(calls) == 1
    assert calls[0].domain == DOMAIN
    assert calls[0].data == {"entity_id": "number.test_number", "value": VALID_NUMBER2}

    # Test invalid state
    await.opp.helpers.state.async_reproduce_state(
        [State("number.test_number", "invalid_state")]
    )

    assert len(calls) == 1
