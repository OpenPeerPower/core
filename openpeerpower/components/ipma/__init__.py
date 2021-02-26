"""Component for the Portuguese weather service - IPMA."""
from openpeerpower.core import Config, OpenPeerPower

from .config_flow import IpmaFlowHandler  # noqa: F401
from .const import DOMAIN  # noqa: F401

DEFAULT_NAME = "ipma"


async def async_setup(opp: OpenPeerPower, config: Config) -> bool:
    """Set up configured IPMA."""
    return True


async def async_setup_entry(opp, config_entry):
    """Set up IPMA station as config entry."""
    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(config_entry, "weather")
    )
    return True


async def async_unload_entry(opp, config_entry):
    """Unload a config entry."""
    await opp.config_entries.async_forward_entry_unload(config_entry, "weather")
    return True
