"""HomeKit controller session fixtures."""
import datetime
from unittest import mock
import unittest.mock

from aiohomekit.testing import FakeController
import pytest

import openpeerpowerr.util.dt as dt_util

from tests.components.light.conftest import mock_light_profiles  # noqa


@pytest.fixture
def utcnow(request):
    """Freeze time at a known point."""
    now = dt_util.utcnow()
    start_dt = datetime.datetime(now.year + 1, 1, 1, 0, 0, 0, tzinfo=now.tzinfo)
    with mock.patch("openpeerpowerr.util.dt.utcnow") as dt_utcnow:
        dt_utcnow.return_value = start_dt
        yield dt_utcnow


@pytest.fixture
def controller.opp):
    """Replace aiohomekit.Controller with an instance of aiohomekit.testing.FakeController."""
    instance = FakeController()
    with unittest.mock.patch("aiohomekit.Controller", return_value=instance):
        yield instance
