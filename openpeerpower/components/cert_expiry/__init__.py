"""The cert_expiry component."""
from datetime import datetime, timedelta
import logging
from typing import Optional

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_HOST, CONF_PORT
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.typing import OpenPeerPowerType
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_PORT, DOMAIN
from .errors import TemporaryFailure, ValidationFailure
from .helper import get_cert_expiry_timestamp

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(hours=12)


async def async_setup(opp, config):
    """Platform setup, do nothing."""
    return True


async def async_setup_entry(opp: OpenPeerPowerType, entry: ConfigEntry):
    """Load the saved entities."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]

    coordinator = CertExpiryDataUpdateCoordinator(opp, host, port)
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = coordinator

    if entry.unique_id is None:
        opp.config_entries.async_update_entry(entry, unique_id=f"{host}:{port}")

    opp.async_create_task(opp.config_entries.async_forward_entry_setup(entry, "sensor"))
    return True


async def async_unload_entry(opp, entry):
    """Unload a config entry."""
    return await opp.config_entries.async_forward_entry_unload(entry, "sensor")


class CertExpiryDataUpdateCoordinator(DataUpdateCoordinator[datetime]):
    """Class to manage fetching Cert Expiry data from single endpoint."""

    def __init__(self, opp, host, port):
        """Initialize global Cert Expiry data updater."""
        self.host = host
        self.port = port
        self.cert_error = None
        self.is_cert_valid = False

        display_port = f":{port}" if port != DEFAULT_PORT else ""
        name = f"{self.host}{display_port}"

        super().__init__(
            opp,
            _LOGGER,
            name=name,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> Optional[datetime]:
        """Fetch certificate."""
        try:
            timestamp = await get_cert_expiry_timestamp(self.opp, self.host, self.port)
        except TemporaryFailure as err:
            raise UpdateFailed(err.args[0]) from err
        except ValidationFailure as err:
            self.cert_error = err
            self.is_cert_valid = False
            _LOGGER.error("Certificate validation error: %s [%s]", self.host, err)
            return None

        self.cert_error = None
        self.is_cert_valid = True
        return timestamp
