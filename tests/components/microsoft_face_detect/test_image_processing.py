"""The tests for the microsoft face detect platform."""
from unittest.mock import PropertyMock, patch

import openpeerpower.components.image_processing as ip
import openpeerpower.components.microsoft_face as mf
from openpeerpower.const import ATTR_ENTITY_PICTURE
from openpeerpower.core import callback
from openpeerpower.setup import setup_component

from tests.common import (
    assert_setup_component,
    get_test_open_peer_power,
    load_fixture,
    mock_coro,
)
from tests.components.image_processing import common


class TestMicrosoftFaceDetectSetup:
    """Test class for image processing."""

    def setup_method(self):
        """Set up things to be run when tests are started."""
        self.opp = get_test_open_peer_power()

    def teardown_method(self):
        """Stop everything that was started."""
        self.opp.stop()

    @patch(
        "openpeerpower.components.microsoft_face.MicrosoftFace.update_store",
        return_value=mock_coro(),
    )
    def test_setup_platform(self, store_mock):
        """Set up platform with one entity."""
        config = {
            ip.DOMAIN: {
                "platform": "microsoft_face_detect",
                "source": {"entity_id": "camera.demo_camera"},
                "attributes": ["age", "gender"],
            },
            "camera": {"platform": "demo"},
            mf.DOMAIN: {"api_key": "12345678abcdef6"},
        }

        with assert_setup_component(1, ip.DOMAIN):
            setup_component(self.opp, ip.DOMAIN, config)
            self.opp.block_till_done()

        assert self.opp.states.get("image_processing.microsoftface_demo_camera")

    @patch(
        "openpeerpower.components.microsoft_face.MicrosoftFace.update_store",
        return_value=mock_coro(),
    )
    def test_setup_platform_name(self, store_mock):
        """Set up platform with one entity and set name."""
        config = {
            ip.DOMAIN: {
                "platform": "microsoft_face_detect",
                "source": {"entity_id": "camera.demo_camera", "name": "test local"},
            },
            "camera": {"platform": "demo"},
            mf.DOMAIN: {"api_key": "12345678abcdef6"},
        }

        with assert_setup_component(1, ip.DOMAIN):
            setup_component(self.opp, ip.DOMAIN, config)
            self.opp.block_till_done()

        assert self.opp.states.get("image_processing.test_local")


class TestMicrosoftFaceDetect:
    """Test class for image processing."""

    def setup_method(self):
        """Set up things to be run when tests are started."""
        self.opp = get_test_open_peer_power()

        self.config = {
            ip.DOMAIN: {
                "platform": "microsoft_face_detect",
                "source": {"entity_id": "camera.demo_camera", "name": "test local"},
                "attributes": ["age", "gender"],
            },
            "camera": {"platform": "demo"},
            mf.DOMAIN: {"api_key": "12345678abcdef6"},
        }

        self.endpoint_url = f"https://westus.{mf.FACE_API_URL}"

    def teardown_method(self):
        """Stop everything that was started."""
        self.opp.stop()

    @patch(
        "openpeerpower.components.microsoft_face_detect.image_processing."
        "MicrosoftFaceDetectEntity.should_poll",
        new_callable=PropertyMock(return_value=False),
    )
    def test_ms_detect_process_image(self, poll_mock, aioclient_mock):
        """Set up and scan a picture and test plates from event."""
        aioclient_mock.get(
            self.endpoint_url.format("persongroups"),
            text=load_fixture("microsoft_face_persongroups.json"),
        )
        aioclient_mock.get(
            self.endpoint_url.format("persongroups/test_group1/persons"),
            text=load_fixture("microsoft_face_persons.json"),
        )
        aioclient_mock.get(
            self.endpoint_url.format("persongroups/test_group2/persons"),
            text=load_fixture("microsoft_face_persons.json"),
        )

        setup_component(self.opp, ip.DOMAIN, self.config)
        self.opp.block_till_done()

        state = self.opp.states.get("camera.demo_camera")
        url = (
            f"{self.opp.config.internal_url}{state.attributes.get(ATTR_ENTITY_PICTURE)}"
        )

        face_events = []

        @callback
        def mock_face_event(event):
            """Mock event."""
            face_events.append(event)

        self.opp.bus.listen("image_processing.detect_face", mock_face_event)

        aioclient_mock.get(url, content=b"image")

        aioclient_mock.post(
            self.endpoint_url.format("detect"),
            text=load_fixture("microsoft_face_detect.json"),
            params={"returnFaceAttributes": "age,gender"},
        )

        common.scan(self.opp, entity_id="image_processing.test_local")
        self.opp.block_till_done()

        state = self.opp.states.get("image_processing.test_local")

        assert len(face_events) == 1
        assert state.attributes.get("total_faces") == 1
        assert state.state == "1"

        assert face_events[0].data["age"] == 71.0
        assert face_events[0].data["gender"] == "male"
        assert face_events[0].data["entity_id"] == "image_processing.test_local"

        # Test that later, if a request is made that results in no face
        # being detected, that this is reflected in the state object
        aioclient_mock.clear_requests()
        aioclient_mock.post(
            self.endpoint_url.format("detect"),
            text="[]",
            params={"returnFaceAttributes": "age,gender"},
        )

        common.scan(self.opp, entity_id="image_processing.test_local")
        self.opp.block_till_done()

        state = self.opp.states.get("image_processing.test_local")

        # No more face events were fired
        assert len(face_events) == 1
        # Total faces and actual qualified number of faces reset to zero
        assert state.attributes.get("total_faces") == 0
        assert state.state == "0"
