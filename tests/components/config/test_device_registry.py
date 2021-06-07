"""Test device_registry API."""
import pytest

from openpeerpower.components.config import device_registry
from openpeerpower.helpers import device_registry as helpers_dr

from tests.common import mock_device_registry
from tests.components.blueprint.conftest import stub_blueprint_populate  # noqa: F401


@pytest.fixture
def client(opp, opp_ws_client):
    """Fixture that can interact with the config manager API."""
    opp.loop.run_until_complete(device_registry.async_setup(opp))
    yield opp.loop.run_until_complete(opp_ws_client(opp))


@pytest.fixture
def registry(opp):
    """Return an empty, loaded, registry."""
    return mock_device_registry(opp)


async def test_list_devices(opp, client, registry):
    """Test list entries."""
    registry.async_get_or_create(
        config_entry_id="1234",
        connections={("ethernet", "12:34:56:78:90:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer",
        model="model",
    )
    registry.async_get_or_create(
        config_entry_id="1234",
        identifiers={("bridgeid", "1234")},
        manufacturer="manufacturer",
        model="model",
        via_device=("bridgeid", "0123"),
        entry_type="service",
    )

    await client.send_json({"id": 5, "type": "config/device_registry/list"})
    msg = await client.receive_json()

    dev1, dev2 = [entry.pop("id") for entry in msg["result"]]

    assert msg["result"] == [
        {
            "config_entries": ["1234"],
            "connections": [["ethernet", "12:34:56:78:90:AB:CD:EF"]],
            "identifiers": [["bridgeid", "0123"]],
            "manufacturer": "manufacturer",
            "model": "model",
            "name": None,
            "sw_version": None,
            "entry_type": None,
            "via_device_id": None,
            "area_id": None,
            "name_by_user": None,
            "disabled_by": None,
        },
        {
            "config_entries": ["1234"],
            "connections": [],
            "identifiers": [["bridgeid", "1234"]],
            "manufacturer": "manufacturer",
            "model": "model",
            "name": None,
            "sw_version": None,
            "entry_type": "service",
            "via_device_id": dev1,
            "area_id": None,
            "name_by_user": None,
            "disabled_by": None,
        },
    ]


async def test_update_device(opp, client, registry):
    """Test update entry."""
    device = registry.async_get_or_create(
        config_entry_id="1234",
        connections={("ethernet", "12:34:56:78:90:AB:CD:EF")},
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer",
        model="model",
    )

    assert not device.area_id
    assert not device.name_by_user

    await client.send_json(
        {
            "id": 1,
            "device_id": device.id,
            "area_id": "12345A",
            "name_by_user": "Test Friendly Name",
            "disabled_by": helpers_dr.DISABLED_USER,
            "type": "config/device_registry/update",
        }
    )

    msg = await client.receive_json()

    assert msg["result"]["id"] == device.id
    assert msg["result"]["area_id"] == "12345A"
    assert msg["result"]["name_by_user"] == "Test Friendly Name"
    assert msg["result"]["disabled_by"] == helpers_dr.DISABLED_USER
    assert len(registry.devices) == 1
