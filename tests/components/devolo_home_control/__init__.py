"""Tests for the devolo_home_control integration."""

from openpeerpower.components.devolo_home_control.const import DOMAIN
from openpeerpower.core import OpenPeerPower

from tests.common import MockConfigEntry


def configure_integration(opp: OpenPeerPower) -> MockConfigEntry:
    """Configure the integration."""
    config = {
        "username": "test-username",
        "password": "test-password",
        "mydevolo_url": "https://test_mydevolo_url.test",
    }
    entry = MockConfigEntry(domain=DOMAIN, data=config, unique_id="123456")
    entry.add_to_opp(opp)

    return entry
