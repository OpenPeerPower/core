"""The tests for the InfluxDB sensor."""
from dataclasses import dataclass
from datetime import timedelta
from typing import Dict, List, Type
from unittest.mock import MagicMock, patch

from influxdb.exceptions import InfluxDBClientError, InfluxDBServerError
from influxdb_client.rest import ApiException
import pytest
from voluptuous import Invalid

from openpeerpower.components.influxdb.const import (
    API_VERSION_2,
    DEFAULT_API_VERSION,
    DEFAULT_BUCKET,
    DEFAULT_DATABASE,
    DOMAIN,
    TEST_QUERY_V1,
    TEST_QUERY_V2,
)
from openpeerpower.components.influxdb.sensor import PLATFORM_SCHEMA
import openpeerpower.components.sensor as sensor
from openpeerpower.const import STATE_UNKNOWN
from openpeerpowerr.helpers.entity_platform import PLATFORM_NOT_READY_BASE_WAIT_TIME
from openpeerpowerr.setup import async_setup_component
from openpeerpowerr.util import dt as dt_util

from tests.common import async_fire_time_changed

INFLUXDB_PATH = "openpeerpower.components.influxdb"
INFLUXDB_CLIENT_PATH = f"{INFLUXDB_PATH}.InfluxDBClient"
INFLUXDB_SENSOR_PATH = f"{INFLUXDB_PATH}.sensor"

BASE_V1_CONFIG = {}
BASE_V2_CONFIG = {
    "api_version": API_VERSION_2,
    "organization": "org",
    "token": "token",
}

BASE_V1_QUERY = {
    "queries": [
        {
            "name": "test",
            "measurement": "measurement",
            "where": "where",
            "field": "field",
        }
    ],
}
BASE_V2_QUERY = {"queries_flux": [{"name": "test", "query": "query"}]}


@dataclass
class Record:
    """Record in a Table."""

    values: Dict


@dataclass
class Table:
    """Table in an Influx 2 resultset."""

    records: List[Type[Record]]


@pytest.fixture(name="mock_client")
def mock_client_fixture(request):
    """Patch the InfluxDBClient object with mock for version under test."""
    if request.param == API_VERSION_2:
        client_target = f"{INFLUXDB_CLIENT_PATH}V2"
    else:
        client_target = INFLUXDB_CLIENT_PATH

    with patch(client_target) as client:
        yield client


@pytest.fixture(autouse=True, scope="module")
def mock_client_close():
    """Mock close method of clients at module scope."""
    with patch(f"{INFLUXDB_CLIENT_PATH}.close") as close_v1, patch(
        f"{INFLUXDB_CLIENT_PATH}V2.close"
    ) as close_v2:
        yield (close_v1, close_v2)


def _make_v1_resultset(*args):
    """Create a mock V1 resultset."""
    for arg in args:
        yield {"value": arg}


def _make_v1_databases_resultset():
    """Create a mock V1 'show databases' resultset."""
    for name in [DEFAULT_DATABASE, "db2"]:
        yield {"name": name}


def _make_v2_resultset(*args):
    """Create a mock V2 resultset."""
    tables = []

    for arg in args:
        values = {"_value": arg}
        record = Record(values)
        tables.append(Table([record]))

    return tables


def _make_v2_buckets_resultset():
    """Create a mock V2 'buckets()' resultset."""
    records = []
    for name in [DEFAULT_BUCKET, "bucket2"]:
        records.append(Record({"name": name}))

    return [Table(records)]


def _set_query_mock_v1(
    mock_influx_client, return_value=None, query_exception=None, side_effect=None
):
    """Set return value or side effect for the V1 client."""
    query_api = mock_influx_client.return_value.query
    if side_effect:
        query_api.side_effect = side_effect

    else:
        if return_value is None:
            return_value = []

        def get_return_value(query, **kwargs):
            """Return mock for test query, return value otherwise."""
            if query == TEST_QUERY_V1:
                points = _make_v1_databases_resultset()
            else:
                if query_exception:
                    raise query_exception
                points = return_value

            query_output = MagicMock()
            query_output.get_points.return_value = points
            return query_output

        query_api.side_effect = get_return_value

    return query_api


