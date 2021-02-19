"""The tests for the openalpr cloud platform."""
import asyncio
from unittest.mock import PropertyMock, patch

from openpeerpower.components import camera, image_processing as ip
from openpeerpower.components.openalpr_cloud.image_processing import OPENALPR_API_URL
from openpeerpowerr.core import callback
from openpeerpowerr.setup import setup_component

from tests.common import assert_setup_component, get_test_home_assistant, load_fixture
from tests.components.image_processing import common


class TestOpenAlprCloudSetup:
    """Test class for image processing."""

    def setup_method(self):
        """Set up things to be run when tests are started."""
        self.opp = get_test_home_assistant()

    def teardown_method(self):
        """Stop everything that was started."""
        self.opp.stop()

    def test_setup_platform(self):
        """Set up platform with one entity."""
        config = {
            ip.DOMAIN: {
                "platform": "openalpr_cloud",
                "source": {"entity_id": "camera.demo_camera"},
                "region": "eu",
                "api_key": "sk_abcxyz123456",
            },
            "camera": {"platform": "demo"},
        }

        with assert_setup_component(1, ip.DOMAIN):
            setup_component(self.opp, ip.DOMAIN, config)
            self.opp.block_till_done()

        assert self.opp.states.get("image_processing.openalpr_demo_camera")

    def test_setup_platform_name(self):
        """Set up platform with one entity and set name."""
        config = {
            ip.DOMAIN: {
                "platform": "openalpr_cloud",
                "source": {"entity_id": "camera.demo_camera", "name": "test local"},
                "region": "eu",
                "api_key": "sk_abcxyz123456",
            },
            "camera": {"platform": "demo"},
        }

        with assert_setup_component(1, ip.DOMAIN):
            setup_component(self.opp, ip.DOMAIN, config)
            self.opp.block_till_done()

        assert self.opp.states.get("image_processing.test_local")

    def test_setup_platform_without_api_key(self):
        """Set up platform with one entity without api_key."""
        config = {
            ip.DOMAIN: {
                "platform": "openalpr_cloud",
                "source": {"entity_id": "camera.demo_camera"},
                "region": "eu",
            },
            "camera": {"platform": "demo"},
        }

        with assert_setup_component(0, ip.DOMAIN):
            setup_component(self.opp, ip.DOMAIN, config)

    def test_setup_platform_without_region(self):
        """Set up platform with one entity without region."""
        config = {
            ip.DOMAIN: {
                "platform": "openalpr_cloud",
                "source": {"entity_id": "camera.demo_camera"},
                "api_key": "sk_abcxyz123456",
            },
            "camera": {"platform": "demo"},
        }

        with assert_setup_component(0, ip.DOMAIN):
            setup_component(self.opp, ip.DOMAIN, config)


class TestOpenAlprCloud:
    """Test class for image processing."""

    def setup_method(self):
        """Set up things to be run when tests are started."""
        self.opp = get_test_home_assistant()

        config = {
            ip.DOMAIN: {
                "platform": "openalpr_cloud",
                "source": {"entity_id": "camera.demo_camera", "name": "test local"},
                "region": "eu",
                "api_key": "sk_abcxyz123456",
            },
            "camera": {"platform": "demo"},
        }

        with patch(
            "openpeerpower.components.openalpr_cloud.image_processing."
            "OpenAlprCloudEntity.should_poll",
            new_callable=PropertyMock(return_value=False),
        ):
            setup_component(self.opp, ip.DOMAIN, config)
            self.opp.block_till_done()

        self.alpr_events = []

        @callback
        def mock_alpr_event(event):
            """Mock event."""
            self.alpr_events.append(event)

        self.opp.bus.listen("image_processing.found_plate", mock_alpr_event)

        self.params = {
            "secret_key": "sk_abcxyz123456",
            "tasks": "plate",
            "return_image": 0,
            "country": "eu",
        }

    def teardown_method(self):
        """Stop everything that was started."""
        self.opp.stop()

    def test_openalpr_process_image(self, aioclient_mock):
        """Set up and scan a picture and test plates from event."""
        aioclient_mock.post(
            OPENALPR_API_URL,
            params=self.params,
            text=load_fixture("alpr_cloud.json"),
            status=200,
        )

        with patch(
            "openpeerpower.components.camera.async_get_image",
            return_value=camera.Image("image/jpeg", b"image"),
        ):
            common.scan(self.opp, entity_id="image_processing.test_local")
            self.opp.block_till_done()

        state = self.opp.states.get("image_processing.test_local")

        assert len(aioclient_mock.mock_calls) == 1
        assert len(self.alpr_events) == 5
        assert state.attributes.get("vehicles") == 1
        assert state.state == "H786P0J"

        event_data = [
            event.data
            for event in self.alpr_events
            if event.data.get("plate") == "H786P0J"
        ]
        assert len(event_data) == 1
        assert event_data[0]["plate"] == "H786P0J"
        assert event_data[0]["confidence"] == float(90.436699)
        assert event_data[0]["entity_id"] == "image_processing.test_local"

    def test_openalpr_process_image_api_error(self, aioclient_mock):
        """Set up and scan a picture and test api error."""
        aioclient_mock.post(
            OPENALPR_API_URL,
            params=self.params,
            text="{'error': 'error message'}",
            status=400,
        )

        with patch(
            "openpeerpower.components.camera.async_get_image",
            return_value=camera.Image("image/jpeg", b"image"),
        ):
            common.scan(self.opp, entity_id="image_processing.test_local")
            self.opp.block_till_done()

        assert len(aioclient_mock.mock_calls) == 1
        assert len(self.alpr_events) == 0

    def test_openalpr_process_image_api_timeout(self, aioclient_mock):
        """Set up and scan a picture and test api error."""
        aioclient_mock.post(
            OPENALPR_API_URL, params=self.params, exc=asyncio.TimeoutError()
        )

        with patch(
            "openpeerpower.components.camera.async_get_image",
            return_value=camera.Image("image/jpeg", b"image"),
        ):
            common.scan(self.opp, entity_id="image_processing.test_local")
            self.opp.block_till_done()

        assert len(aioclient_mock.mock_calls) == 1
        assert len(self.alpr_events) == 0
