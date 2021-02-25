"""The sensor tests for the griddy platform."""
import json
import os
from unittest.mock import patch

from griddypower.async_api import GriddyPriceData

from openpeerpower.components.griddy import CONF_LOADZONE, DOMAIN
from openpeerpower.setup import async_setup_component

from tests.common import load_fixture


async def _load_json_fixture(opp, path):
    fixture = await opp.async_add_executor_job(
        load_fixture, os.path.join("griddy", path)
    )
    return json.loads(fixture)


def _mock_get_config():
    """Return a default griddy config."""
    return {DOMAIN: {CONF_LOADZONE: "LZ_HOUSTON"}}


async def test_houston_loadzone.opp):
    """Test creation of the houston load zone."""

    getnow_json = await _load_json_fixture(opp, "getnow.json")
    griddy_price_data = GriddyPriceData(getnow_json)
    with patch(
        "openpeerpower.components.griddy.AsyncGriddy.async_getnow",
        return_value=griddy_price_data,
    ):
        assert await async_setup_component(opp, DOMAIN, _mock_get_config())
        await opp.async_block_till_done()

    sensor_lz_houston_price_now = opp.states.get("sensor.lz_houston_price_now")
    assert sensor_lz_houston_price_now.state == "1.269"
