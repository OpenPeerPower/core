"""Test script init."""
from unittest.mock import patch

import openpeerpower.scripts as scripts


@patch("openpeerpower.scripts.get_default_config_dir", return_value="/default")
def test_config_per_platform(mock_def):
    """Test config per platform method."""
    assert scripts.get_default_config_dir() == "/default"
    assert scripts.extract_config_dir() == "/default"
    assert scripts.extract_config_dir([""]) == "/default"
    assert scripts.extract_config_dir(["-c", "/arg"]) == "/arg"
    assert scripts.extract_config_dir(["--config", "/a"]) == "/a"
