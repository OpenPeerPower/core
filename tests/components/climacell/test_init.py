"""Tests for Climacell init."""
import logging

import pytest

from openpeerpower.components.climacell.config_flow import (
    _get_config_schema,
    _get_unique_id,
)
from openpeerpower.components.climacell.const import DOMAIN
from openpeerpower.components.weather import DOMAIN as WEATHER_DOMAIN
from openpeerpower.helpers.typing import OpenPeerPowerType

from .const import MIN_CONFIG

from tests.common import MockConfigEntry

_LOGGER = logging.getLogger(__name__)


async def test_load_and_unload(
    opp: OpenPeerPowerType,
    climacell_config_entry_update: pytest.fixture,
) -> None:
    """Test loading and unloading entry."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=_get_config_schema(opp)(MIN_CONFIG),
        unique_id=_get_unique_id(opp, _get_config_schema(opp)(MIN_CONFIG)),
    )
    config_entry.add_to_opp(opp)
    assert await opp.config_entries.async_setup(config_entry.entry_id)
    await opp.async_block_till_done()
    assert len(opp.states.async_entity_ids(WEATHER_DOMAIN)) == 1

    assert await opp.config_entries.async_remove(config_entry.entry_id)
    await opp.async_block_till_done()
    assert len(opp.states.async_entity_ids(WEATHER_DOMAIN)) == 0
