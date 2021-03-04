"""Counter for the days until an HTTPS (TLS) certificate will expire."""
from datetime import timedelta

import voluptuous as vol

from openpeerpower.components.sensor import PLATFORM_SCHEMA
from openpeerpower.config_entries import SOURCE_IMPORT
from openpeerpower.const import (
    CONF_HOST,
    CONF_PORT,
    DEVICE_CLASS_TIMESTAMP,
    EVENT_OPENPEERPOWER_START,
)
from openpeerpower.core import callback
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.event import async_call_later
from openpeerpower.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_PORT, DOMAIN

SCAN_INTERVAL = timedelta(hours=12)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    }
)


async def async_setup_platform(opp, config, async_add_entities, discovery_info=None):
    """Set up certificate expiry sensor."""

    @callback
    def schedule_import(_):
        """Schedule delayed import after OP is fully started."""
        async_call_later(opp, 10, do_import)

    @callback
    def do_import(_):
        """Process YAML import."""
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=dict(config)
            )
        )

    opp.bus.async_listen_once(EVENT_OPENPEERPOWER_START, schedule_import)


async def async_setup_entry(opp, entry, async_add_entities):
    """Add cert-expiry entry."""
    coordinator = opp.data[DOMAIN][entry.entry_id]

    sensors = [
        SSLCertificateTimestamp(coordinator),
    ]

    async_add_entities(sensors, True)


class CertExpiryEntity(CoordinatorEntity):
    """Defines a base Cert Expiry entity."""

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return "mdi:certificate"

    @property
    def device_state_attributes(self):
        """Return additional sensor state attributes."""
        return {
            "is_valid": self.coordinator.is_cert_valid,
            "error": str(self.coordinator.cert_error),
        }


class SSLCertificateTimestamp(CertExpiryEntity):
    """Implementation of the Cert Expiry timestamp sensor."""

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return DEVICE_CLASS_TIMESTAMP

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"Cert Expiry Timestamp ({self.coordinator.name})"

    @property
    def state(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.isoformat()
        return None

    @property
    def unique_id(self):
        """Return a unique id for the sensor."""
        return f"{self.coordinator.host}:{self.coordinator.port}-timestamp"
