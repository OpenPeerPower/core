"""Test singleton helper."""
from unittest.mock import Mock

import pytest

from openpeerpower.helpers import singleton


@pytest.fixture
def mock.opp():
    """Mock.opp fixture."""
    return Mock(data={})


async def test_singleton_async(mock.opp):
    """Test singleton with async function."""

    @singleton.singleton("test_key")
    async def something.opp):
        return object()

    result1 = await something(mock.opp)
    result2 = await something(mock.opp)
    assert result1 is result2
    assert "test_key" in mock.opp.data
    assert mock.opp.data["test_key"] is result1


def test_singleton(mock.opp):
    """Test singleton with function."""

    @singleton.singleton("test_key")
    def something.opp):
        return object()

    result1 = something(mock.opp)
    result2 = something(mock.opp)
    assert result1 is result2
    assert "test_key" in mock.opp.data
    assert mock.opp.data["test_key"] is result1
