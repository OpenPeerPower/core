"""The tests for the folder_watcher component."""
import os
from unittest.mock import Mock, patch

from openpeerpower.components import folder_watcher
from openpeerpower.setup import async_setup_component


async def test_invalid_path_setup.opp):
    """Test that an invalid path is not set up."""
    assert not await async_setup_component(
       .opp,
        folder_watcher.DOMAIN,
        {folder_watcher.DOMAIN: {folder_watcher.CONF_FOLDER: "invalid_path"}},
    )


async def test_valid_path_setup.opp):
    """Test that a valid path is setup."""
    cwd = os.path.join(os.path.dirname(__file__))
   .opp.config.allowlist_external_dirs = {cwd}
    with patch.object(folder_watcher, "Watcher"):
        assert await async_setup_component(
           .opp,
            folder_watcher.DOMAIN,
            {folder_watcher.DOMAIN: {folder_watcher.CONF_FOLDER: cwd}},
        )


def test_event():
    """Check that Open Peer Power events are fired correctly on watchdog event."""

    class MockPatternMatchingEventHandler:
        """Mock base class for the pattern matcher event handler."""

        def __init__(self, patterns):
            pass

    with patch(
        "openpeerpower.components.folder_watcher.PatternMatchingEventHandler",
        MockPatternMatchingEventHandler,
    ):
       .opp = Mock()
        handler = folder_watcher.create_event_handler(["*"],.opp)
        handler.on_created(
            Mock(is_directory=False, src_path="/hello/world.txt", event_type="created")
        )
        assert.opp.bus.fire.called
        assert.opp.bus.fire.mock_calls[0][1][0] == folder_watcher.DOMAIN
        assert.opp.bus.fire.mock_calls[0][1][1] == {
            "event_type": "created",
            "path": "/hello/world.txt",
            "file": "world.txt",
            "folder": "/hello",
        }
