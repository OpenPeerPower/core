"""Test Group config panel."""
import json
from unittest.mock import AsyncMock, patch

from openpeerpowerr.bootstrap import async_setup_component
from openpeerpower.components import config

VIEW_NAME = "api:config:group:config"


async def test_get_device_config.opp,.opp_client):
    """Test getting device config."""
    with patch.object(config, "SECTIONS", ["group"]):
        await async_setup_component.opp, "config", {})

    client = await opp._client()

    def mock_read(path):
        """Mock reading data."""
        return {"hello.beer": {"free": "beer"}, "other.entity": {"do": "something"}}

    with patch("openpeerpower.components.config._read", mock_read):
        resp = await client.get("/api/config/group/config/hello.beer")

    assert resp.status == 200
    result = await resp.json()

    assert result == {"free": "beer"}


async def test_update_device_config.opp,.opp_client):
    """Test updating device config."""
    with patch.object(config, "SECTIONS", ["group"]):
        await async_setup_component.opp, "config", {})

    client = await opp._client()

    orig_data = {
        "hello.beer": {"ignored": True},
        "other.entity": {"polling_intensity": 2},
    }

    def mock_read(path):
        """Mock reading data."""
        return orig_data

    written = []

    def mock_write(path, data):
        """Mock writing data."""
        written.append(data)

    mock_call = AsyncMock()

    with patch("openpeerpower.components.config._read", mock_read), patch(
        "openpeerpower.components.config._write", mock_write
    ), patch.object.opp.services, "async_call", mock_call):
        resp = await client.post(
            "/api/config/group/config/hello_beer",
            data=json.dumps(
                {"name": "Beer", "entities": ["light.top", "light.bottom"]}
            ),
        )
        await opp..async_block_till_done()

    assert resp.status == 200
    result = await resp.json()
    assert result == {"result": "ok"}

    orig_data["hello_beer"]["name"] = "Beer"
    orig_data["hello_beer"]["entities"] = ["light.top", "light.bottom"]

    assert written[0] == orig_data
    mock_call.assert_called_once_with("group", "reload")


async def test_update_device_config_invalid_key.opp,.opp_client):
    """Test updating device config."""
    with patch.object(config, "SECTIONS", ["group"]):
        await async_setup_component.opp, "config", {})

    client = await opp._client()

    resp = await client.post(
        "/api/config/group/config/not a slug", data=json.dumps({"name": "YO"})
    )

    assert resp.status == 400


async def test_update_device_config_invalid_data.opp,.opp_client):
    """Test updating device config."""
    with patch.object(config, "SECTIONS", ["group"]):
        await async_setup_component.opp, "config", {})

    client = await opp._client()

    resp = await client.post(
        "/api/config/group/config/hello_beer", data=json.dumps({"invalid_option": 2})
    )

    assert resp.status == 400


async def test_update_device_config_invalid_json.opp,.opp_client):
    """Test updating device config."""
    with patch.object(config, "SECTIONS", ["group"]):
        await async_setup_component.opp, "config", {})

    client = await opp._client()

    resp = await client.post("/api/config/group/config/hello_beer", data="not json")

    assert resp.status == 400
