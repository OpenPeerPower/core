"""The tests for the Met Office sensor component."""
import json
from unittest.mock import patch

from openpeerpower.components.metoffice.const import ATTRIBUTION, DOMAIN

from . import NewDateTime
from .const import (
    DATETIME_FORMAT,
    KINGSLYNN_SENSOR_RESULTS,
    METOFFICE_CONFIG_KINGSLYNN,
    METOFFICE_CONFIG_WAVERTREE,
    TEST_DATETIME_STRING,
    TEST_SITE_NAME_KINGSLYNN,
    TEST_SITE_NAME_WAVERTREE,
    WAVERTREE_SENSOR_RESULTS,
)

from tests.common import MockConfigEntry, load_fixture


@patch(
    "datapoint.Forecast.datetime.datetime",
    NewDateTime,
)
async def test_one_sensor_site_running.opp, requests_mock, legacy_patchable_time):
    """Test the Met Office sensor platform."""
    # all metoffice test data encapsulated in here
    mock_json = json.loads(load_fixture("metoffice.json"))
    all_sites = json.dumps(mock_json["all_sites"])
    wavertree_hourly = json.dumps(mock_json["wavertree_hourly"])

    requests_mock.get("/public/data/val/wxfcs/all/json/sitelist/", text=all_sites)
    requests_mock.get(
        "/public/data/val/wxfcs/all/json/354107?res=3hourly",
        text=wavertree_hourly,
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=METOFFICE_CONFIG_WAVERTREE,
    )
    entry.add_to_opp.opp)
    await.opp.config_entries.async_setup(entry.entry_id)
    await.opp.async_block_till_done()

    running_sensor_ids = opp.states.async_entity_ids("sensor")
    assert len(running_sensor_ids) > 0
    for running_id in running_sensor_ids:
        sensor = opp.states.get(running_id)
        sensor_id = sensor.attributes.get("sensor_id")
        sensor_name, sensor_value = WAVERTREE_SENSOR_RESULTS[sensor_id]

        assert sensor.state == sensor_value
        assert (
            sensor.attributes.get("last_update").strftime(DATETIME_FORMAT)
            == TEST_DATETIME_STRING
        )
        assert sensor.attributes.get("site_id") == "354107"
        assert sensor.attributes.get("site_name") == TEST_SITE_NAME_WAVERTREE
        assert sensor.attributes.get("attribution") == ATTRIBUTION


@patch(
    "datapoint.Forecast.datetime.datetime",
    NewDateTime,
)
async def test_two_sensor_sites_running.opp, requests_mock, legacy_patchable_time):
    """Test we handle two sets of sensors running for two different sites."""

    # all metoffice test data encapsulated in here
    mock_json = json.loads(load_fixture("metoffice.json"))
    all_sites = json.dumps(mock_json["all_sites"])
    wavertree_hourly = json.dumps(mock_json["wavertree_hourly"])
    kingslynn_hourly = json.dumps(mock_json["kingslynn_hourly"])

    requests_mock.get("/public/data/val/wxfcs/all/json/sitelist/", text=all_sites)
    requests_mock.get(
        "/public/data/val/wxfcs/all/json/354107?res=3hourly", text=wavertree_hourly
    )
    requests_mock.get(
        "/public/data/val/wxfcs/all/json/322380?res=3hourly", text=kingslynn_hourly
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=METOFFICE_CONFIG_WAVERTREE,
    )
    entry.add_to_opp.opp)
    await.opp.config_entries.async_setup(entry.entry_id)
    entry2 = MockConfigEntry(
        domain=DOMAIN,
        data=METOFFICE_CONFIG_KINGSLYNN,
    )
    entry2.add_to_opp.opp)
    await.opp.config_entries.async_setup(entry2.entry_id)
    await.opp.async_block_till_done()

    running_sensor_ids = opp.states.async_entity_ids("sensor")
    assert len(running_sensor_ids) > 0
    for running_id in running_sensor_ids:
        sensor = opp.states.get(running_id)
        sensor_id = sensor.attributes.get("sensor_id")
        if sensor.attributes.get("site_id") == "354107":
            sensor_name, sensor_value = WAVERTREE_SENSOR_RESULTS[sensor_id]
            assert sensor.state == sensor_value
            assert (
                sensor.attributes.get("last_update").strftime(DATETIME_FORMAT)
                == TEST_DATETIME_STRING
            )
            assert sensor.attributes.get("sensor_id") == sensor_id
            assert sensor.attributes.get("site_id") == "354107"
            assert sensor.attributes.get("site_name") == TEST_SITE_NAME_WAVERTREE
            assert sensor.attributes.get("attribution") == ATTRIBUTION

        else:
            sensor_name, sensor_value = KINGSLYNN_SENSOR_RESULTS[sensor_id]
            assert sensor.state == sensor_value
            assert (
                sensor.attributes.get("last_update").strftime(DATETIME_FORMAT)
                == TEST_DATETIME_STRING
            )
            assert sensor.attributes.get("sensor_id") == sensor_id
            assert sensor.attributes.get("site_id") == "322380"
            assert sensor.attributes.get("site_name") == TEST_SITE_NAME_KINGSLYNN
            assert sensor.attributes.get("attribution") == ATTRIBUTION
