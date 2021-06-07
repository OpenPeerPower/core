"""Define tests for the GIOS config flow."""
import json
from unittest.mock import patch

from gios import ApiError

from openpeerpower import data_entry_flow
from openpeerpower.components.gios import config_flow
from openpeerpower.components.gios.const import CONF_STATION_ID
from openpeerpower.const import CONF_NAME

from tests.common import load_fixture
from tests.components.gios import STATIONS

CONFIG = {
    CONF_NAME: "Foo",
    CONF_STATION_ID: 123,
}


async def test_show_form(opp):
    """Test that the form is served with no input."""
    flow = config_flow.GiosFlowHandler()
    flow.opp = opp

    result = await flow.async_step_user(user_input=None)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"


async def test_invalid_station_id(opp):
    """Test that errors are shown when measuring station ID is invalid."""
    with patch(
        "openpeerpower.components.gios.Gios._get_stations", return_value=STATIONS
    ):
        flow = config_flow.GiosFlowHandler()
        flow.opp = opp
        flow.context = {}

        result = await flow.async_step_user(
            user_input={CONF_NAME: "Foo", CONF_STATION_ID: 0}
        )

        assert result["errors"] == {CONF_STATION_ID: "wrong_station_id"}


async def test_invalid_sensor_data(opp):
    """Test that errors are shown when sensor data is invalid."""
    with patch(
        "openpeerpower.components.gios.Gios._get_stations", return_value=STATIONS
    ), patch(
        "openpeerpower.components.gios.Gios._get_station",
        return_value=json.loads(load_fixture("gios/station.json")),
    ), patch(
        "openpeerpower.components.gios.Gios._get_sensor", return_value={}
    ):
        flow = config_flow.GiosFlowHandler()
        flow.opp = opp
        flow.context = {}

        result = await flow.async_step_user(user_input=CONFIG)

        assert result["errors"] == {CONF_STATION_ID: "invalid_sensors_data"}


async def test_cannot_connect(opp):
    """Test that errors are shown when cannot connect to GIOS server."""
    with patch(
        "openpeerpower.components.gios.Gios._async_get", side_effect=ApiError("error")
    ):
        flow = config_flow.GiosFlowHandler()
        flow.opp = opp
        flow.context = {}

        result = await flow.async_step_user(user_input=CONFIG)

        assert result["errors"] == {"base": "cannot_connect"}


async def test_create_entry(opp):
    """Test that the user step works."""
    with patch(
        "openpeerpower.components.gios.Gios._get_stations", return_value=STATIONS
    ), patch(
        "openpeerpower.components.gios.Gios._get_station",
        return_value=json.loads(load_fixture("gios/station.json")),
    ), patch(
        "openpeerpower.components.gios.Gios._get_all_sensors",
        return_value=json.loads(load_fixture("gios/sensors.json")),
    ), patch(
        "openpeerpower.components.gios.Gios._get_indexes",
        return_value=json.loads(load_fixture("gios/indexes.json")),
    ):
        flow = config_flow.GiosFlowHandler()
        flow.opp = opp
        flow.context = {}

        result = await flow.async_step_user(user_input=CONFIG)

        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == CONFIG[CONF_STATION_ID]
        assert result["data"][CONF_STATION_ID] == CONFIG[CONF_STATION_ID]

        assert flow.context["unique_id"] == "123"
