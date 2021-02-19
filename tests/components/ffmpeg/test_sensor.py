"""The tests for Home Assistant ffmpeg binary sensor."""
from unittest.mock import patch

from openpeerpowerr.setup import setup_component

from tests.common import assert_setup_component, get_test_home_assistant, mock_coro


class TestFFmpegNoiseSetup:
    """Test class for ffmpeg."""

    def setup_method(self):
        """Set up things to be run when tests are started."""
        self.opp = get_test_home_assistant()

        self.config = {
            "binary_sensor": {"platform": "ffmpeg_noise", "input": "testinputvideo"}
        }

    def teardown_method(self):
        """Stop everything that was started."""
        self.opp.stop()

    def test_setup_component(self):
        """Set up ffmpeg component."""
        with assert_setup_component(1, "binary_sensor"):
            setup_component(self.opp, "binary_sensor", self.config)
        self.opp.block_till_done()

        assert self.opp.data["ffmpeg"].binary == "ffmpeg"
        assert self.opp.states.get("binary_sensor.ffmpeg_noise") is not None

    @patch("haffmpeg.sensor.SensorNoise.open_sensor", return_value=mock_coro())
    def test_setup_component_start(self, mock_start):
        """Set up ffmpeg component."""
        with assert_setup_component(1, "binary_sensor"):
            setup_component(self.opp, "binary_sensor", self.config)
        self.opp.block_till_done()

        assert self.opp.data["ffmpeg"].binary == "ffmpeg"
        assert self.opp.states.get("binary_sensor.ffmpeg_noise") is not None

        self.opp.start()
        assert mock_start.called

        entity = self.opp.states.get("binary_sensor.ffmpeg_noise")
        assert entity.state == "unavailable"

    @patch("haffmpeg.sensor.SensorNoise")
    def test_setup_component_start_callback(self, mock_ffmpeg):
        """Set up ffmpeg component."""
        with assert_setup_component(1, "binary_sensor"):
            setup_component(self.opp, "binary_sensor", self.config)
        self.opp.block_till_done()

        assert self.opp.data["ffmpeg"].binary == "ffmpeg"
        assert self.opp.states.get("binary_sensor.ffmpeg_noise") is not None

        self.opp.start()

        entity = self.opp.states.get("binary_sensor.ffmpeg_noise")
        assert entity.state == "off"

        self.opp.add_job(mock_ffmpeg.call_args[0][1], True)
        self.opp.block_till_done()

        entity = self.opp.states.get("binary_sensor.ffmpeg_noise")
        assert entity.state == "on"


class TestFFmpegMotionSetup:
    """Test class for ffmpeg."""

    def setup_method(self):
        """Set up things to be run when tests are started."""
        self.opp = get_test_home_assistant()

        self.config = {
            "binary_sensor": {"platform": "ffmpeg_motion", "input": "testinputvideo"}
        }

    def teardown_method(self):
        """Stop everything that was started."""
        self.opp.stop()

    def test_setup_component(self):
        """Set up ffmpeg component."""
        with assert_setup_component(1, "binary_sensor"):
            setup_component(self.opp, "binary_sensor", self.config)
        self.opp.block_till_done()

        assert self.opp.data["ffmpeg"].binary == "ffmpeg"
        assert self.opp.states.get("binary_sensor.ffmpeg_motion") is not None

    @patch("haffmpeg.sensor.SensorMotion.open_sensor", return_value=mock_coro())
    def test_setup_component_start(self, mock_start):
        """Set up ffmpeg component."""
        with assert_setup_component(1, "binary_sensor"):
            setup_component(self.opp, "binary_sensor", self.config)
        self.opp.block_till_done()

        assert self.opp.data["ffmpeg"].binary == "ffmpeg"
        assert self.opp.states.get("binary_sensor.ffmpeg_motion") is not None

        self.opp.start()
        assert mock_start.called

        entity = self.opp.states.get("binary_sensor.ffmpeg_motion")
        assert entity.state == "unavailable"

    @patch("haffmpeg.sensor.SensorMotion")
    def test_setup_component_start_callback(self, mock_ffmpeg):
        """Set up ffmpeg component."""
        with assert_setup_component(1, "binary_sensor"):
            setup_component(self.opp, "binary_sensor", self.config)
        self.opp.block_till_done()

        assert self.opp.data["ffmpeg"].binary == "ffmpeg"
        assert self.opp.states.get("binary_sensor.ffmpeg_motion") is not None

        self.opp.start()

        entity = self.opp.states.get("binary_sensor.ffmpeg_motion")
        assert entity.state == "off"

        self.opp.add_job(mock_ffmpeg.call_args[0][1], True)
        self.opp.block_till_done()

        entity = self.opp.states.get("binary_sensor.ffmpeg_motion")
        assert entity.state == "on"
