"""The test for the sql sensor platform."""
import pytest
import voluptuous as vol

from openpeerpower.components.sql.sensor import validate_sql_select
from openpeerpower.const import STATE_UNKNOWN
from openpeerpower.setup import async_setup_component


async def test_query(opp):
    """Test the SQL sensor."""
    config = {
        "sensor": {
            "platform": "sql",
            "db_url": "sqlite://",
            "queries": [
                {
                    "name": "count_tables",
                    "query": "SELECT 5 as value",
                    "column": "value",
                }
            ],
        }
    }

    assert await async_setup_component(opp, "sensor", config)
    await opp.async_block_till_done()

    state = opp.states.get("sensor.count_tables")
    assert state.state == "5"
    assert state.attributes["value"] == 5


async def test_invalid_query(opp):
    """Test the SQL sensor for invalid queries."""
    with pytest.raises(vol.Invalid):
        validate_sql_select("DROP TABLE *")

    config = {
        "sensor": {
            "platform": "sql",
            "db_url": "sqlite://",
            "queries": [
                {
                    "name": "count_tables",
                    "query": "SELECT * value FROM sqlite_master;",
                    "column": "value",
                }
            ],
        }
    }

    assert await async_setup_component(opp, "sensor", config)
    await opp.async_block_till_done()

    state = opp.states.get("sensor.count_tables")
    assert state.state == STATE_UNKNOWN


@pytest.mark.parametrize(
    "url,expected_patterns,not_expected_patterns",
    [
        (
            "sqlite://openpeerpower:hunter2@openpeerpower.local",
            ["sqlite://****:****@openpeerpower.local"],
            ["sqlite://openpeerpower:hunter2@openpeerpower.local"],
        ),
        (
            "sqlite://openpeerpower.local",
            ["sqlite://openpeerpower.local"],
            [],
        ),
    ],
)
async def test_invalid_url(opp, caplog, url, expected_patterns, not_expected_patterns):
    """Test credentials in url is not logged."""
    config = {
        "sensor": {
            "platform": "sql",
            "db_url": url,
            "queries": [
                {
                    "name": "count_tables",
                    "query": "SELECT 5 as value",
                    "column": "value",
                }
            ],
        }
    }

    assert await async_setup_component(opp, "sensor", config)
    await opp.async_block_till_done()

    for pattern in not_expected_patterns:
        assert pattern not in caplog.text
    for pattern in expected_patterns:
        assert pattern in caplog.text
