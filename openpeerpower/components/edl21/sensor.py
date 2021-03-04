"""Support for EDL21 Smart Meters."""

from datetime import timedelta
import logging

from sml import SmlGetListResponse
from sml.asyncio import SmlProtocol
import voluptuous as vol

from openpeerpower.components.sensor import PLATFORM_SCHEMA
from openpeerpower.const import CONF_NAME
from openpeerpower.core import callback
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from openpeerpower.helpers.entity import Entity
from openpeerpower.helpers.entity_registry import async_get_registry
from openpeerpower.helpers.typing import Optional
from openpeerpower.util.dt import utcnow

_LOGGER = logging.getLogger(__name__)

DOMAIN = "edl21"
CONF_SERIAL_PORT = "serial_port"
ICON_POWER = "mdi:flash"
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)
SIGNAL_EDL21_TELEGRAM = "edl21_telegram"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_SERIAL_PORT): cv.string,
        vol.Optional(CONF_NAME, default=""): cv.string,
    },
)


async def async_setup_platform(opp, config, async_add_entities, discovery_info=None):
    """Set up the EDL21 sensor."""
    opp.data[DOMAIN] = EDL21(opp, config, async_add_entities)
    await opp.data[DOMAIN].connect()


class EDL21:
    """EDL21 handles telegrams sent by a compatible smart meter."""

    # OBIS format: A-B:C.D.E*F
    _OBIS_NAMES = {
        # A=1: Electricity
        # C=0: General purpose objects
        "1-0:0.0.9*255": "Electricity ID",
        # C=1: Active power +
        # D=8: Time integral 1
        # E=0: Total
        "1-0:1.8.0*255": "Positive active energy total",
        # E=1: Rate 1
        "1-0:1.8.1*255": "Positive active energy in tariff T1",
        # E=2: Rate 2
        "1-0:1.8.2*255": "Positive active energy in tariff T2",
        # D=17: Time integral 7
        # E=0: Total
        "1-0:1.17.0*255": "Last signed positive active energy total",
        # C=2: Active power -
        # D=8: Time integral 1
        # E=0: Total
        "1-0:2.8.0*255": "Negative active energy total",
        # E=1: Rate 1
        "1-0:2.8.1*255": "Negative active energy in tariff T1",
        # E=2: Rate 2
        "1-0:2.8.2*255": "Negative active energy in tariff T2",
        # C=15: Active power absolute
        # D=7: Instantaneous value
        # E=0: Total
        "1-0:15.7.0*255": "Absolute active instantaneous power",
        # C=16: Active power sum
        # D=7: Instantaneous value
        # E=0: Total
        "1-0:16.7.0*255": "Sum active instantaneous power",
        # C=31: Active amperage L1
        # D=7: Instantaneous value
        # E=0: Total
        "1-0:31.7.0*255": "L1 active instantaneous amperage",
        # C=36: Active power L1
        # D=7: Instantaneous value
        # E=0: Total
        "1-0:36.7.0*255": "L1 active instantaneous power",
        # C=51: Active amperage L2
        # D=7: Instantaneous value
        # E=0: Total
        "1-0:51.7.0*255": "L2 active instantaneous amperage",
        # C=56: Active power L2
        # D=7: Instantaneous value
        # E=0: Total
        "1-0:56.7.0*255": "L2 active instantaneous power",
        # C=71: Active amperage L3
        # D=7: Instantaneous value
        # E=0: Total
        "1-0:71.7.0*255": "L3 active instantaneous amperage",
        # C=76: Active power L3
        # D=7: Instantaneous value
        # E=0: Total
        "1-0:76.7.0*255": "L3 active instantaneous power",
        # C=96: Electricity-related service entries
        "1-0:96.1.0*255": "Metering point ID 1",
    }
    _OBIS_BLACKLIST = {
        # C=96: Electricity-related service entries
        "1-0:96.50.1*1",  # Manufacturer specific
        # A=129: Manufacturer specific
        "129-129:199.130.3*255",  # Iskraemeco: Manufacturer
        "129-129:199.130.5*255",  # Iskraemeco: Public Key
    }

    def __init__(self, opp, config, async_add_entities) -> None:
        """Initialize an EDL21 object."""
        self._registered_obis = set()
        self._opp = opp
        self._async_add_entities = async_add_entities
        self._name = config[CONF_NAME]
        self._proto = SmlProtocol(config[CONF_SERIAL_PORT])
        self._proto.add_listener(self.event, ["SmlGetListResponse"])

    async def connect(self):
        """Connect to an EDL21 reader."""
        await self._proto.connect(self._opp.loop)

    def event(self, message_body) -> None:
        """Handle events from pysml."""
        assert isinstance(message_body, SmlGetListResponse)

        electricity_id = None
        for telegram in message_body.get("valList", []):
            if telegram.get("objName") in ("1-0:0.0.9*255", "1-0:96.1.0*255"):
                electricity_id = telegram.get("value")
                break

        if electricity_id is None:
            return
        electricity_id = electricity_id.replace(" ", "")

        new_entities = []
        for telegram in message_body.get("valList", []):
            obis = telegram.get("objName")
            if not obis:
                continue

            if (electricity_id, obis) in self._registered_obis:
                async_dispatcher_send(
                    self._opp, SIGNAL_EDL21_TELEGRAM, electricity_id, telegram
                )
            else:
                name = self._OBIS_NAMES.get(obis)
                if name:
                    if self._name:
                        name = f"{self._name}: {name}"
                    new_entities.append(
                        EDL21Entity(electricity_id, obis, name, telegram)
                    )
                    self._registered_obis.add((electricity_id, obis))
                elif obis not in self._OBIS_BLACKLIST:
                    _LOGGER.warning(
                        "Unhandled sensor %s detected. Please report at "
                        'https://github.com/openpeerpower/core/issues?q=is%%3Aissue+label%%3A"integration%%3A+edl21"+',
                        obis,
                    )
                    self._OBIS_BLACKLIST.add(obis)

        if new_entities:
            self._opp.loop.create_task(self.add_entities(new_entities))

    async def add_entities(self, new_entities) -> None:
        """Migrate old unique IDs, then add entities to opp."""
        registry = await async_get_registry(self._opp)

        for entity in new_entities:
            old_entity_id = registry.async_get_entity_id(
                "sensor", DOMAIN, entity.old_unique_id
            )
            if old_entity_id is not None:
                _LOGGER.debug(
                    "Migrating unique_id from [%s] to [%s]",
                    entity.old_unique_id,
                    entity.unique_id,
                )
                if registry.async_get_entity_id("sensor", DOMAIN, entity.unique_id):
                    registry.async_remove(old_entity_id)
                else:
                    registry.async_update_entity(
                        old_entity_id, new_unique_id=entity.unique_id
                    )

        self._async_add_entities(new_entities, update_before_add=True)


