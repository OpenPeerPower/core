"""Test helpers for Freebox."""
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def mock_path():
    """Mock path lib."""
    with patch("openpeerpower.components.freebox.router.Path"):
        yield
