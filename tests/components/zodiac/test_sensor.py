"""The test for the zodiac sensor platform."""
from datetime import datetime
from unittest.mock import patch

import pytest

from openpeerpower.components.zodiac.const import (
    ATTR_ELEMENT,
    ATTR_MODALITY,
    DOMAIN,
    ELEMENT_EARTH,
    ELEMENT_FIRE,
    ELEMENT_WATER,
    MODALITY_CARDINAL,
    MODALITY_FIXED,
    SIGN_ARIES,
    SIGN_SCORPIO,
    SIGN_TAURUS,
)
from openpeerpower.setup import async_setup_component
import openpeerpower.util.dt as dt_util

DAY1 = datetime(2020, 11, 15, tzinfo=dt_util.UTC)
DAY2 = datetime(2020, 4, 20, tzinfo=dt_util.UTC)
DAY3 = datetime(2020, 4, 21, tzinfo=dt_util.UTC)


@pytest.mark.parametrize(
    "now,sign,element,modality",
    [
        (DAY1, SIGN_SCORPIO, ELEMENT_WATER, MODALITY_FIXED),
        (DAY2, SIGN_ARIES, ELEMENT_FIRE, MODALITY_CARDINAL),
        (DAY3, SIGN_TAURUS, ELEMENT_EARTH, MODALITY_FIXED),
    ],
)
async def test_zodiac_day.opp, now, sign, element, modality):
    """Test the zodiac sensor."""
    config = {DOMAIN: {}}

    with patch("openpeerpower.components.zodiac.sensor.utcnow", return_value=now):
        assert await async_setup_component.opp, DOMAIN, config)
        await.opp.async_block_till_done()

    state = opp.states.get("sensor.zodiac")
    assert state
    assert state.state == sign
    assert state.attributes
    assert state.attributes[ATTR_ELEMENT] == element
    assert state.attributes[ATTR_MODALITY] == modality
