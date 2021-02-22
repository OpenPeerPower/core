"""Provide a mock package component."""
from .const import TEST  # noqa: F401

DOMAIN = "test_package"


async def async_setup(opp, config):
    """Mock a successful setup."""
    return True
