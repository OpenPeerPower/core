"""The tests for local file sensor platform."""
from unittest.mock import Mock, mock_open, patch

import pytest

from openpeerpower.const import STATE_UNKNOWN
from openpeerpower.setup import async_setup_component

from tests.common import mock_registry


@pytest.fixture
def entity_reg.opp):
    """Return an empty, loaded, registry."""
    return mock_registry.opp)


@patch("os.path.isfile", Mock(return_value=True))
@patch("os.access", Mock(return_value=True))
async def test_file_value.opp, entity_reg):
    """Test the File sensor."""
    config = {
        "sensor": {"platform": "file", "name": "file1", "file_path": "mock.file1"}
    }

    m_open = mock_open(read_data="43\n45\n21")
    with patch(
        "openpeerpower.components.file.sensor.open", m_open, create=True
    ), patch.object.opp.config, "is_allowed_path", return_value=True):
        assert await async_setup_component.opp, "sensor", config)
        await opp.async_block_till_done()

    state = opp.states.get("sensor.file1")
    assert state.state == "21"


@patch("os.path.isfile", Mock(return_value=True))
@patch("os.access", Mock(return_value=True))
async def test_file_value_template.opp, entity_reg):
    """Test the File sensor with JSON entries."""
    config = {
        "sensor": {
            "platform": "file",
            "name": "file2",
            "file_path": "mock.file2",
            "value_template": "{{ value_json.temperature }}",
        }
    }

    data = '{"temperature": 29, "humidity": 31}\n' '{"temperature": 26, "humidity": 36}'

    m_open = mock_open(read_data=data)
    with patch(
        "openpeerpower.components.file.sensor.open", m_open, create=True
    ), patch.object.opp.config, "is_allowed_path", return_value=True):
        assert await async_setup_component.opp, "sensor", config)
        await opp.async_block_till_done()

    state = opp.states.get("sensor.file2")
    assert state.state == "26"


@patch("os.path.isfile", Mock(return_value=True))
@patch("os.access", Mock(return_value=True))
async def test_file_empty.opp, entity_reg):
    """Test the File sensor with an empty file."""
    config = {"sensor": {"platform": "file", "name": "file3", "file_path": "mock.file"}}

    m_open = mock_open(read_data="")
    with patch(
        "openpeerpower.components.file.sensor.open", m_open, create=True
    ), patch.object.opp.config, "is_allowed_path", return_value=True):
        assert await async_setup_component.opp, "sensor", config)
        await opp.async_block_till_done()

    state = opp.states.get("sensor.file3")
    assert state.state == STATE_UNKNOWN
