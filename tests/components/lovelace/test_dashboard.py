"""Test the Lovelace initialization."""
from unittest.mock import patch

import pytest

from openpeerpower.components import frontend
from openpeerpower.components.lovelace import const, dashboard
from openpeerpowerr.setup import async_setup_component

from tests.common import assert_setup_component, async_capture_events


async def test_lovelace_from_storage.opp,.opp_ws_client,.opp_storage):
    """Test we load lovelace config from storage."""
    assert await async_setup_component.opp, "lovelace", {})
    assert.opp.data[frontend.DATA_PANELS]["lovelace"].config == {"mode": "storage"}

    client = await.opp_ws_client.opp)

    # Fetch data
    await client.send_json({"id": 5, "type": "lovelace/config"})
    response = await client.receive_json()
    assert not response["success"]
    assert response["error"]["code"] == "config_not_found"

    # Store new config
    events = async_capture_events.opp, const.EVENT_LOVELACE_UPDATED)

    await client.send_json(
        {"id": 6, "type": "lovelace/config/save", "config": {"yo": "hello"}}
    )
    response = await client.receive_json()
    assert response["success"]
    assert.opp_storage[dashboard.CONFIG_STORAGE_KEY_DEFAULT]["data"] == {
        "config": {"yo": "hello"}
    }
    assert len(events) == 1

    # Load new config
    await client.send_json({"id": 7, "type": "lovelace/config"})
    response = await client.receive_json()
    assert response["success"]

    assert response["result"] == {"yo": "hello"}

    # Test with safe mode
   .opp.config.safe_mode = True
    await client.send_json({"id": 8, "type": "lovelace/config"})
    response = await client.receive_json()
    assert not response["success"]
    assert response["error"]["code"] == "config_not_found"

    await client.send_json(
        {"id": 9, "type": "lovelace/config/save", "config": {"yo": "hello"}}
    )
    response = await client.receive_json()
    assert not response["success"]

    await client.send_json({"id": 10, "type": "lovelace/config/delete"})
    response = await client.receive_json()
    assert not response["success"]


async def test_lovelace_from_storage_save_before_load(
   .opp,.opp_ws_client,.opp_storage
):
    """Test we can load lovelace config from storage."""
    assert await async_setup_component.opp, "lovelace", {})
    client = await.opp_ws_client.opp)

    # Store new config
    await client.send_json(
        {"id": 6, "type": "lovelace/config/save", "config": {"yo": "hello"}}
    )
    response = await client.receive_json()
    assert response["success"]
    assert.opp_storage[dashboard.CONFIG_STORAGE_KEY_DEFAULT]["data"] == {
        "config": {"yo": "hello"}
    }


async def test_lovelace_from_storage_delete.opp,.opp_ws_client,.opp_storage):
    """Test we delete lovelace config from storage."""
    assert await async_setup_component.opp, "lovelace", {})
    client = await.opp_ws_client.opp)

    # Store new config
    await client.send_json(
        {"id": 6, "type": "lovelace/config/save", "config": {"yo": "hello"}}
    )
    response = await client.receive_json()
    assert response["success"]
    assert.opp_storage[dashboard.CONFIG_STORAGE_KEY_DEFAULT]["data"] == {
        "config": {"yo": "hello"}
    }

    # Delete config
    await client.send_json({"id": 7, "type": "lovelace/config/delete"})
    response = await client.receive_json()
    assert response["success"]
    assert dashboard.CONFIG_STORAGE_KEY_DEFAULT not in.opp_storage

    # Fetch data
    await client.send_json({"id": 8, "type": "lovelace/config"})
    response = await client.receive_json()
    assert not response["success"]
    assert response["error"]["code"] == "config_not_found"


