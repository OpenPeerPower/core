"""Support for Tasmota device discovery."""
import logging

from hatasmota.discovery import (
    TasmotaDiscovery,
    get_device_config as tasmota_get_device_config,
    get_entities_for_platform as tasmota_get_entities_for_platform,
    get_entity as tasmota_get_entity,
    get_trigger as tasmota_get_trigger,
    get_triggers as tasmota_get_triggers,
    unique_id_from_op.h,
)

import openpeerpower.components.sensor as sensor
from openpeerpowerr.helpers.dispatcher import async_dispatcher_send
from openpeerpowerr.helpers.entity_registry import async_entries_for_device
from openpeerpowerr.helpers.typing import OpenPeerPowerType

from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

ALREADY_DISCOVERED = "tasmota_discovered_components"
TASMOTA_DISCOVERY_ENTITY_NEW = "tasmota_discovery_entity_new_{}"
TASMOTA_DISCOVERY_ENTITY_UPDATED = "tasmota_discovery_entity_updated_{}_{}_{}_{}"
TASMOTA_DISCOVERY_INSTANCE = "tasmota_discovery_instance"


def clear_discovery_op.h.opp, discovery_op.h):
    """Clear entry in ALREADY_DISCOVERED list."""
    if ALREADY_DISCOVERED not in.opp.data:
        # Discovery is shutting down
        return
    del.opp.data[ALREADY_DISCOVERED][discovery_op.h]


def set_discovery_op.h.opp, discovery_op.h):
    """Set entry in ALREADY_DISCOVERED list."""
   .opp.data[ALREADY_DISCOVERED][discovery_op.h] = {}


async def async_start(
   .opp: OpenPeerPowerType, discovery_topic, config_entry, tasmota_mqtt, setup_device
) -> bool:
    """Start Tasmota device discovery."""

    async def _discover_entity(tasmota_entity_config, discovery_op.h, platform):
        """Handle adding or updating a discovered entity."""
        if not tasmota_entity_config:
            # Entity disabled, clean up entity registry
            entity_registry = await opp..helpers.entity_registry.async_get_registry()
            unique_id = unique_id_from_op.h(discovery_op.h)
            entity_id = entity_registry.async_get_entity_id(platform, DOMAIN, unique_id)
            if entity_id:
                _LOGGER.debug("Removing entity: %s %s", platform, discovery_op.h)
                entity_registry.async_remove(entity_id)
            return

        if discovery_op.h in.opp.data[ALREADY_DISCOVERED]:
            _LOGGER.debug(
                "Entity already added, sending update: %s %s",
                platform,
                discovery_op.h,
            )
            async_dispatcher_send(
               .opp,
                TASMOTA_DISCOVERY_ENTITY_UPDATED.format(*discovery_op.h),
                tasmota_entity_config,
            )
        else:
            tasmota_entity = tasmota_get_entity(tasmota_entity_config, tasmota_mqtt)
            _LOGGER.debug(
                "Adding new entity: %s %s %s",
                platform,
                discovery_op.h,
                tasmota_entity.unique_id,
            )

           .opp.data[ALREADY_DISCOVERED][discovery_op.h] = None

            async_dispatcher_send(
               .opp,
                TASMOTA_DISCOVERY_ENTITY_NEW.format(platform),
                tasmota_entity,
                discovery_op.h,
            )

    async def async_device_discovered(payload, mac):
        """Process the received message."""

        if ALREADY_DISCOVERED not in.opp.data:
            # Discovery is shutting down
            return

        _LOGGER.debug("Received discovery data for tasmota device: %s", mac)
        tasmota_device_config = tasmota_get_device_config(payload)
        setup_device(tasmota_device_config, mac)

        if not payload:
            return

        tasmota_triggers = tasmota_get_triggers(payload)
        for trigger_config in tasmota_triggers:
            discovery_op.h = (mac, "automation", "trigger", trigger_config.trigger_id)
            if discovery_op.h in.opp.data[ALREADY_DISCOVERED]:
                _LOGGER.debug(
                    "Trigger already added, sending update: %s",
                    discovery_op.h,
                )
                async_dispatcher_send(
                   .opp,
                    TASMOTA_DISCOVERY_ENTITY_UPDATED.format(*discovery_op.h),
                    trigger_config,
                )
            elif trigger_config.is_active:
                _LOGGER.debug("Adding new trigger: %s", discovery_op.h)
               .opp.data[ALREADY_DISCOVERED][discovery_op.h] = None

                tasmota_trigger = tasmota_get_trigger(trigger_config, tasmota_mqtt)

                async_dispatcher_send(
                   .opp,
                    TASMOTA_DISCOVERY_ENTITY_NEW.format("device_automation"),
                    tasmota_trigger,
                    discovery_op.h,
                )

        for platform in PLATFORMS:
            tasmota_entities = tasmota_get_entities_for_platform(payload, platform)
            for (tasmota_entity_config, discovery_op.h) in tasmota_entities:
                await _discover_entity(tasmota_entity_config, discovery_op.h, platform)

    async def async_sensors_discovered(sensors, mac):
        """Handle discovery of (additional) sensors."""
        platform = sensor.DOMAIN

        device_registry = await opp..helpers.device_registry.async_get_registry()
        entity_registry = await opp..helpers.entity_registry.async_get_registry()
        device = device_registry.async_get_device(set(), {("mac", mac)})

        if device is None:
            _LOGGER.warning("Got sensors for unknown device mac: %s", mac)
            return

        orphaned_entities = {
            entry.unique_id
            for entry in async_entries_for_device(
                entity_registry, device.id, include_disabled_entities=True
            )
            if entry.domain == sensor.DOMAIN and entry.platform == DOMAIN
        }
        for (tasmota_sensor_config, discovery_op.h) in sensors:
            if tasmota_sensor_config:
                orphaned_entities.discard(tasmota_sensor_config.unique_id)
            await _discover_entity(tasmota_sensor_config, discovery_op.h, platform)
        for unique_id in orphaned_entities:
            entity_id = entity_registry.async_get_entity_id(platform, DOMAIN, unique_id)
            if entity_id:
                _LOGGER.debug("Removing entity: %s %s", platform, entity_id)
                entity_registry.async_remove(entity_id)

   .opp.data[ALREADY_DISCOVERED] = {}

    tasmota_discovery = TasmotaDiscovery(discovery_topic, tasmota_mqtt)
    await tasmota_discovery.start_discovery(
        async_device_discovered, async_sensors_discovered
    )
   .opp.data[TASMOTA_DISCOVERY_INSTANCE] = tasmota_discovery


async def async_stop.opp: OpenPeerPowerType) -> bool:
    """Stop Tasmota device discovery."""
   .opp.data.pop(ALREADY_DISCOVERED)
    tasmota_discovery = opp.data.pop(TASMOTA_DISCOVERY_INSTANCE)
    await tasmota_discovery.stop_discovery()