def _set_query_mock_v2(
    mock_influx_client, return_value=None, query_exception=None, side_effect=None
):
    """Set return value or side effect for the V2 client."""
    query_api = mock_influx_client.return_value.query_api.return_value.query
    if side_effect:
        query_api.side_effect = side_effect
    else:
        if return_value is None:
            return_value = []

        def get_return_value(query):
            """Return buckets list for test query, return value otherwise."""
            if query == TEST_QUERY_V2:
                return _make_v2_buckets_resultset()

            if query_exception:
                raise query_exception

            return return_value

        query_api.side_effect = get_return_value

    return query_api


async def _setup.opp, config_ext, queries, expected_sensors):
    """Create client and test expected sensors."""
    config = {
        DOMAIN: config_ext,
        sensor.DOMAIN: {"platform": DOMAIN},
    }
    influx_config = config[sensor.DOMAIN]
    influx_config.update(config_ext)
    influx_config.update(queries)

    assert await async_setup_component.opp, sensor.DOMAIN, config)
    await opp.async_block_till_done()

    sensors = []
    for expected_sensor in expected_sensors:
        state = opp.states.get(expected_sensor)
        assert state is not None
        sensors.append(state)

    return sensors


@pytest.mark.parametrize(
    "mock_client, config_ext, queries, set_query_mock",
    [
        (DEFAULT_API_VERSION, BASE_V1_CONFIG, BASE_V1_QUERY, _set_query_mock_v1),
        (API_VERSION_2, BASE_V2_CONFIG, BASE_V2_QUERY, _set_query_mock_v2),
    ],
    indirect=["mock_client"],
)
async def test_minimal_config.opp, mock_client, config_ext, queries, set_query_mock):
    """Test the minimal config and defaults."""
    set_query_mock(mock_client)
    await _setup.opp, config_ext, queries, ["sensor.test"])


@pytest.mark.parametrize(
    "mock_client, config_ext, queries, set_query_mock",
    [
        (
            DEFAULT_API_VERSION,
            {
                "ssl": "true",
                "host": "host",
                "port": "9000",
                "path": "path",
                "username": "user",
                "password": "pass",
                "database": "db",
                "verify_ssl": "true",
            },
            {
                "queries": [
                    {
                        "name": "test",
                        "unit_of_measurement": "unit",
                        "measurement": "measurement",
                        "where": "where",
                        "value_template": "value",
                        "database": "db2",
                        "group_function": "fn",
                        "field": "field",
                    }
                ],
            },
            _set_query_mock_v1,
        ),
        (
            API_VERSION_2,
            {
                "api_version": "2",
                "ssl": "true",
                "host": "host",
                "port": "9000",
                "path": "path",
                "token": "token",
                "organization": "org",
                "bucket": "bucket",
            },
            {
                "queries_flux": [
                    {
                        "name": "test",
                        "unit_of_measurement": "unit",
                        "range_start": "start",
                        "range_stop": "end",
                        "group_function": "fn",
                        "bucket": "bucket2",
                        "imports": "import",
                        "query": "query",
                    }
                ],
            },
            _set_query_mock_v2,
        ),
    ],
    indirect=["mock_client"],
)
async def test_full_config.opp, mock_client, config_ext, queries, set_query_mock):
    """Test the full config."""
    set_query_mock(mock_client)
    await _setup.opp, config_ext, queries, ["sensor.test"])


@pytest.mark.parametrize("config_ext", [(BASE_V1_CONFIG), (BASE_V2_CONFIG)])
async def test_config_failure.opp, config_ext):
    """Test an invalid config."""
    config = {"platform": DOMAIN}
    config.update(config_ext)

    with pytest.raises(Invalid):
        PLATFORM_SCHEMA(config)


@pytest.mark.parametrize(
    "mock_client, config_ext, queries, set_query_mock, make_resultset",
    [
        (
            DEFAULT_API_VERSION,
            BASE_V1_CONFIG,
            BASE_V1_QUERY,
            _set_query_mock_v1,
            _make_v1_resultset,
        ),
        (
            API_VERSION_2,
            BASE_V2_CONFIG,
            BASE_V2_QUERY,
            _set_query_mock_v2,
            _make_v2_resultset,
        ),
    ],
    indirect=["mock_client"],
)
async def test_state_matches_query_result(
   .opp, mock_client, config_ext, queries, set_query_mock, make_resultset
):
    """Test state of sensor matches respone from query api."""
    set_query_mock(mock_client, return_value=make_resultset(42))

    sensors = await _setup.opp, config_ext, queries, ["sensor.test"])

    assert sensors[0].state == "42"


