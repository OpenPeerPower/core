"""Test the default_config init."""
from unittest.mock import patch

import pytest

from openpeerpower.setup import async_setup_component

from tests.components.blueprint.conftest import stub_blueprint_populate  # noqa: F401


@pytest.fixture(autouse=True)
def mock_ssdp():
    """Mock ssdp."""
    with patch("openpeerpower.components.ssdp.Scanner.async_scan"):
        yield


@pytest.fixture(autouse=True)
def mock_updater():
    """Mock updater."""
    with patch("openpeerpower.components.updater.get_newest_version"):
        yield


@pytest.fixture(autouse=True)
def recorder_url_mock():
    """Mock recorder url."""
    with patch("openpeerpower.components.recorder.DEFAULT_URL", "sqlite://"):
        yield


async def test_setup(opp, mock_zeroconf):
    """Test setup."""
    assert await async_setup_component(opp, "default_config", {"foo": "bar"})