async def test_lovelace_from_yaml.opp,.opp_ws_client):
    """Test we load lovelace config from yaml."""
    assert await async_setup_component.opp, "lovelace", {"lovelace": {"mode": "YAML"}})
    assert.opp.data[frontend.DATA_PANELS]["lovelace"].config == {"mode": "yaml"}

    client = await.opp_ws_client.opp)

    # Fetch data
    await client.send_json({"id": 5, "type": "lovelace/config"})
    response = await client.receive_json()
    assert not response["success"]

    assert response["error"]["code"] == "config_not_found"

    # Store new config not allowed
    await client.send_json(
        {"id": 6, "type": "lovelace/config/save", "config": {"yo": "hello"}}
    )
    response = await client.receive_json()
    assert not response["success"]

    # Patch data
    events = async_capture_events.opp, const.EVENT_LOVELACE_UPDATED)

    with patch(
        "openpeerpower.components.lovelace.dashboard.load_yaml",
        return_value={"hello": "yo"},
    ):
        await client.send_json({"id": 7, "type": "lovelace/config"})
        response = await client.receive_json()

    assert response["success"]
    assert response["result"] == {"hello": "yo"}

    assert len(events) == 0

    # Fake new data to see we fire event
    with patch(
        "openpeerpower.components.lovelace.dashboard.load_yaml",
        return_value={"hello": "yo2"},
    ):
        await client.send_json({"id": 8, "type": "lovelace/config", "force": True})
        response = await client.receive_json()

    assert response["success"]
    assert response["result"] == {"hello": "yo2"}

    assert len(events) == 1


@pytest.mark.parametrize("url_path", ("test-panel", "test-panel-no-sidebar"))
async def test_dashboard_from_yaml.opp,.opp_ws_client, url_path):
    """Test we load lovelace dashboard config from yaml."""
    assert await async_setup_component(
       .opp,
        "lovelace",
        {
            "lovelace": {
                "dashboards": {
                    "test-panel": {
                        "mode": "yaml",
                        "filename": "bla.yaml",
                        "title": "Test Panel",
                        "icon": "mdi:test-icon",
                        "show_in_sidebar": False,
                        "require_admin": True,
                    },
                    "test-panel-no-sidebar": {
                        "title": "Title No Sidebar",
                        "mode": "yaml",
                        "filename": "bla2.yaml",
                    },
                }
            }
        },
    )
    assert.opp.data[frontend.DATA_PANELS]["test-panel"].config == {"mode": "yaml"}
    assert.opp.data[frontend.DATA_PANELS]["test-panel-no-sidebar"].config == {
        "mode": "yaml"
    }

    client = await.opp_ws_client.opp)

    # List dashboards
    await client.send_json({"id": 4, "type": "lovelace/dashboards/list"})
    response = await client.receive_json()
    assert response["success"]
    assert len(response["result"]) == 2
    with_sb, without_sb = response["result"]

    assert with_sb["mode"] == "yaml"
    assert with_sb["filename"] == "bla.yaml"
    assert with_sb["title"] == "Test Panel"
    assert with_sb["icon"] == "mdi:test-icon"
    assert with_sb["show_in_sidebar"] is False
    assert with_sb["require_admin"] is True
    assert with_sb["url_path"] == "test-panel"

    assert without_sb["mode"] == "yaml"
    assert without_sb["filename"] == "bla2.yaml"
    assert without_sb["show_in_sidebar"] is True
    assert without_sb["require_admin"] is False
    assert without_sb["url_path"] == "test-panel-no-sidebar"

    # Fetch data
    await client.send_json({"id": 5, "type": "lovelace/config", "url_path": url_path})
    response = await client.receive_json()
    assert not response["success"]

    assert response["error"]["code"] == "config_not_found"

    # Store new config not allowed
    await client.send_json(
        {
            "id": 6,
            "type": "lovelace/config/save",
            "config": {"yo": "hello"},
            "url_path": url_path,
        }
    )
    response = await client.receive_json()
    assert not response["success"]

    # Patch data
    events = async_capture_events.opp, const.EVENT_LOVELACE_UPDATED)

    with patch(
        "openpeerpower.components.lovelace.dashboard.load_yaml",
        return_value={"hello": "yo"},
    ):
        await client.send_json(
            {"id": 7, "type": "lovelace/config", "url_path": url_path}
        )
        response = await client.receive_json()

    assert response["success"]
    assert response["result"] == {"hello": "yo"}

    assert len(events) == 0

    # Fake new data to see we fire event
    with patch(
        "openpeerpower.components.lovelace.dashboard.load_yaml",
        return_value={"hello": "yo2"},
    ):
        await client.send_json(
            {"id": 8, "type": "lovelace/config", "force": True, "url_path": url_path}
        )
        response = await client.receive_json()

    assert response["success"]
    assert response["result"] == {"hello": "yo2"}

    assert len(events) == 1


