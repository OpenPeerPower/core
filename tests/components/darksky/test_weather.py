"""The tests for the Dark Sky weather component."""
import re
import unittest
from unittest.mock import patch

import forecastio
from requests.exceptions import ConnectionError
import requests_mock

from openpeerpower.components import weather
from openpeerpower.setup import setup_component
from openpeerpower.util.unit_system import METRIC_SYSTEM

from tests.common import get_test_open_peer_power, load_fixture


class TestDarkSky(unittest.TestCase):
    """Test the Dark Sky weather component."""

    def setUp(self):
        """Set up things to be run when tests are started."""
        self opp =get_test_open_peer_power()
        self.opp.config.units = METRIC_SYSTEM
        self.lat = self.opp.config.latitude = 37.8267
        self.lon = self.opp.config.longitude = -122.423
        self.addCleanup(self.tear_down_cleanup)

    def tear_down_cleanup(self):
        """Stop down everything that was started."""
        self.opp.stop()

    @requests_mock.Mocker()
    @patch("forecastio.api.get_forecast", wraps=forecastio.api.get_forecast)
    def test_setup(self, mock_req, mock_get_forecast):
        """Test for successfully setting up the forecast.io platform."""
        uri = (
            r"https://api.(darksky.net|forecast.io)\/forecast\/(\w+)\/"
            r"(-?\d+\.?\d*),(-?\d+\.?\d*)"
        )
        mock_req.get(re.compile(uri), text=load_fixture("darksky.json"))

        assert setup_component(
            self.opp,
            weather.DOMAIN,
            {"weather": {"name": "test", "platform": "darksky", "api_key": "foo"}},
        )
        self.opp.block_till_done()

        assert mock_get_forecast.called
        assert mock_get_forecast.call_count == 1

        state = self.opp.states.get("weather.test")
        assert state.state == "sunny"

    @patch("forecastio.load_forecast", side_effect=ConnectionError())
    def test_failed_setup(self, mock_load_forecast):
        """Test to ensure that a network error does not break component state."""

        assert setup_component(
            self.opp,
            weather.DOMAIN,
            {"weather": {"name": "test", "platform": "darksky", "api_key": "foo"}},
        )
        self.opp.block_till_done()

        state = self.opp.states.get("weather.test")
        assert state.state == "unavailable"
