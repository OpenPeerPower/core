"""Test integration platform helpers."""
from unittest.mock import Mock

from openpeerpowerr.setup import ATTR_COMPONENT, EVENT_COMPONENT_LOADED

from tests.common import mock_platform


async def test_process_integration_platforms.opp):
    """Test processing integrations."""
    loaded_platform = Mock()
    mock_platform.opp, "loaded.platform_to_check", loaded_platform)
   .opp.config.components.add("loaded")

    event_platform = Mock()
    mock_platform.opp, "event.platform_to_check", event_platform)

    processed = []

    async def _process_platform.opp, domain, platform):
        """Process platform."""
        processed.append((domain, platform))

    await opp..helpers.integration_platform.async_process_integration_platforms(
        "platform_to_check", _process_platform
    )

    assert len(processed) == 1
    assert processed[0][0] == "loaded"
    assert processed[0][1] == loaded_platform

   .opp.bus.async_fire(EVENT_COMPONENT_LOADED, {ATTR_COMPONENT: "event"})
    await opp..async_block_till_done()

    assert len(processed) == 2
    assert processed[1][0] == "event"
    assert processed[1][1] == event_platform
