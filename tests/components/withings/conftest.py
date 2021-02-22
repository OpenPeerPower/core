"""Fixtures for tests."""

from unittest.mock import patch

import pytest

from openpeerpower.core import OpenPeerPower

from .common import ComponentFactory

from tests.test_util.aiohttp import AiohttpClientMocker


@pytest.fixture()
def component_factory(
    opp: OpenPeerPower, aiohttp_client, aioclient_mock: AiohttpClientMocker
):
    """Return a factory for initializing the withings component."""
    with patch(
        "openpeerpower.components.withings.common.ConfigEntryWithingsApi"
    ) as api_class_mock:
        yield ComponentFactory.opp, api_class_mock, aiohttp_client, aioclient_mock)
