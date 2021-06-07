"""Test init of GIOS integration."""
import json
from unittest.mock import patch

from openpeerpower.components.gios.const import DOMAIN
from openpeerpower.config_entries import ConfigEntryState
from openpeerpower.const import STATE_UNAVAILABLE

from . import STATIONS

from tests.common import MockConfigEntry, load_fixture, mock_device_registry
from tests.components.gios import init_integration


async def test_async_setup_entry(opp):
    """Test a successful setup entry."""
    await init_integration(opp)

    state = opp.states.get("air_quality.home")
    assert state is not None
    assert state.state != STATE_UNAVAILABLE
    assert state.state == "4"


async def test_config_not_ready(opp):
    """Test for setup failure if connection to GIOS is missing."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Home",
        unique_id=123,
        data={"station_id": 123, "name": "Home"},
    )

    with patch(
        "openpeerpower.components.gios.Gios._get_stations",
        side_effect=ConnectionError(),
    ):
        entry.add_to_opp(opp)
        await opp.config_entries.async_setup(entry.entry_id)
        assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload_entry(opp):
    """Test successful unload of entry."""
    entry = await init_integration(opp)

    assert len(opp.config_entries.async_entries(DOMAIN)) == 1
    assert entry.state is ConfigEntryState.LOADED

    assert await opp.config_entries.async_unload(entry.entry_id)
    await opp.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED
    assert not opp.data.get(DOMAIN)


async def test_migrate_device_and_config_entry(opp):
    """Test device_info identifiers and config entry migration."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Home",
        unique_id=123,
        data={
            "station_id": 123,
            "name": "Home",
        },
    )

    indexes = json.loads(load_fixture("gios/indexes.json"))
    station = json.loads(load_fixture("gios/station.json"))
    sensors = json.loads(load_fixture("gios/sensors.json"))

    with patch(
        "openpeerpower.components.gios.Gios._get_stations", return_value=STATIONS
    ), patch(
        "openpeerpower.components.gios.Gios._get_station",
        return_value=station,
    ), patch(
        "openpeerpower.components.gios.Gios._get_all_sensors",
        return_value=sensors,
    ), patch(
        "openpeerpower.components.gios.Gios._get_indexes", return_value=indexes
    ):
        config_entry.add_to_opp(opp)

        device_reg = mock_device_registry(opp)
        device_entry = device_reg.async_get_or_create(
            config_entry_id=config_entry.entry_id, identifiers={(DOMAIN, 123)}
        )

        await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()

        migrated_device_entry = device_reg.async_get_or_create(
            config_entry_id=config_entry.entry_id, identifiers={(DOMAIN, "123")}
        )
        assert device_entry.id == migrated_device_entry.id
