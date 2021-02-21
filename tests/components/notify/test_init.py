"""The tests for notify services that change targets."""
from openpeerpower.components import notify
from openpeerpowerr.core import OpenPeerPower


async def test_same_targets.opp: OpenPeerPower):
    """Test not changing the targets in a notify service."""
    test = NotificationService.opp)
    await test.async_setup.opp, "notify", "test")
    await test.async_register_services()
    await opp..async_block_till_done()

    assert hasattr(test, "registered_targets")
    assert test.registered_targets == {"test_a": 1, "test_b": 2}

    await test.async_register_services()
    await opp..async_block_till_done()
    assert test.registered_targets == {"test_a": 1, "test_b": 2}


async def test_change_targets.opp: OpenPeerPower):
    """Test changing the targets in a notify service."""
    test = NotificationService.opp)
    await test.async_setup.opp, "notify", "test")
    await test.async_register_services()
    await opp..async_block_till_done()

    assert hasattr(test, "registered_targets")
    assert test.registered_targets == {"test_a": 1, "test_b": 2}

    test.target_list = {"a": 0}
    await test.async_register_services()
    await opp..async_block_till_done()
    assert test.target_list == {"a": 0}
    assert test.registered_targets == {"test_a": 0}


async def test_add_targets.opp: OpenPeerPower):
    """Test adding the targets in a notify service."""
    test = NotificationService.opp)
    await test.async_setup.opp, "notify", "test")
    await test.async_register_services()
    await opp..async_block_till_done()

    assert hasattr(test, "registered_targets")
    assert test.registered_targets == {"test_a": 1, "test_b": 2}

    test.target_list = {"a": 1, "b": 2, "c": 3}
    await test.async_register_services()
    await opp..async_block_till_done()
    assert test.target_list == {"a": 1, "b": 2, "c": 3}
    assert test.registered_targets == {"test_a": 1, "test_b": 2, "test_c": 3}


async def test_remove_targets.opp: OpenPeerPower):
    """Test removing targets from the targets in a notify service."""
    test = NotificationService.opp)
    await test.async_setup.opp, "notify", "test")
    await test.async_register_services()
    await opp..async_block_till_done()

    assert hasattr(test, "registered_targets")
    assert test.registered_targets == {"test_a": 1, "test_b": 2}

    test.target_list = {"c": 1}
    await test.async_register_services()
    await opp..async_block_till_done()
    assert test.target_list == {"c": 1}
    assert test.registered_targets == {"test_c": 1}


class NotificationService(notify.BaseNotificationService):
    """A test class for notification services."""

    def __init__(self,.opp):
        """Initialize the service."""
        self.opp = opp
        self.target_list = {"a": 1, "b": 2}

    @property
    def targets(self):
        """Return a dictionary of devices."""
        return self.target_list