@pytest.mark.parametrize(
    "mock_client, config_ext, queries, set_query_mock, make_resultset",
    [
        (
            DEFAULT_API_VERSION,
            BASE_V1_CONFIG,
            BASE_V1_QUERY,
            _set_query_mock_v1,
            _make_v1_resultset,
        ),
        (
            API_VERSION_2,
            BASE_V2_CONFIG,
            BASE_V2_QUERY,
            _set_query_mock_v2,
            _make_v2_resultset,
        ),
    ],
    indirect=["mock_client"],
)
async def test_state_matches_first_query_result_for_multiple_return(
   .opp, caplog, mock_client, config_ext, queries, set_query_mock, make_resultset
):
    """Test state of sensor matches respone from query api."""
    set_query_mock(mock_client, return_value=make_resultset(42, "not used"))

    sensors = await _setup.opp, config_ext, queries, ["sensor.test"])
    assert sensors[0].state == "42"
    assert (
        len([record for record in caplog.records if record.levelname == "WARNING"]) == 1
    )


@pytest.mark.parametrize(
    "mock_client, config_ext, queries, set_query_mock",
    [
        (
            DEFAULT_API_VERSION,
            BASE_V1_CONFIG,
            BASE_V1_QUERY,
            _set_query_mock_v1,
        ),
        (API_VERSION_2, BASE_V2_CONFIG, BASE_V2_QUERY, _set_query_mock_v2),
    ],
    indirect=["mock_client"],
)
async def test_state_for_no_results(
   .opp, caplog, mock_client, config_ext, queries, set_query_mock
):
    """Test state of sensor matches respone from query api."""
    set_query_mock(mock_client)

    sensors = await _setup.opp, config_ext, queries, ["sensor.test"])
    assert sensors[0].state == STATE_UNKNOWN
    assert (
        len([record for record in caplog.records if record.levelname == "WARNING"]) == 1
    )


@pytest.mark.parametrize(
    "mock_client, config_ext, queries, set_query_mock, query_exception",
    [
        (
            DEFAULT_API_VERSION,
            BASE_V1_CONFIG,
            BASE_V1_QUERY,
            _set_query_mock_v1,
            OSError("fail"),
        ),
        (
            DEFAULT_API_VERSION,
            BASE_V1_CONFIG,
            BASE_V1_QUERY,
            _set_query_mock_v1,
            InfluxDBClientError("fail"),
        ),
        (
            DEFAULT_API_VERSION,
            BASE_V1_CONFIG,
            BASE_V1_QUERY,
            _set_query_mock_v1,
            InfluxDBClientError("fail", code=400),
        ),
        (
            API_VERSION_2,
            BASE_V2_CONFIG,
            BASE_V2_QUERY,
            _set_query_mock_v2,
            OSError("fail"),
        ),
        (
            API_VERSION_2,
            BASE_V2_CONFIG,
            BASE_V2_QUERY,
            _set_query_mock_v2,
            ApiException(),
        ),
        (
            API_VERSION_2,
            BASE_V2_CONFIG,
            BASE_V2_QUERY,
            _set_query_mock_v2,
            ApiException(status=400),
        ),
    ],
    indirect=["mock_client"],
)
async def test_error_querying_influx(
   .opp, caplog, mock_client, config_ext, queries, set_query_mock, query_exception
):
    """Test behavior of sensor when influx returns error."""
    set_query_mock(mock_client, query_exception=query_exception)

    sensors = await _setup.opp, config_ext, queries, ["sensor.test"])
    assert sensors[0].state == STATE_UNKNOWN
    assert (
        len([record for record in caplog.records if record.levelname == "ERROR"]) == 1
    )


