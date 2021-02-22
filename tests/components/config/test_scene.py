"""Test Automation config panel."""
import json
from unittest.mock import patch

from openpeerpower.bootstrap import async_setup_component
from openpeerpower.components import config
from openpeerpower.util.yaml import dump


async def test_update_scene.opp, opp_client):
    """Test updating a scene."""
    with patch.object(config, "SECTIONS", ["scene"]):
        await async_setup_component.opp, "config", {})

    client = await opp_client()

    orig_data = [{"id": "light_on"}, {"id": "light_off"}]

    def mock_read(path):
        """Mock reading data."""
        return orig_data

    written = []

    def mock_write(path, data):
        """Mock writing data."""
        data = dump(data)
        written.append(data)

    with patch("openpeerpower.components.config._read", mock_read), patch(
        "openpeerpower.components.config._write", mock_write
    ), patch("openpeerpower.config.async.opp_config_yaml", return_value={}):
        resp = await client.post(
            "/api/config/scene/config/light_off",
            data=json.dumps(
                {
                    "id": "light_off",
                    "name": "Lights off",
                    "entities": {"light.bedroom": {"state": "off"}},
                }
            ),
        )

    assert resp.status == 200
    result = await resp.json()
    assert result == {"result": "ok"}

    assert len(written) == 1
    written_yaml = written[0]
    assert (
        written_yaml
        == """- id: light_on
- id: light_off
  name: Lights off
  entities:
    light.bedroom:
      state: 'off'
"""
    )


async def test_bad_formatted_scene.opp, opp_client):
    """Test that we handle scene without ID."""
    with patch.object(config, "SECTIONS", ["scene"]):
        await async_setup_component.opp, "config", {})

    client = await opp_client()

    orig_data = [
        {
            # No ID
            "entities": {"light.bedroom": "on"}
        },
        {"id": "light_off"},
    ]

    def mock_read(path):
        """Mock reading data."""
        return orig_data

    written = []

    def mock_write(path, data):
        """Mock writing data."""
        written.append(data)

    with patch("openpeerpower.components.config._read", mock_read), patch(
        "openpeerpower.components.config._write", mock_write
    ), patch("openpeerpower.config.async.opp_config_yaml", return_value={}):
        resp = await client.post(
            "/api/config/scene/config/light_off",
            data=json.dumps(
                {
                    "id": "light_off",
                    "name": "Lights off",
                    "entities": {"light.bedroom": {"state": "off"}},
                }
            ),
        )

    assert resp.status == 200
    result = await resp.json()
    assert result == {"result": "ok"}

    # Verify ID added to orig_data
    assert "id" in orig_data[0]

    assert orig_data[1] == {
        "id": "light_off",
        "name": "Lights off",
        "entities": {"light.bedroom": {"state": "off"}},
    }


async def test_delete_scene.opp, opp_client):
    """Test deleting a scene."""
    ent_reg = await opp.helpers.entity_registry.async_get_registry()

    assert await async_setup_component(
       .opp,
        "scene",
        {
            "scene": [
                {"id": "light_on", "name": "Light on", "entities": {}},
                {"id": "light_off", "name": "Light off", "entities": {}},
            ]
        },
    )

    assert len(ent_reg.entities) == 2

    with patch.object(config, "SECTIONS", ["scene"]):
        assert await async_setup_component.opp, "config", {})

    client = await opp_client()

    orig_data = [{"id": "light_on"}, {"id": "light_off"}]

    def mock_read(path):
        """Mock reading data."""
        return orig_data

    written = []

    def mock_write(path, data):
        """Mock writing data."""
        written.append(data)

    with patch("openpeerpower.components.config._read", mock_read), patch(
        "openpeerpower.components.config._write", mock_write
    ), patch("openpeerpower.config.async.opp_config_yaml", return_value={}):
        resp = await client.delete("/api/config/scene/config/light_on")
        await opp.async_block_till_done()

    assert resp.status == 200
    result = await resp.json()
    assert result == {"result": "ok"}

    assert len(written) == 1
    assert written[0][0]["id"] == "light_off"

    assert len(ent_reg.entities) == 1