async def test_wrong_key_dashboard_from_yaml.opp):
    """Test we don't load lovelace dashboard without hyphen config from yaml."""
    with assert_setup_component(0):
        assert not await async_setup_component(
           .opp,
            "lovelace",
            {
                "lovelace": {
                    "dashboards": {
                        "testpanel": {
                            "mode": "yaml",
                            "filename": "bla.yaml",
                            "title": "Test Panel",
                            "icon": "mdi:test-icon",
                            "show_in_sidebar": False,
                            "require_admin": True,
                        }
                    }
                }
            },
        )


async def test_storage_dashboards.opp,.opp_ws_client,.opp_storage):
    """Test we load lovelace config from storage."""
    assert await async_setup_component.opp, "lovelace", {})
    assert.opp.data[frontend.DATA_PANELS]["lovelace"].config == {"mode": "storage"}

    client = await.opp_ws_client.opp)

    # Fetch data
    await client.send_json({"id": 5, "type": "lovelace/dashboards/list"})
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == []

    # Add a wrong dashboard
    await client.send_json(
        {
            "id": 6,
            "type": "lovelace/dashboards/create",
            "url_path": "path",
            "title": "Test path without hyphen",
        }
    )
    response = await client.receive_json()
    assert not response["success"]

    # Add a dashboard
    await client.send_json(
        {
            "id": 7,
            "type": "lovelace/dashboards/create",
            "url_path": "created-url-path",
            "require_admin": True,
            "title": "New Title",
            "icon": "mdi:map",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"]["require_admin"] is True
    assert response["result"]["title"] == "New Title"
    assert response["result"]["icon"] == "mdi:map"

    dashboard_id = response["result"]["id"]

    assert "created-url-path" in.opp.data[frontend.DATA_PANELS]

    await client.send_json({"id": 8, "type": "lovelace/dashboards/list"})
    response = await client.receive_json()
    assert response["success"]
    assert len(response["result"]) == 1
    assert response["result"][0]["mode"] == "storage"
    assert response["result"][0]["title"] == "New Title"
    assert response["result"][0]["icon"] == "mdi:map"
    assert response["result"][0]["show_in_sidebar"] is True
    assert response["result"][0]["require_admin"] is True

    # Fetch config
    await client.send_json(
        {"id": 9, "type": "lovelace/config", "url_path": "created-url-path"}
    )
    response = await client.receive_json()
    assert not response["success"]
    assert response["error"]["code"] == "config_not_found"

    # Store new config
    events = async_capture_events.opp, const.EVENT_LOVELACE_UPDATED)

    await client.send_json(
        {
            "id": 10,
            "type": "lovelace/config/save",
            "url_path": "created-url-path",
            "config": {"yo": "hello"},
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert.opp_storage[dashboard.CONFIG_STORAGE_KEY.format(dashboard_id)]["data"] == {
        "config": {"yo": "hello"}
    }
    assert len(events) == 1
    assert events[0].data["url_path"] == "created-url-path"

    await client.send_json(
        {"id": 11, "type": "lovelace/config", "url_path": "created-url-path"}
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {"yo": "hello"}

    # Update a dashboard
    await client.send_json(
        {
            "id": 12,
            "type": "lovelace/dashboards/update",
            "dashboard_id": dashboard_id,
            "require_admin": False,
            "icon": "mdi:updated",
            "show_in_sidebar": False,
            "title": "Updated Title",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert response["result"]["mode"] == "storage"
    assert response["result"]["url_path"] == "created-url-path"
    assert response["result"]["title"] == "Updated Title"
    assert response["result"]["icon"] == "mdi:updated"
    assert response["result"]["show_in_sidebar"] is False
    assert response["result"]["require_admin"] is False

    # List dashboards again and make sure we see latest config
    await client.send_json({"id": 13, "type": "lovelace/dashboards/list"})
    response = await client.receive_json()
    assert response["success"]
    assert len(response["result"]) == 1
    assert response["result"][0]["mode"] == "storage"
    assert response["result"][0]["url_path"] == "created-url-path"
    assert response["result"][0]["title"] == "Updated Title"
    assert response["result"][0]["icon"] == "mdi:updated"
    assert response["result"][0]["show_in_sidebar"] is False
    assert response["result"][0]["require_admin"] is False

    # Add dashboard with existing url path
    await client.send_json(
        {"id": 14, "type": "lovelace/dashboards/create", "url_path": "created-url-path"}
    )
    response = await client.receive_json()
    assert not response["success"]

    # Delete dashboards
    await client.send_json(
        {"id": 15, "type": "lovelace/dashboards/delete", "dashboard_id": dashboard_id}
    )
    response = await client.receive_json()
    assert response["success"]

    assert "created-url-path" not in.opp.data[frontend.DATA_PANELS]
    assert dashboard.CONFIG_STORAGE_KEY.format(dashboard_id) not in.opp_storage


async def test_storage_dashboard_migrate.opp,.opp_ws_client,.opp_storage):
    """Test changing url path from storage config."""
   .opp_storage[dashboard.DASHBOARDS_STORAGE_KEY] = {
        "key": "lovelace_dashboards",
        "version": 1,
        "data": {
            "items": [
                {
                    "icon": "mdi:tools",
                    "id": "tools",
                    "mode": "storage",
                    "require_admin": True,
                    "show_in_sidebar": True,
                    "title": "Tools",
                    "url_path": "tools",
                },
                {
                    "icon": "mdi:tools",
                    "id": "tools2",
                    "mode": "storage",
                    "require_admin": True,
                    "show_in_sidebar": True,
                    "title": "Tools",
                    "url_path": "dashboard-tools",
                },
            ]
        },
    }

    assert await async_setup_component.opp, "lovelace", {})

    client = await.opp_ws_client.opp)

    # Fetch data
    await client.send_json({"id": 5, "type": "lovelace/dashboards/list"})
    response = await client.receive_json()
    assert response["success"]
    without_hyphen, with_hyphen = response["result"]

    assert without_hyphen["icon"] == "mdi:tools"
    assert without_hyphen["id"] == "tools"
    assert without_hyphen["mode"] == "storage"
    assert without_hyphen["require_admin"]
    assert without_hyphen["show_in_sidebar"]
    assert without_hyphen["title"] == "Tools"
    assert without_hyphen["url_path"] == "lovelace-tools"

    assert (
        with_hyphen
        == opp_storage[dashboard.DASHBOARDS_STORAGE_KEY]["data"]["items"][1]
    )


async def test_websocket_list_dashboards.opp,.opp_ws_client):
    """Test listing dashboards both storage + YAML."""
    assert await async_setup_component(
       .opp,
        "lovelace",
        {
            "lovelace": {
                "dashboards": {
                    "test-panel-no-sidebar": {
                        "title": "Test YAML",
                        "mode": "yaml",
                        "filename": "bla.yaml",
                    },
                }
            }
        },
    )

    client = await.opp_ws_client.opp)

    # Create a storage dashboard
    await client.send_json(
        {
            "id": 6,
            "type": "lovelace/dashboards/create",
            "url_path": "created-url-path",
            "title": "Test Storage",
        }
    )
    response = await client.receive_json()
    assert response["success"]

    # List dashboards
    await client.send_json({"id": 8, "type": "lovelace/dashboards/list"})
    response = await client.receive_json()
    assert response["success"]
    assert len(response["result"]) == 2
    with_sb, without_sb = response["result"]

    assert with_sb["mode"] == "yaml"
    assert with_sb["title"] == "Test YAML"
    assert with_sb["filename"] == "bla.yaml"
    assert with_sb["url_path"] == "test-panel-no-sidebar"

    assert without_sb["mode"] == "storage"
    assert without_sb["title"] == "Test Storage"
    assert without_sb["url_path"] == "created-url-path"
