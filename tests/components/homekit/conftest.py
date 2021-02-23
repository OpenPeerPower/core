"""HomeKit session fixtures."""
from unittest.mock import patch

from pyhap.accessory_driver import AccessoryDriver
import pytest

from openpeerpower.components.homekit.const import EVENT_HOMEKIT_CHANGED
from openpeerpower.core import callback as op_callback


@pytest.fixture
def hk_driver(loop):
    """Return a custom AccessoryDriver instance for HomeKit accessory init."""
    with patch("pyhap.accessory_driver.Zeroconf"), patch(
        "pyhap.accessory_driver.AccessoryEncoder"
    ), patch("pyhap.accessory_driver.HAPServer"), patch(
        "pyhap.accessory_driver.AccessoryDriver.publish"
    ), patch(
        "pyhap.accessory_driver.AccessoryDriver.persist"
    ):
        yield AccessoryDriver(pincode=b"123-45-678", address="127.0.0.1", loop=loop)


@pytest.fixture
def events.opp):
    """Yield caught homekit_changed events."""
    events = []
    opp.bus.async_listen(
        EVENT_HOMEKIT_CHANGED, op_callback(lambda e: events.append(e))
    )
    yield events
