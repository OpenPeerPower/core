"""Test the frame helper."""
from unittest.mock import Mock, patch

import pytest

from openpeerpower.helpers import frame


async def test_extract_frame_integration(caplog):
    """Test extracting the current frame from integration context."""
    correct_frame = Mock(
        filename="/home/paulus/openpeerpower/components/hue/light.py",
        lineno="23",
        line="self.light.is_on",
    )
    with patch(
        "openpeerpower.helpers.frame.extract_stack",
        return_value=[
            Mock(
                filename="/home/paulus/openpeerpower/core.py",
                lineno="23",
                line="do_something()",
            ),
            correct_frame,
            Mock(
                filename="/home/paulus/aiohue/lights.py",
                lineno="2",
                line="something()",
            ),
        ],
    ):
        found_frame, integration, path = frame.get_integration_frame()

    assert integration == "hue"
    assert path == "openpeerpower/components/"
    assert found_frame == correct_frame


async def test_extract_frame_integration_with_excluded_intergration(caplog):
    """Test extracting the current frame from integration context."""
    correct_frame = Mock(
        filename="/home/dev/openpeerpower/components/mdns/light.py",
        lineno="23",
        line="self.light.is_on",
    )
    with patch(
        "openpeerpower.helpers.frame.extract_stack",
        return_value=[
            Mock(
                filename="/home/dev/openpeerpower/core.py",
                lineno="23",
                line="do_something()",
            ),
            correct_frame,
            Mock(
                filename="/home/dev/openpeerpower/components/zeroconf/usage.py",
                lineno="23",
                line="self.light.is_on",
            ),
            Mock(
                filename="/home/dev/mdns/lights.py",
                lineno="2",
                line="something()",
            ),
        ],
    ):
        found_frame, integration, path = frame.get_integration_frame(
            exclude_integrations={"zeroconf"}
        )

    assert integration == "mdns"
    assert path == "openpeerpower/components/"
    assert found_frame == correct_frame


async def test_extract_frame_no_integration(caplog):
    """Test extracting the current frame without integration context."""
    with patch(
        "openpeerpower.helpers.frame.extract_stack",
        return_value=[
            Mock(
                filename="/home/paulus/openpeerpower/core.py",
                lineno="23",
                line="do_something()",
            ),
            Mock(
                filename="/home/paulus/aiohue/lights.py",
                lineno="2",
                line="something()",
            ),
        ],
    ), pytest.raises(frame.MissingIntegrationFrame):
        frame.get_integration_frame()
