"""Tests for the onboarding component."""

from openpeerpower.components import onboarding


def mock_storage.opp_storage, data):
    """Mock the onboarding storage."""
   .opp_storage[onboarding.STORAGE_KEY] = {
        "version": onboarding.STORAGE_VERSION,
        "data": data,
    }
