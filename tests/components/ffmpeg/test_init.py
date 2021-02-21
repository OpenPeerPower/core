"""The tests for Open Peer Power ffmpeg."""
from unittest.mock import MagicMock

import openpeerpower.components.ffmpeg as ffmpeg
from openpeerpower.components.ffmpeg import (
    DOMAIN,
    SERVICE_RESTART,
    SERVICE_START,
    SERVICE_STOP,
)
from openpeerpower.const import ATTR_ENTITY_ID
from openpeerpowerr.core import callback
from openpeerpowerr.setup import async_setup_component, setup_component

from tests.common import assert_setup_component, get_test_home_assistant


@callback
def async_start.opp, entity_id=None):
    """Start a FFmpeg process on entity.

    This is a legacy helper method. Do not use it for new tests.
    """
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else {}
   .opp.async_add_job.opp.services.async_call(DOMAIN, SERVICE_START, data))


@callback
def async_stop.opp, entity_id=None):
    """Stop a FFmpeg process on entity.

    This is a legacy helper method. Do not use it for new tests.
    """
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else {}
   .opp.async_add_job.opp.services.async_call(DOMAIN, SERVICE_STOP, data))


@callback
def async_restart.opp, entity_id=None):
    """Restart a FFmpeg process on entity.

    This is a legacy helper method. Do not use it for new tests.
    """
    data = {ATTR_ENTITY_ID: entity_id} if entity_id else {}
   .opp.async_add_job.opp.services.async_call(DOMAIN, SERVICE_RESTART, data))


class MockFFmpegDev(ffmpeg.FFmpegBase):
    """FFmpeg device mock."""

    def __init__(self,.opp, initial_state=True, entity_id="test.ffmpeg_device"):
        """Initialize mock."""
        super().__init__(initial_state)

        self.opp = opp
        self.entity_id = entity_id
        self.ffmpeg = MagicMock
        self.called_stop = False
        self.called_start = False
        self.called_restart = False
        self.called_entities = None

    async def _async_start_ffmpeg(self, entity_ids):
        """Mock start."""
        self.called_start = True
        self.called_entities = entity_ids

    async def _async_stop_ffmpeg(self, entity_ids):
        """Mock stop."""
        self.called_stop = True
        self.called_entities = entity_ids


class TestFFmpegSetup:
    """Test class for ffmpeg."""

    def setup_method(self):
        """Set up things to be run when tests are started."""
        self.opp = get_test_home_assistant()

    def teardown_method(self):
        """Stop everything that was started."""
        self.opp.stop()

    def test_setup_component(self):
        """Set up ffmpeg component."""
        with assert_setup_component(1):
            setup_component(self.opp, ffmpeg.DOMAIN, {ffmpeg.DOMAIN: {}})

        assert self.opp.data[ffmpeg.DATA_FFMPEG].binary == "ffmpeg"

    def test_setup_component_test_service(self):
        """Set up ffmpeg component test services."""
        with assert_setup_component(1):
            setup_component(self.opp, ffmpeg.DOMAIN, {ffmpeg.DOMAIN: {}})

        assert self.opp.services.has_service(ffmpeg.DOMAIN, "start")
        assert self.opp.services.has_service(ffmpeg.DOMAIN, "stop")
        assert self.opp.services.has_service(ffmpeg.DOMAIN, "restart")


async def test_setup_component_test_register.opp):
    """Set up ffmpeg component test register."""
    with assert_setup_component(1):
        await async_setup_component.opp, ffmpeg.DOMAIN, {ffmpeg.DOMAIN: {}})

   .opp.bus.async_listen_once = MagicMock()
    ffmpeg_dev = MockFFmpegDev.opp)
    await ffmpeg_dev.async_added_to_opp()

    assert.opp.bus.async_listen_once.called
    assert.opp.bus.async_listen_once.call_count == 2


async def test_setup_component_test_register_no_startup.opp):
    """Set up ffmpeg component test register without startup."""
    with assert_setup_component(1):
        await async_setup_component.opp, ffmpeg.DOMAIN, {ffmpeg.DOMAIN: {}})

   .opp.bus.async_listen_once = MagicMock()
    ffmpeg_dev = MockFFmpegDev.opp, False)
    await ffmpeg_dev.async_added_to_opp()

    assert.opp.bus.async_listen_once.called
    assert.opp.bus.async_listen_once.call_count == 1


async def test_setup_component_test_service_start.opp):
    """Set up ffmpeg component test service start."""
    with assert_setup_component(1):
        await async_setup_component.opp, ffmpeg.DOMAIN, {ffmpeg.DOMAIN: {}})

    ffmpeg_dev = MockFFmpegDev.opp, False)
    await ffmpeg_dev.async_added_to_opp()

    async_start.opp)
    await opp.async_block_till_done()

    assert ffmpeg_dev.called_start


async def test_setup_component_test_service_stop.opp):
    """Set up ffmpeg component test service stop."""
    with assert_setup_component(1):
        await async_setup_component.opp, ffmpeg.DOMAIN, {ffmpeg.DOMAIN: {}})

    ffmpeg_dev = MockFFmpegDev.opp, False)
    await ffmpeg_dev.async_added_to_opp()

    async_stop.opp)
    await opp.async_block_till_done()

    assert ffmpeg_dev.called_stop


async def test_setup_component_test_service_restart.opp):
    """Set up ffmpeg component test service restart."""
    with assert_setup_component(1):
        await async_setup_component.opp, ffmpeg.DOMAIN, {ffmpeg.DOMAIN: {}})

    ffmpeg_dev = MockFFmpegDev.opp, False)
    await ffmpeg_dev.async_added_to_opp()

    async_restart.opp)
    await opp.async_block_till_done()

    assert ffmpeg_dev.called_stop
    assert ffmpeg_dev.called_start


async def test_setup_component_test_service_start_with_entity.opp):
    """Set up ffmpeg component test service start."""
    with assert_setup_component(1):
        await async_setup_component.opp, ffmpeg.DOMAIN, {ffmpeg.DOMAIN: {}})

    ffmpeg_dev = MockFFmpegDev.opp, False)
    await ffmpeg_dev.async_added_to_opp()

    async_start.opp, "test.ffmpeg_device")
    await opp.async_block_till_done()

    assert ffmpeg_dev.called_start
    assert ffmpeg_dev.called_entities == ["test.ffmpeg_device"]
