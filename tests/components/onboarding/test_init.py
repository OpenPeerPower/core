"""Tests for the init."""
from unittest.mock import Mock, patch

from openpeerpower.components import onboarding
from openpeerpower.setup import async_setup_component

from . import mock_storage

from tests.common import MockUser, mock_coro

# Temporarily: if auth not active, always set onboarded=True


async def test_not_setup_views_if_onboarded(opp, opp_storage):
    """Test if onboarding is done, we don't setup views."""
    mock_storage(opp_storage, {"done": onboarding.STEPS})

    with patch("openpeerpower.components.onboarding.views.async_setup") as mock_setup:
        assert await async_setup_component(opp, "onboarding", {})

    assert len(mock_setup.mock_calls) == 0
    assert onboarding.DOMAIN not in opp.data
    assert onboarding.async_is_onboarded(opp)


async def test_setup_views_if_not_onboarded(opp):
    """Test if onboarding is not done, we setup views."""
    with patch(
        "openpeerpower.components.onboarding.views.async_setup",
        return_value=mock_coro(),
    ) as mock_setup:
        assert await async_setup_component(opp, "onboarding", {})

    assert len(mock_setup.mock_calls) == 1
    assert onboarding.DOMAIN in opp.data

    assert not onboarding.async_is_onboarded(opp)


async def test_is_onboarded():
    """Test the is onboarded function."""
   opp = Mock()
    opp.data = {}

    assert onboarding.async_is_onboarded(opp)

    opp.data[onboarding.DOMAIN] = True
    assert onboarding.async_is_onboarded(opp)

    opp.data[onboarding.DOMAIN] = {"done": []}
    assert not onboarding.async_is_onboarded(opp)


async def test_is_user_onboarded():
    """Test the is onboarded function."""
   opp = Mock()
    opp.data = {}

    assert onboarding.async_is_user_onboarded(opp)

    opp.data[onboarding.DOMAIN] = True
    assert onboarding.async_is_user_onboarded(opp)

    opp.data[onboarding.DOMAIN] = {"done": []}
    assert not onboarding.async_is_user_onboarded(opp)


async def test_having_owner_finishes_user_step(opp, opp_storage):
    """If owner user already exists, mark user step as complete."""
    MockUser(is_owner=True).add_to_opp(opp)

    with patch(
        "openpeerpower.components.onboarding.views.async_setup"
    ) as mock_setup, patch.object(onboarding, "STEPS", [onboarding.STEP_USER]):
        assert await async_setup_component(opp, "onboarding", {})

    assert len(mock_setup.mock_calls) == 0
    assert onboarding.DOMAIN not in opp.data
    assert onboarding.async_is_onboarded(opp)

    done = opp_storage[onboarding.STORAGE_KEY]["data"]["done"]
    assert onboarding.STEP_USER in done


async def test_migration(opp, opp_storage):
    """Test migrating onboarding to new version."""
    opp.storage[onboarding.STORAGE_KEY] = {"version": 1, "data": {"done": ["user"]}}
    assert await async_setup_component(opp, "onboarding", {})
    assert onboarding.async_is_onboarded(opp)
