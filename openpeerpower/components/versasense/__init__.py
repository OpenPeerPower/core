"""Support for VersaSense MicroPnP devices."""
import logging

import pyversasense as pyv
import voluptuous as vol

from openpeerpower.const import CONF_HOST
from openpeerpower.helpers import aiohttp_client
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.discovery import async_load_platform

from .const import (
    KEY_CONSUMER,
    KEY_IDENTIFIER,
    KEY_MEASUREMENT,
    KEY_PARENT_MAC,
    KEY_PARENT_NAME,
    KEY_UNIT,
    PERIPHERAL_CLASS_SENSOR,
    PERIPHERAL_CLASS_SENSOR_ACTUATOR,
)

_LOGGER = logging.getLogger(__name__)

DOMAIN = "versasense"

# Validation of the user's configuration
CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Required(CONF_HOST): cv.string})}, extra=vol.ALLOW_EXTRA
)


async def async_setup.opp, config):
    """Set up the versasense component."""
    session = aiohttp_client.async_get_clientsession.opp)
    consumer = pyv.Consumer(config[DOMAIN]["host"], session)

   .opp.data[DOMAIN] = {KEY_CONSUMER: consumer}

    await _configure_entities.opp, config, consumer)

    # Return boolean to indicate that initialization was successful.
    return True


async def _configure_entities.opp, config, consumer):
    """Fetch all devices with their peripherals for representation."""
    devices = await consumer.fetchDevices()
    _LOGGER.debug(devices)

    sensor_info_list = []
    switch_info_list = []

    for mac, device in devices.items():
        _LOGGER.info("Device connected: %s %s", device.name, mac)
       .opp.data[DOMAIN][mac] = {}

        for peripheral_id, peripheral in device.peripherals.items():
           .opp.data[DOMAIN][mac][peripheral_id] = peripheral

            if peripheral.classification == PERIPHERAL_CLASS_SENSOR:
                sensor_info_list = _add_entity_info_to_list(
                    peripheral, device, sensor_info_list
                )
            elif peripheral.classification == PERIPHERAL_CLASS_SENSOR_ACTUATOR:
                switch_info_list = _add_entity_info_to_list(
                    peripheral, device, switch_info_list
                )

    if sensor_info_list:
        _load_platform.opp, config, "sensor", sensor_info_list)

    if switch_info_list:
        _load_platform.opp, config, "switch", switch_info_list)


def _add_entity_info_to_list(peripheral, device, entity_info_list):
    """Add info from a peripheral to specified list."""
    for measurement in peripheral.measurements:
        entity_info = {
            KEY_IDENTIFIER: peripheral.identifier,
            KEY_UNIT: measurement.unit,
            KEY_MEASUREMENT: measurement.name,
            KEY_PARENT_NAME: device.name,
            KEY_PARENT_MAC: device.mac,
        }

        entity_info_list.append(entity_info)

    return entity_info_list


def _load_platform.opp, config, entity_type, entity_info_list):
    """Load platform with list of entity info."""
   .opp.async_create_task(
        async_load_platform.opp, entity_type, DOMAIN, entity_info_list, config)
    )