class EDL21Entity(Entity):
    """Entity reading values from EDL21 telegram."""

    def __init__(self, electricity_id, obis, name, telegram):
        """Initialize an EDL21Entity."""
        self._electricity_id = electricity_id
        self._obis = obis
        self._name = name
        self._unique_id = f"{electricity_id}_{obis}"
        self._telegram = telegram
        self._min_time = MIN_TIME_BETWEEN_UPDATES
        self._last_update = utcnow()
        self._state_attrs = {
            "status": "status",
            "valTime": "val_time",
            "scaler": "scaler",
            "valueSignature": "value_signature",
        }
        self._async_remove_dispatcher = None

    async def async_added_to_opp(self):
        """Run when entity about to be added to opp."""

        @callback
        def handle_telegram(electricity_id, telegram):
            """Update attributes from last received telegram for this object."""
            if self._electricity_id != electricity_id:
                return
            if self._obis != telegram.get("objName"):
                return
            if self._telegram == telegram:
                return

            now = utcnow()
            if now - self._last_update < self._min_time:
                return

            self._telegram = telegram
            self._last_update = now
            self.async_write_op_state()

        self._async_remove_dispatcher = async_dispatcher_connect(
            self.opp, SIGNAL_EDL21_TELEGRAM, handle_telegram
        )

    async def async_will_remove_from_opp(self):
        """Run when entity will be removed from opp."""
        if self._async_remove_dispatcher:
            self._async_remove_dispatcher()

    @property
    def should_poll(self) -> bool:
        """Do not poll."""
        return False

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id

    @property
    def old_unique_id(self) -> str:
        """Return a less unique ID as used in the first version of edl21."""
        return self._obis

    @property
    def name(self) -> Optional[str]:
        """Return a name."""
        return self._name

    @property
    def state(self) -> str:
        """Return the value of the last received telegram."""
        return self._telegram.get("value")

    @property
    def device_state_attributes(self):
        """Enumerate supported attributes."""
        return {
            self._state_attrs[k]: v
            for k, v in self._telegram.items()
            if k in self._state_attrs
        }

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._telegram.get("unit")

    @property
    def icon(self):
        """Return an icon."""
        return ICON_POWER
