"""Configure py.test."""
from unittest.mock import patch

import pytest


@pytest.fixture(name="skip_notifications", autouse=True)
def skip_notifications_fixture():
    """Skip notification calls."""
    with patch("openpeerpower.components.persistent_notification.async_create"), patch(
        "openpeerpower.components.persistent_notification.async_dismiss"
    ):
        yield


@pytest.fixture(name="climacell_config_flow_connect", autouse=True)
def climacell_config_flow_connect():
    """Mock valid climacell config flow setup."""
    with patch(
        "openpeerpower.components.climacell.config_flow.ClimaCell.realtime",
        return_value={},
    ):
        yield


@pytest.fixture(name="climacell_config_entry_update")
def climacell_config_entry_update_fixture():
    """Mock valid climacell config entry setup."""
    with patch(
        "openpeerpower.components.climacell.ClimaCell.realtime",
        return_value={},
    ), patch(
        "openpeerpower.components.climacell.ClimaCell.forecast_hourly",
        return_value=[],
    ), patch(
        "openpeerpower.components.climacell.ClimaCell.forecast_daily",
        return_value=[],
    ), patch(
        "openpeerpower.components.climacell.ClimaCell.forecast_nowcast",
        return_value=[],
    ):
        yield
