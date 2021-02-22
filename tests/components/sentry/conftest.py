"""Configuration for Sonos tests."""
import pytest

from openpeerpower.components.sentry import DOMAIN

from tests.common import MockConfigEntry


@pytest.fixture(name="config_entry")
def config_entry_fixture():
    """Create a mock config entry."""
    return MockConfigEntry(domain=DOMAIN, title="Sentry")


@pytest.fixture(name="config")
def config_fixture():
    """Create.opp config fixture."""
    return {DOMAIN: {"dsn": "http://public@sentry.local/1"}}
