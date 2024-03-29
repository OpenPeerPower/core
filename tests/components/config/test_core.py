"""Test opp.ian config."""
from unittest.mock import patch

import pytest

from openpeerpower.bootstrap import async_setup_component
from openpeerpower.components import config
from openpeerpower.components.websocket_api.const import TYPE_RESULT
from openpeerpower.const import CONF_UNIT_SYSTEM, CONF_UNIT_SYSTEM_IMPERIAL
from openpeerpower.util import dt as dt_util, location

ORIG_TIME_ZONE = dt_util.DEFAULT_TIME_ZONE


@pytest.fixture
async def client(opp, opp_ws_client):
    """Fixture that can interact with the config manager API."""
    with patch.object(config, "SECTIONS", ["core"]):
        assert await async_setup_component(opp, "config", {})
    return await opp_ws_client(opp)


async def test_validate_config_ok(opp, opp_client):
    """Test checking config."""
    with patch.object(config, "SECTIONS", ["core"]):
        await async_setup_component(opp, "config", {})

    client = await opp_client()

    with patch(
        "openpeerpower.components.config.core.async_check_op_config_file",
        return_value=None,
    ):
        resp = await client.post("/api/config/core/check_config")

    assert resp.status == 200
    result = await resp.json()
    assert result["result"] == "valid"
    assert result["errors"] is None

    with patch(
        "openpeerpower.components.config.core.async_check_op_config_file",
        return_value="beer",
    ):
        resp = await client.post("/api/config/core/check_config")

    assert resp.status == 200
    result = await resp.json()
    assert result["result"] == "invalid"
    assert result["errors"] == "beer"


async def test_websocket_core_update(opp, client):
    """Test core config update websocket command."""
    assert opp.config.latitude != 60
    assert opp.config.longitude != 50
    assert opp.config.elevation != 25
    assert opp.config.location_name != "Huis"
    assert opp.config.units.name != CONF_UNIT_SYSTEM_IMPERIAL
    assert opp.config.time_zone != "America/New_York"
    assert opp.config.external_url != "https://www.example.com"
    assert opp.config.internal_url != "http://example.com"

    with patch("openpeerpower.util.dt.set_default_time_zone") as mock_set_tz:
        await client.send_json(
            {
                "id": 5,
                "type": "config/core/update",
                "latitude": 60,
                "longitude": 50,
                "elevation": 25,
                "location_name": "Huis",
                CONF_UNIT_SYSTEM: CONF_UNIT_SYSTEM_IMPERIAL,
                "time_zone": "America/New_York",
                "external_url": "https://www.example.com",
                "internal_url": "http://example.local",
            }
        )

        msg = await client.receive_json()

    assert msg["id"] == 5
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]
    assert opp.config.latitude == 60
    assert opp.config.longitude == 50
    assert opp.config.elevation == 25
    assert opp.config.location_name == "Huis"
    assert opp.config.units.name == CONF_UNIT_SYSTEM_IMPERIAL
    assert opp.config.external_url == "https://www.example.com"
    assert opp.config.internal_url == "http://example.local"

    assert len(mock_set_tz.mock_calls) == 1
    assert mock_set_tz.mock_calls[0][1][0] == dt_util.get_time_zone("America/New_York")


async def test_websocket_core_update_not_admin(opp, opp_ws_client, opp_admin_user):
    """Test core config fails for non admin."""
    opp_admin_user.groups = []
    with patch.object(config, "SECTIONS", ["core"]):
        await async_setup_component(opp, "config", {})

    client = await opp_ws_client(opp)
    await client.send_json({"id": 6, "type": "config/core/update", "latitude": 23})

    msg = await client.receive_json()

    assert msg["id"] == 6
    assert msg["type"] == TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == "unauthorized"


async def test_websocket_bad_core_update(opp, client):
    """Test core config update fails with bad parameters."""
    await client.send_json({"id": 7, "type": "config/core/update", "latituude": 23})

    msg = await client.receive_json()

    assert msg["id"] == 7
    assert msg["type"] == TYPE_RESULT
    assert not msg["success"]
    assert msg["error"]["code"] == "invalid_format"


async def test_detect_config(opp, client):
    """Test detect config."""
    with patch(
        "openpeerpower.util.location.async_detect_location_info",
        return_value=None,
    ):
        await client.send_json({"id": 1, "type": "config/core/detect"})

        msg = await client.receive_json()

    assert msg["success"] is True
    assert msg["result"] == {}


async def test_detect_config_fail(opp, client):
    """Test detect config."""
    with patch(
        "openpeerpower.util.location.async_detect_location_info",
        return_value=location.LocationInfo(
            ip=None,
            country_code=None,
            region_code=None,
            region_name=None,
            city=None,
            zip_code=None,
            latitude=None,
            longitude=None,
            use_metric=True,
            time_zone="Europe/Amsterdam",
        ),
    ):
        await client.send_json({"id": 1, "type": "config/core/detect"})

        msg = await client.receive_json()

    assert msg["success"] is True
    assert msg["result"] == {"unit_system": "metric", "time_zone": "Europe/Amsterdam"}
