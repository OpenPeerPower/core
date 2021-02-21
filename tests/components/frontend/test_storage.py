"""The tests for frontend storage."""
import pytest

from openpeerpower.components.frontend import DOMAIN
from openpeerpower.setup import async_setup_component


@pytest.fixture(autouse=True)
def setup_frontend.opp):
    """Fixture to setup the frontend."""
   .opp.loop.run_until_complete(async_setup_component.opp, "frontend", {}))


async def test_get_user_data_empty.opp,.opp_ws_client,.opp_storage):
    """Test get_user_data command."""
    client = await.opp_ws_client.opp)

    await client.send_json(
        {"id": 5, "type": "frontend/get_user_data", "key": "non-existing-key"}
    )

    res = await client.receive_json()
    assert res["success"], res
    assert res["result"]["value"] is None


async def test_get_user_data.opp,.opp_ws_client,.opp_admin_user,.opp_storage):
    """Test get_user_data command."""
    storage_key = f"{DOMAIN}.user_data_.opp_admin_user.id}"
   .opp_storage[storage_key] = {
        "key": storage_key,
        "version": 1,
        "data": {"test-key": "test-value", "test-complex": [{"foo": "bar"}]},
    }

    client = await.opp_ws_client.opp)

    # Get a simple string key

    await client.send_json(
        {"id": 6, "type": "frontend/get_user_data", "key": "test-key"}
    )

    res = await client.receive_json()
    assert res["success"], res
    assert res["result"]["value"] == "test-value"

    # Get a more complex key

    await client.send_json(
        {"id": 7, "type": "frontend/get_user_data", "key": "test-complex"}
    )

    res = await client.receive_json()
    assert res["success"], res
    assert res["result"]["value"][0]["foo"] == "bar"

    # Get all data (no key)

    await client.send_json({"id": 8, "type": "frontend/get_user_data"})

    res = await client.receive_json()
    assert res["success"], res
    assert res["result"]["value"]["test-key"] == "test-value"
    assert res["result"]["value"]["test-complex"][0]["foo"] == "bar"


async def test_set_user_data_empty.opp,.opp_ws_client,.opp_storage):
    """Test set_user_data command."""
    client = await.opp_ws_client.opp)

    # test creating

    await client.send_json(
        {"id": 6, "type": "frontend/get_user_data", "key": "test-key"}
    )

    res = await client.receive_json()
    assert res["success"], res
    assert res["result"]["value"] is None

    await client.send_json(
        {
            "id": 7,
            "type": "frontend/set_user_data",
            "key": "test-key",
            "value": "test-value",
        }
    )

    res = await client.receive_json()
    assert res["success"], res

    await client.send_json(
        {"id": 8, "type": "frontend/get_user_data", "key": "test-key"}
    )

    res = await client.receive_json()
    assert res["success"], res
    assert res["result"]["value"] == "test-value"


async def test_set_user_data.opp,.opp_ws_client,.opp_storage,.opp_admin_user):
    """Test set_user_data command with initial data."""
    storage_key = f"{DOMAIN}.user_data_.opp_admin_user.id}"
   .opp_storage[storage_key] = {
        "version": 1,
        "data": {"test-key": "test-value", "test-complex": "string"},
    }

    client = await.opp_ws_client.opp)

    # test creating

    await client.send_json(
        {
            "id": 5,
            "type": "frontend/set_user_data",
            "key": "test-non-existent-key",
            "value": "test-value-new",
        }
    )

    res = await client.receive_json()
    assert res["success"], res

    await client.send_json(
        {"id": 6, "type": "frontend/get_user_data", "key": "test-non-existent-key"}
    )

    res = await client.receive_json()
    assert res["success"], res
    assert res["result"]["value"] == "test-value-new"

    # test updating with complex data

    await client.send_json(
        {
            "id": 7,
            "type": "frontend/set_user_data",
            "key": "test-complex",
            "value": [{"foo": "bar"}],
        }
    )

    res = await client.receive_json()
    assert res["success"], res

    await client.send_json(
        {"id": 8, "type": "frontend/get_user_data", "key": "test-complex"}
    )

    res = await client.receive_json()
    assert res["success"], res
    assert res["result"]["value"][0]["foo"] == "bar"

    # ensure other existing key was not modified

    await client.send_json(
        {"id": 9, "type": "frontend/get_user_data", "key": "test-key"}
    )

    res = await client.receive_json()
    assert res["success"], res
    assert res["result"]["value"] == "test-value"