@pytest.mark.parametrize(
    "mock_client, config_ext, queries, set_query_mock, make_resultset",
    [
        (
            DEFAULT_API_VERSION,
            BASE_V1_CONFIG,
            {
                "queries": [
                    {
                        "name": "test",
                        "measurement": "measurement",
                        "where": "{{ illegal.template }}",
                        "field": "field",
                    }
                ]
            },
            _set_query_mock_v1,
            _make_v1_resultset,
        ),
        (
            API_VERSION_2,
            BASE_V2_CONFIG,
            {"queries_flux": [{"name": "test", "query": "{{ illegal.template }}"}]},
            _set_query_mock_v2,
            _make_v2_resultset,
        ),
    ],
    indirect=["mock_client"],
)
async def test_error_rendering_template(
   .opp, caplog, mock_client, config_ext, queries, set_query_mock, make_resultset
):
    """Test behavior of sensor with error rendering template."""
    set_query_mock(mock_client, return_value=make_resultset(42))

    sensors = await _setup.opp, config_ext, queries, ["sensor.test"])
    assert sensors[0].state == STATE_UNKNOWN
    assert (
        len([record for record in caplog.records if record.levelname == "ERROR"]) == 1
    )


@pytest.mark.parametrize(
    "mock_client, config_ext, queries, set_query_mock, test_exception, make_resultset",
    [
        (
            DEFAULT_API_VERSION,
            BASE_V1_CONFIG,
            BASE_V1_QUERY,
            _set_query_mock_v1,
            OSError("fail"),
            _make_v1_resultset,
        ),
        (
            DEFAULT_API_VERSION,
            BASE_V1_CONFIG,
            BASE_V1_QUERY,
            _set_query_mock_v1,
            InfluxDBClientError("fail"),
            _make_v1_resultset,
        ),
        (
            DEFAULT_API_VERSION,
            BASE_V1_CONFIG,
            BASE_V1_QUERY,
            _set_query_mock_v1,
            InfluxDBServerError("fail"),
            _make_v1_resultset,
        ),
        (
            API_VERSION_2,
            BASE_V2_CONFIG,
            BASE_V2_QUERY,
            _set_query_mock_v2,
            OSError("fail"),
            _make_v2_resultset,
        ),
        (
            API_VERSION_2,
            BASE_V2_CONFIG,
            BASE_V2_QUERY,
            _set_query_mock_v2,
            ApiException(),
            _make_v2_resultset,
        ),
    ],
    indirect=["mock_client"],
)
async def test_connection_error_at_startup(
   .opp,
    caplog,
    mock_client,
    config_ext,
    queries,
    set_query_mock,
    test_exception,
    make_resultset,
):
    """Test behavior of sensor when influx returns error."""
    query_api = set_query_mock(mock_client, side_effect=test_exception)
    expected_sensor = "sensor.test"

    # Test sensor is not setup first time due to connection error
    await _setup.opp, config_ext, queries, [])
    assert.opp.states.get(expected_sensor) is None
    assert (
        len([record for record in caplog.records if record.levelname == "ERROR"]) == 1
    )

    # Stop throwing exception and advance time to test setup succeeds
    query_api.reset_mock(side_effect=True)
    set_query_mock(mock_client, return_value=make_resultset(42))
    new_time = dt_util.utcnow() + timedelta(seconds=PLATFORM_NOT_READY_BASE_WAIT_TIME)
    async_fire_time_changed.opp, new_time)
    await opp.async_block_till_done()
    assert.opp.states.get(expected_sensor) is not None


@pytest.mark.parametrize(
    "mock_client, config_ext, queries, set_query_mock",
    [
        (
            DEFAULT_API_VERSION,
            {"database": "bad_db"},
            BASE_V1_QUERY,
            _set_query_mock_v1,
        ),
        (
            API_VERSION_2,
            {
                "api_version": API_VERSION_2,
                "organization": "org",
                "token": "token",
                "bucket": "bad_bucket",
            },
            BASE_V2_QUERY,
            _set_query_mock_v2,
        ),
    ],
    indirect=["mock_client"],
)
async def test_data_repository_not_found(
   .opp,
    caplog,
    mock_client,
    config_ext,
    queries,
    set_query_mock,
):
    """Test sensor is not setup when bucket not available."""
    set_query_mock(mock_client)
    await _setup.opp, config_ext, queries, [])
    assert.opp.states.get("sensor.test") is None
    assert (
        len([record for record in caplog.records if record.levelname == "ERROR"]) == 1
    )
