"""Common fixtures for smarttub tests."""

from unittest.mock import create_autospec, patch

import pytest
import smarttub

from openpeerpower.components.smarttub.const import DOMAIN
from openpeerpower.const import CONF_EMAIL, CONF_PASSWORD
from openpeerpower.setup import async_setup_component

from tests.common import MockConfigEntry


@pytest.fixture
def config_data():
    """Provide configuration data for tests."""
    return {CONF_EMAIL: "test-email", CONF_PASSWORD: "test-password"}


@pytest.fixture
def config_entry(config_data):
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data=config_data,
        options={},
    )


@pytest.fixture
async def setup_component.opp):
    """Set up the component."""
    assert await async_setup_component.opp, DOMAIN, {}) is True


@pytest.fixture(name="spa")
def mock_spa():
    """Mock a SmartTub.Spa."""

    mock_spa = create_autospec(smarttub.Spa, instance=True)
    mock_spa.id = "mockspa1"
    mock_spa.brand = "mockbrand1"
    mock_spa.model = "mockmodel1"
    mock_spa.get_status.return_value = {
        "setTemperature": 39,
        "water": {"temperature": 38},
        "heater": "ON",
        "state": "NORMAL",
    }
    return mock_spa


@pytest.fixture(name="account")
def mock_account(spa):
    """Mock a SmartTub.Account."""

    mock_account = create_autospec(smarttub.Account, instance=True)
    mock_account.id = "mockaccount1"
    mock_account.get_spas.return_value = [spa]
    return mock_account


@pytest.fixture(name="smarttub_api", autouse=True)
def mock_api(account, spa):
    """Mock the SmartTub API."""

    with patch(
        "openpeerpower.components.smarttub.controller.SmartTub",
        autospec=True,
    ) as api_class_mock:
        api_mock = api_class_mock.return_value
        api_mock.get_account.return_value = account
        yield api_mock


@pytest.fixture
async def setup_entry.opp, config_entry):
    """Initialize the config entry."""
    config_entry.add_to.opp.opp)
    await opp.config_entries.async_setup(config_entry.entry_id)
    await opp.async_block_till_done()
