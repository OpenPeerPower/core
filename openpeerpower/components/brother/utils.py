"""Brother helpers functions."""
import logging

import pysnmp.hlapi.asyncio as hlapi
from pysnmp.hlapi.asyncio.cmdgen import lcd

from openpeerpower.const import EVENT_OPENPEERPOWER_STOP
from openpeerpower.core import callback
from openpeerpower.helpers import singleton

from .const import DOMAIN, SNMP

_LOGGER = logging.getLogger(__name__)


@singleton.singleton("snmp_engine")
def get_snmp_engine(opp):
    """Get SNMP engine."""
    _LOGGER.debug("Creating SNMP engine")
    snmp_engine = hlapi.SnmpEngine()

    @callback
    def shutdown_listener(ev):
        if opp.data.get(DOMAIN):
            _LOGGER.debug("Unconfiguring SNMP engine")
            lcd.unconfigure(opp.data[DOMAIN][SNMP], None)

    opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, shutdown_listener)

    return snmp_engine
