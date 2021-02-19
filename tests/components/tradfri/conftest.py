"""Common tradfri test fixtures."""
from unittest.mock import Mock, patch

import pytest

from . import MOCK_GATEWAY_ID

from tests.components.light.conftest import mock_light_profiles  # noqa

# pylint: disable=protected-access


@pytest.fixture
def mock_gateway_info():
    """Mock get_gateway_info."""
    with patch(
        "openpeerpower.components.tradfri.config_flow.get_gateway_info"
    ) as gateway_info:
        yield gateway_info


@pytest.fixture
def mock_entry_setup():
    """Mock entry setup."""
    with patch("openpeerpower.components.tradfri.async_setup_entry") as mock_setup:
        mock_setup.return_value = True
        yield mock_setup


@pytest.fixture(name="gateway_id")
def mock_gateway_id_fixture():
    """Return mock gateway_id."""
    return MOCK_GATEWAY_ID


@pytest.fixture(name="mock_gateway")
def mock_gateway_fixture(gateway_id):
    """Mock a Tradfri gateway."""

    def get_devices():
        """Return mock devices."""
        return gateway.mock_devices

    def get_groups():
        """Return mock groups."""
        return gateway.mock_groups

    gateway_info = Mock(id=gateway_id, firmware_version="1.2.1234")

    def get_gateway_info():
        """Return mock gateway info."""
        return gateway_info

    gateway = Mock(
        get_devices=get_devices,
        get_groups=get_groups,
        get_gateway_info=get_gateway_info,
        mock_devices=[],
        mock_groups=[],
        mock_responses=[],
    )
    with patch("openpeerpower.components.tradfri.Gateway", return_value=gateway), patch(
        "openpeerpower.components.tradfri.config_flow.Gateway", return_value=gateway
    ):
        yield gateway


@pytest.fixture(name="mock_api")
def mock_api_fixture(mock_gateway):
    """Mock api."""

    async def api(command):
        """Mock api function."""
        # Store the data for "real" command objects.
        if hasattr(command, "_data") and not isinstance(command, Mock):
            mock_gateway.mock_responses.append(command._data)
        return command

    return api


@pytest.fixture(name="api_factory")
def mock_api_factory_fixture(mock_api):
    """Mock pytradfri api factory."""
    with patch("openpeerpower.components.tradfri.APIFactory", autospec=True) as factory:
        factory.init.return_value = factory.return_value
        factory.return_value.request = mock_api
        yield factory.return_value
