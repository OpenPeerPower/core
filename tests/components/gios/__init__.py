"""Tests for GIOS."""
import json
from unittest.mock import patch

from openpeerpower.components.gios.const import DOMAIN

from tests.common import MockConfigEntry, load_fixture

STATIONS = [
    {"id": 123, "stationName": "Test Name 1", "gegrLat": "99.99", "gegrLon": "88.88"},
    {"id": 321, "stationName": "Test Name 2", "gegrLat": "77.77", "gegrLon": "66.66"},
]


async def init_integration(opp, incomplete_data=False) -> MockConfigEntry:
    """Set up the GIOS integration in Open Peer Power."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Home",
        unique_id="123",
        data={"station_id": 123, "name": "Home"},
    )

    indexes = json.loads(load_fixture("gios/indexes.json"))
    station = json.loads(load_fixture("gios/station.json"))
    sensors = json.loads(load_fixture("gios/sensors.json"))
    if incomplete_data:
        indexes["stIndexLevel"]["indexLevelName"] = "foo"
        sensors["pm10"]["values"][0]["value"] = None
        sensors["pm10"]["values"][1]["value"] = None

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
        entry.add_to_opp(opp)
        await opp.config_entries.async_setup(entry.entry_id)
        await opp.async_block_till_done()

    return entry
