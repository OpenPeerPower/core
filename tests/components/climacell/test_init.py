"""Tests for Climacell init."""
import logging

import pytest

from openpeerpower.components.climacell.config_flow import (
    _get_config_schema,
    _get_unique_id,
)
from openpeerpower.components.climacell.const import CONF_TIMESTEP, DOMAIN
from openpeerpower.components.weather import DOMAIN as WEATHER_DOMAIN
from openpeerpower.const import CONF_API_VERSION
from openpeerpower.core import OpenPeerPower

from .const import API_V3_ENTRY_DATA, MIN_CONFIG, V1_ENTRY_DATA

from tests.common import MockConfigEntry

_LOGGER = logging.getLogger(__name__)


async def test_load_and_unload(
    opp: OpenPeerPower,
    climacell_config_entry_update: pytest.fixture,
) -> None:
    """Test loading and unloading entry."""
    data = _get_config_schema(opp)(MIN_CONFIG)
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=data,
        unique_id=_get_unique_id(opp, data),
        version=1,
    )
    config_entry.add_to_opp(opp)
    assert await opp.config_entries.async_setup(config_entry.entry_id)
    await opp.async_block_till_done()
    assert len(opp.states.async_entity_ids(WEATHER_DOMAIN)) == 1

    assert await opp.config_entries.async_remove(config_entry.entry_id)
    await opp.async_block_till_done()
    assert len(opp.states.async_entity_ids(WEATHER_DOMAIN)) == 0


async def test_v3_load_and_unload(
    opp: OpenPeerPower,
    climacell_config_entry_update: pytest.fixture,
) -> None:
    """Test loading and unloading v3 entry."""
    data = _get_config_schema(opp)(API_V3_ENTRY_DATA)
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=data,
        unique_id=_get_unique_id(opp, data),
        version=1,
    )
    config_entry.add_to_opp(opp)
    assert await opp.config_entries.async_setup(config_entry.entry_id)
    await opp.async_block_till_done()
    assert len(opp.states.async_entity_ids(WEATHER_DOMAIN)) == 1

    assert await opp.config_entries.async_remove(config_entry.entry_id)
    await opp.async_block_till_done()
    assert len(opp.states.async_entity_ids(WEATHER_DOMAIN)) == 0


@pytest.mark.parametrize(
    "old_timestep, new_timestep", [(2, 1), (7, 5), (20, 15), (21, 30)]
)
async def test_migrate_timestep(
    opp: OpenPeerPower,
    climacell_config_entry_update: pytest.fixture,
    old_timestep: int,
    new_timestep: int,
) -> None:
    """Test migration to standardized timestep."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=V1_ENTRY_DATA,
        options={CONF_TIMESTEP: old_timestep},
        unique_id=_get_unique_id(opp, V1_ENTRY_DATA),
        version=1,
    )
    config_entry.add_to_opp(opp)
    assert await opp.config_entries.async_setup(config_entry.entry_id)
    await opp.async_block_till_done()
    assert config_entry.version == 1
    assert (
        CONF_API_VERSION in config_entry.data
        and config_entry.data[CONF_API_VERSION] == 3
    )
    assert config_entry.options[CONF_TIMESTEP] == new_timestep
