"""Component to embed Google Cast."""
from openpeerpower import config_entries

from . import open_peer_power_cast
from .const import DOMAIN


async def async_setup(opp, config):
    """Set up the Cast component."""
    conf = config.get(DOMAIN)

    opp.data[DOMAIN] = conf or {}

    if conf is not None:
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_IMPORT}
            )
        )

    return True


async def async_setup_entry(opp, entry: config_entries.ConfigEntry):
    """Set up Cast from a config entry."""
    await open_peer_power_cast.async_setup_op_cast(opp, entry)

    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(entry, "media_player")
    )
    return True


async def async_remove_entry(opp, entry):
    """Remove Open Peer Power Cast user."""
    await open_peer_power_cast.async_remove_user(opp, entry)
