"""Support for Luftdaten stations."""
import logging

from luftdaten import Luftdaten
from luftdaten.exceptions import LuftdatenError
import voluptuous as vol

from openpeerpower.config_entries import SOURCE_IMPORT
from openpeerpower.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONF_MONITORED_CONDITIONS,
    CONF_SCAN_INTERVAL,
    CONF_SENSORS,
    CONF_SHOW_ON_MAP,
    PERCENTAGE,
    PRESSURE_PA,
    TEMP_CELSIUS,
)
from openpeerpower.core import callback
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.dispatcher import async_dispatcher_send
from openpeerpower.helpers.event import async_track_time_interval

from .config_flow import configured_sensors, duplicate_stations
from .const import CONF_SENSOR_ID, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_LUFTDATEN = "luftdaten"
DATA_LUFTDATEN_CLIENT = "data_luftdaten_client"
DATA_LUFTDATEN_LISTENER = "data_luftdaten_listener"
DEFAULT_ATTRIBUTION = "Data provided by luftdaten.info"

SENSOR_HUMIDITY = "humidity"
SENSOR_PM10 = "P1"
SENSOR_PM2_5 = "P2"
SENSOR_PRESSURE = "pressure"
SENSOR_PRESSURE_AT_SEALEVEL = "pressure_at_sealevel"
SENSOR_TEMPERATURE = "temperature"

TOPIC_UPDATE = f"{DOMAIN}_data_update"

SENSORS = {
    SENSOR_TEMPERATURE: ["Temperature", "mdi:thermometer", TEMP_CELSIUS],
    SENSOR_HUMIDITY: ["Humidity", "mdi:water-percent", PERCENTAGE],
    SENSOR_PRESSURE: ["Pressure", "mdi:arrow-down-bold", PRESSURE_PA],
    SENSOR_PRESSURE_AT_SEALEVEL: ["Pressure at sealevel", "mdi:download", PRESSURE_PA],
    SENSOR_PM10: [
        "PM10",
        "mdi:thought-bubble",
        CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    ],
    SENSOR_PM2_5: [
        "PM2.5",
        "mdi:thought-bubble-outline",
        CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    ],
}

SENSOR_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_MONITORED_CONDITIONS, default=list(SENSORS)): vol.All(
            cv.ensure_list, [vol.In(SENSORS)]
        )
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_SENSOR_ID): cv.positive_int,
                vol.Optional(CONF_SENSORS, default={}): SENSOR_SCHEMA,
                vol.Optional(CONF_SHOW_ON_MAP, default=False): cv.boolean,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): cv.time_period,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


@callback
def _async_fixup_sensor_id(opp, config_entry, sensor_id):
    opp.config_entries.async_update_entry(
        config_entry, data={**config_entry.data, CONF_SENSOR_ID: int(sensor_id)}
    )


async def async_setup(opp, config):
    """Set up the Luftdaten component."""
    opp.data[DOMAIN] = {}
    opp.data[DOMAIN][DATA_LUFTDATEN_CLIENT] = {}
    opp.data[DOMAIN][DATA_LUFTDATEN_LISTENER] = {}

    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]
    station_id = conf[CONF_SENSOR_ID]

    if station_id not in configured_sensors(opp):
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data={
                    CONF_SENSORS: conf[CONF_SENSORS],
                    CONF_SENSOR_ID: conf[CONF_SENSOR_ID],
                    CONF_SHOW_ON_MAP: conf[CONF_SHOW_ON_MAP],
                },
            )
        )

    opp.data[DOMAIN][CONF_SCAN_INTERVAL] = conf[CONF_SCAN_INTERVAL]

    return True


async def async_setup_entry(opp, config_entry):
    """Set up Luftdaten as config entry."""

    if not isinstance(config_entry.data[CONF_SENSOR_ID], int):
        _async_fixup_sensor_id(opp, config_entry, config_entry.data[CONF_SENSOR_ID])

    if (
        config_entry.data[CONF_SENSOR_ID] in duplicate_stations(opp)
        and config_entry.source == SOURCE_IMPORT
    ):
        _LOGGER.warning(
            "Removing duplicate sensors for station %s",
            config_entry.data[CONF_SENSOR_ID],
        )
        opp.async_create_task(opp.config_entries.async_remove(config_entry.entry_id))
        return False

    session = async_get_clientsession(opp)

    try:
        luftdaten = LuftDatenData(
            Luftdaten(config_entry.data[CONF_SENSOR_ID], opp.loop, session),
            config_entry.data.get(CONF_SENSORS, {}).get(
                CONF_MONITORED_CONDITIONS, list(SENSORS)
            ),
        )
        await luftdaten.async_update()
        opp.data[DOMAIN][DATA_LUFTDATEN_CLIENT][config_entry.entry_id] = luftdaten
    except LuftdatenError as err:
        raise ConfigEntryNotReady from err

    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(config_entry, "sensor")
    )

    async def refresh_sensors(event_time):
        """Refresh Luftdaten data."""
        await luftdaten.async_update()
        async_dispatcher_send(opp, TOPIC_UPDATE)

    opp.data[DOMAIN][DATA_LUFTDATEN_LISTENER][
        config_entry.entry_id
    ] = async_track_time_interval(
        opp,
        refresh_sensors,
        opp.data[DOMAIN].get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )

    return True


async def async_unload_entry(opp, config_entry):
    """Unload an Luftdaten config entry."""
    remove_listener = opp.data[DOMAIN][DATA_LUFTDATEN_LISTENER].pop(
        config_entry.entry_id
    )
    remove_listener()

    opp.data[DOMAIN][DATA_LUFTDATEN_CLIENT].pop(config_entry.entry_id)

    return await opp.config_entries.async_forward_entry_unload(config_entry, "sensor")


class LuftDatenData:
    """Define a generic Luftdaten object."""

    def __init__(self, client, sensor_conditions):
        """Initialize the Luftdata object."""
        self.client = client
        self.data = {}
        self.sensor_conditions = sensor_conditions

    async def async_update(self):
        """Update sensor/binary sensor data."""
        try:
            await self.client.get_data()

            if self.client.values:
                self.data[DATA_LUFTDATEN] = self.client.values
                self.data[DATA_LUFTDATEN].update(self.client.meta)

        except LuftdatenError:
            _LOGGER.error("Unable to retrieve data from luftdaten.info")
