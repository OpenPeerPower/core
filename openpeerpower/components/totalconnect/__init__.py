"""The totalconnect component."""
from total_connect_client import TotalConnectClient

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_PASSWORD, CONF_USERNAME
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryAuthFailed
import openpeerpower.helpers.config_validation as cv

from .const import CONF_USERCODES, DOMAIN

PLATFORMS = ["alarm_control_panel", "binary_sensor"]

CONFIG_SCHEMA = cv.deprecated(DOMAIN)


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up upon config entry in user interface."""
    conf = entry.data
    username = conf[CONF_USERNAME]
    password = conf[CONF_PASSWORD]

    if CONF_USERCODES not in conf:
        # should only happen for those who used UI before we added usercodes
        raise ConfigEntryAuthFailed("No usercodes in TotalConnect configuration")

    temp_codes = conf[CONF_USERCODES]
    usercodes = {int(code): temp_codes[code] for code in temp_codes}
    client = await opp.async_add_executor_job(
        TotalConnectClient.TotalConnectClient, username, password, usercodes
    )

    if not client.is_valid_credentials():
        raise ConfigEntryAuthFailed("TotalConnect authentication failed")

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = client

    opp.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(opp, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await opp.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
