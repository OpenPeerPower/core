"""Test fixtures for Tasmota component."""
from unittest.mock import patch

from hatasmota.discovery import get_status_sensor_entities
import pytest

from openpeerpower import config_entries
from openpeerpower.components.tasmota.const import (
    CONF_DISCOVERY_PREFIX,
    DEFAULT_PREFIX,
    DOMAIN,
)

from tests.common import (
    MockConfigEntry,
    async_mock_service,
    mock_device_registry,
    mock_registry,
)
from tests.components.light.conftest import mock_light_profiles  # noqa


@pytest.fixture
def device_reg(opp):
    """Return an empty, loaded, registry."""
    return mock_device_registry(opp)


@pytest.fixture
def entity_reg(opp):
    """Return an empty, loaded, registry."""
    return mock_registry(opp)


@pytest.fixture
def calls.opp):
    """Track calls to a mock service."""
    return async_mock_service(opp, "test", "automation")


@pytest.fixture(autouse=True)
def disable_debounce():
    """Set MQTT debounce timer to zero."""
    with patch("hatasmota.mqtt.DEBOUNCE_TIMEOUT", 0):
        yield


@pytest.fixture
def status_sensor_disabled():
    """Fixture to allow overriding MQTT config."""
    return True


@pytest.fixture(autouse=True)
def disable_status_sensor(status_sensor_disabled):
    """Disable Tasmota status sensor."""
    wraps = None if status_sensor_disabled else get_status_sensor_entities
    with patch("hatasmota.discovery.get_status_sensor_entities", wraps=wraps):
        yield


async def setup_tasmota_helper(opp):
    """Set up Tasmota."""
    opp.config.components.add("tasmota")

    entry = MockConfigEntry(
        connection_class=config_entries.CONN_CLASS_LOCAL_PUSH,
        data={CONF_DISCOVERY_PREFIX: DEFAULT_PREFIX},
        domain=DOMAIN,
        title="Tasmota",
    )

    entry.add_to_opp(opp)

    assert await opp.config_entries.async_setup(entry.entry_id)
    await opp.async_block_till_done()

    assert "tasmota" in opp.config.components


@pytest.fixture
async def setup_tasmota(opp):
    """Set up Tasmota."""
    await setup_tasmota_helper(opp)
