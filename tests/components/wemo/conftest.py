"""Fixtures for pywemo."""
import asyncio
from unittest.mock import create_autospec, patch

import pytest
import pywemo

from openpeerpower.components.wemo import CONF_DISCOVERY, CONF_STATIC
from openpeerpower.components.wemo.const import DOMAIN
from openpeerpower.setup import async_setup_component

MOCK_HOST = "127.0.0.1"
MOCK_PORT = 50000
MOCK_NAME = "WemoDeviceName"
MOCK_SERIAL_NUMBER = "WemoSerialNumber"


@pytest.fixture(name="pywemo_model")
def pywemo_model_fixture():
    """Fixture containing a pywemo class name used by pywemo_device_fixture."""
    return "Insight"


@pytest.fixture(name="pywemo_registry")
def pywemo_registry_fixture():
    """Fixture for SubscriptionRegistry instances."""
    registry = create_autospec(pywemo.SubscriptionRegistry, instance=True)

    registry.callbacks = {}
    registry.semaphore = asyncio.Semaphore(value=0)

    def on_func(device, type_filter, callback):
        registry.callbacks[device.name] = callback
        registry.semaphore.release()

    registry.on.side_effect = on_func

    with patch("pywemo.SubscriptionRegistry", return_value=registry):
        yield registry


@pytest.fixture(name="pywemo_device")
def pywemo_device_fixture(pywemo_registry, pywemo_model):
    """Fixture for WeMoDevice instances."""
    device = create_autospec(getattr(pywemo, pywemo_model), instance=True)
    device.host = MOCK_HOST
    device.port = MOCK_PORT
    device.name = MOCK_NAME
    device.serialnumber = MOCK_SERIAL_NUMBER
    device.model_name = pywemo_model
    device.get_state.return_value = 0  # Default to Off

    url = f"http://{MOCK_HOST}:{MOCK_PORT}/setup.xml"
    with patch("pywemo.setup_url_for_address", return_value=url), patch(
        "pywemo.discovery.device_from_description", return_value=device
    ):
        yield device


@pytest.fixture(name="wemo_entity")
async def async_wemo_entity_fixture.opp, pywemo_device):
    """Fixture for a Wemo entity in.opp."""
    assert await async_setup_component(
       .opp,
        DOMAIN,
        {
            DOMAIN: {
                CONF_DISCOVERY: False,
                CONF_STATIC: [f"{MOCK_HOST}:{MOCK_PORT}"],
            },
        },
    )
    await.opp.async_block_till_done()

    entity_registry = await.opp.helpers.entity_registry.async_get_registry()
    entity_entries = list(entity_registry.entities.values())
    assert len(entity_entries) == 1

    yield entity_entries[0]
