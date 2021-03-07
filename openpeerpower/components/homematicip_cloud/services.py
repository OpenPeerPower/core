"""Support for HomematicIP Cloud devices."""
import logging
from pathlib import Path
from typing import Optional

from homematicip.aio.device import AsyncSwitchMeasuring
from homematicip.aio.group import AsyncHeatingGroup
from homematicip.aio.home import AsyncHome
from homematicip.base.helpers import handle_config
import voluptuous as vol

from openpeerpower.const import ATTR_ENTITY_ID, ATTR_TEMPERATURE
import openpeerpower.helpers.config_validation as cv
from openpeerpower.helpers.config_validation import comp_entity_ids
from openpeerpower.helpers.service import (
    async_register_admin_service,
    verify_domain_control,
)
from openpeerpower.helpers.typing import OpenPeerPowerType, ServiceCallType

from .const import DOMAIN as HMIPC_DOMAIN

_LOGGER = logging.getLogger(__name__)

ATTR_ACCESSPOINT_ID = "accesspoint_id"
ATTR_ANONYMIZE = "anonymize"
ATTR_CLIMATE_PROFILE_INDEX = "climate_profile_index"
ATTR_CONFIG_OUTPUT_FILE_PREFIX = "config_output_file_prefix"
ATTR_CONFIG_OUTPUT_PATH = "config_output_path"
ATTR_DURATION = "duration"
ATTR_ENDTIME = "endtime"

DEFAULT_CONFIG_FILE_PREFIX = "hmip-config"

SERVICE_ACTIVATE_ECO_MODE_WITH_DURATION = "activate_eco_mode_with_duration"
SERVICE_ACTIVATE_ECO_MODE_WITH_PERIOD = "activate_eco_mode_with_period"
SERVICE_ACTIVATE_VACATION = "activate_vacation"
SERVICE_DEACTIVATE_ECO_MODE = "deactivate_eco_mode"
SERVICE_DEACTIVATE_VACATION = "deactivate_vacation"
SERVICE_DUMP_HAP_CONFIG = "dump_hap_config"
SERVICE_RESET_ENERGY_COUNTER = "reset_energy_counter"
SERVICE_SET_ACTIVE_CLIMATE_PROFILE = "set_active_climate_profile"

HMIPC_SERVICES = [
    SERVICE_ACTIVATE_ECO_MODE_WITH_DURATION,
    SERVICE_ACTIVATE_ECO_MODE_WITH_PERIOD,
    SERVICE_ACTIVATE_VACATION,
    SERVICE_DEACTIVATE_ECO_MODE,
    SERVICE_DEACTIVATE_VACATION,
    SERVICE_DUMP_HAP_CONFIG,
    SERVICE_RESET_ENERGY_COUNTER,
    SERVICE_SET_ACTIVE_CLIMATE_PROFILE,
]

SCHEMA_ACTIVATE_ECO_MODE_WITH_DURATION = vol.Schema(
    {
        vol.Required(ATTR_DURATION): cv.positive_int,
        vol.Optional(ATTR_ACCESSPOINT_ID): vol.All(str, vol.Length(min=24, max=24)),
    }
)

SCHEMA_ACTIVATE_ECO_MODE_WITH_PERIOD = vol.Schema(
    {
        vol.Required(ATTR_ENDTIME): cv.datetime,
        vol.Optional(ATTR_ACCESSPOINT_ID): vol.All(str, vol.Length(min=24, max=24)),
    }
)

SCHEMA_ACTIVATE_VACATION = vol.Schema(
    {
        vol.Required(ATTR_ENDTIME): cv.datetime,
        vol.Required(ATTR_TEMPERATURE, default=18.0): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=55)
        ),
        vol.Optional(ATTR_ACCESSPOINT_ID): vol.All(str, vol.Length(min=24, max=24)),
    }
)

SCHEMA_DEACTIVATE_ECO_MODE = vol.Schema(
    {vol.Optional(ATTR_ACCESSPOINT_ID): vol.All(str, vol.Length(min=24, max=24))}
)

SCHEMA_DEACTIVATE_VACATION = vol.Schema(
    {vol.Optional(ATTR_ACCESSPOINT_ID): vol.All(str, vol.Length(min=24, max=24))}
)

SCHEMA_SET_ACTIVE_CLIMATE_PROFILE = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): comp_entity_ids,
        vol.Required(ATTR_CLIMATE_PROFILE_INDEX): cv.positive_int,
    }
)

SCHEMA_DUMP_HAP_CONFIG = vol.Schema(
    {
        vol.Optional(ATTR_CONFIG_OUTPUT_PATH): cv.string,
        vol.Optional(
            ATTR_CONFIG_OUTPUT_FILE_PREFIX, default=DEFAULT_CONFIG_FILE_PREFIX
        ): cv.string,
        vol.Optional(ATTR_ANONYMIZE, default=True): cv.boolean,
    }
)

SCHEMA_RESET_ENERGY_COUNTER = vol.Schema(
    {vol.Required(ATTR_ENTITY_ID): comp_entity_ids}
)


async def async_setup_services(opp: OpenPeerPowerType) -> None:
    """Set up the HomematicIP Cloud services."""

    if opp.services.async_services().get(HMIPC_DOMAIN):
        return

    @verify_domain_control(opp, HMIPC_DOMAIN)
    async def async_call_hmipc_service(service: ServiceCallType):
        """Call correct HomematicIP Cloud service."""
        service_name = service.service

        if service_name == SERVICE_ACTIVATE_ECO_MODE_WITH_DURATION:
            await _async_activate_eco_mode_with_duration(opp, service)
        elif service_name == SERVICE_ACTIVATE_ECO_MODE_WITH_PERIOD:
            await _async_activate_eco_mode_with_period(opp, service)
        elif service_name == SERVICE_ACTIVATE_VACATION:
            await _async_activate_vacation(opp, service)
        elif service_name == SERVICE_DEACTIVATE_ECO_MODE:
            await _async_deactivate_eco_mode(opp, service)
        elif service_name == SERVICE_DEACTIVATE_VACATION:
            await _async_deactivate_vacation(opp, service)
        elif service_name == SERVICE_DUMP_HAP_CONFIG:
            await _async_dump_hap_config(opp, service)
        elif service_name == SERVICE_RESET_ENERGY_COUNTER:
            await _async_reset_energy_counter(opp, service)
        elif service_name == SERVICE_SET_ACTIVE_CLIMATE_PROFILE:
            await _set_active_climate_profile(opp, service)

    opp.services.async_register(
        domain=HMIPC_DOMAIN,
        service=SERVICE_ACTIVATE_ECO_MODE_WITH_DURATION,
        service_func=async_call_hmipc_service,
        schema=SCHEMA_ACTIVATE_ECO_MODE_WITH_DURATION,
    )

    opp.services.async_register(
        domain=HMIPC_DOMAIN,
        service=SERVICE_ACTIVATE_ECO_MODE_WITH_PERIOD,
        service_func=async_call_hmipc_service,
        schema=SCHEMA_ACTIVATE_ECO_MODE_WITH_PERIOD,
    )

    opp.services.async_register(
        domain=HMIPC_DOMAIN,
        service=SERVICE_ACTIVATE_VACATION,
        service_func=async_call_hmipc_service,
        schema=SCHEMA_ACTIVATE_VACATION,
    )

    opp.services.async_register(
        domain=HMIPC_DOMAIN,
        service=SERVICE_DEACTIVATE_ECO_MODE,
        service_func=async_call_hmipc_service,
        schema=SCHEMA_DEACTIVATE_ECO_MODE,
    )

    opp.services.async_register(
        domain=HMIPC_DOMAIN,
        service=SERVICE_DEACTIVATE_VACATION,
        service_func=async_call_hmipc_service,
        schema=SCHEMA_DEACTIVATE_VACATION,
    )

    opp.services.async_register(
        domain=HMIPC_DOMAIN,
        service=SERVICE_SET_ACTIVE_CLIMATE_PROFILE,
        service_func=async_call_hmipc_service,
        schema=SCHEMA_SET_ACTIVE_CLIMATE_PROFILE,
    )

    async_register_admin_service(
        opp=opp,
        domain=HMIPC_DOMAIN,
        service=SERVICE_DUMP_HAP_CONFIG,
        service_func=async_call_hmipc_service,
        schema=SCHEMA_DUMP_HAP_CONFIG,
    )

    async_register_admin_service(
        opp=opp,
        domain=HMIPC_DOMAIN,
        service=SERVICE_RESET_ENERGY_COUNTER,
        service_func=async_call_hmipc_service,
        schema=SCHEMA_RESET_ENERGY_COUNTER,
    )


async def async_unload_services(opp: OpenPeerPowerType):
    """Unload HomematicIP Cloud services."""
    if opp.data[HMIPC_DOMAIN]:
        return

    for hmipc_service in HMIPC_SERVICES:
        opp.services.async_remove(domain=HMIPC_DOMAIN, service=hmipc_service)


async def _async_activate_eco_mode_with_duration(
    opp: OpenPeerPowerType, service: ServiceCallType
) -> None:
    """Service to activate eco mode with duration."""
    duration = service.data[ATTR_DURATION]
    hapid = service.data.get(ATTR_ACCESSPOINT_ID)

    if hapid:
        home = _get_home(opp, hapid)
        if home:
            await home.activate_absence_with_duration(duration)
    else:
        for hap in opp.data[HMIPC_DOMAIN].values():
            await hap.home.activate_absence_with_duration(duration)


async def _async_activate_eco_mode_with_period(
    opp: OpenPeerPowerType, service: ServiceCallType
) -> None:
    """Service to activate eco mode with period."""
    endtime = service.data[ATTR_ENDTIME]
    hapid = service.data.get(ATTR_ACCESSPOINT_ID)

    if hapid:
        home = _get_home(opp, hapid)
        if home:
            await home.activate_absence_with_period(endtime)
    else:
        for hap in opp.data[HMIPC_DOMAIN].values():
            await hap.home.activate_absence_with_period(endtime)


async def _async_activate_vacation(
    opp: OpenPeerPowerType, service: ServiceCallType
) -> None:
    """Service to activate vacation."""
    endtime = service.data[ATTR_ENDTIME]
    temperature = service.data[ATTR_TEMPERATURE]
    hapid = service.data.get(ATTR_ACCESSPOINT_ID)

    if hapid:
        home = _get_home(opp, hapid)
        if home:
            await home.activate_vacation(endtime, temperature)
    else:
        for hap in opp.data[HMIPC_DOMAIN].values():
            await hap.home.activate_vacation(endtime, temperature)


async def _async_deactivate_eco_mode(
    opp: OpenPeerPowerType, service: ServiceCallType
) -> None:
    """Service to deactivate eco mode."""
    hapid = service.data.get(ATTR_ACCESSPOINT_ID)

    if hapid:
        home = _get_home(opp, hapid)
        if home:
            await home.deactivate_absence()
    else:
        for hap in opp.data[HMIPC_DOMAIN].values():
            await hap.home.deactivate_absence()


async def _async_deactivate_vacation(
    opp: OpenPeerPowerType, service: ServiceCallType
) -> None:
    """Service to deactivate vacation."""
    hapid = service.data.get(ATTR_ACCESSPOINT_ID)

    if hapid:
        home = _get_home(opp, hapid)
        if home:
            await home.deactivate_vacation()
    else:
        for hap in opp.data[HMIPC_DOMAIN].values():
            await hap.home.deactivate_vacation()


async def _set_active_climate_profile(
    opp: OpenPeerPowerType, service: ServiceCallType
) -> None:
    """Service to set the active climate profile."""
    entity_id_list = service.data[ATTR_ENTITY_ID]
    climate_profile_index = service.data[ATTR_CLIMATE_PROFILE_INDEX] - 1

    for hap in opp.data[HMIPC_DOMAIN].values():
        if entity_id_list != "all":
            for entity_id in entity_id_list:
                group = hap.hmip_device_by_entity_id.get(entity_id)
                if group and isinstance(group, AsyncHeatingGroup):
                    await group.set_active_profile(climate_profile_index)
        else:
            for group in hap.home.groups:
                if isinstance(group, AsyncHeatingGroup):
                    await group.set_active_profile(climate_profile_index)


async def _async_dump_hap_config(
    opp: OpenPeerPowerType, service: ServiceCallType
) -> None:
    """Service to dump the configuration of a Homematic IP Access Point."""
    config_path = service.data.get(ATTR_CONFIG_OUTPUT_PATH) or opp.config.config_dir
    config_file_prefix = service.data[ATTR_CONFIG_OUTPUT_FILE_PREFIX]
    anonymize = service.data[ATTR_ANONYMIZE]

    for hap in opp.data[HMIPC_DOMAIN].values():
        hap_sgtin = hap.config_entry.unique_id

        if anonymize:
            hap_sgtin = hap_sgtin[-4:]

        file_name = f"{config_file_prefix}_{hap_sgtin}.json"
        path = Path(config_path)
        config_file = path / file_name

        json_state = await hap.home.download_configuration()
        json_state = handle_config(json_state, anonymize)

        config_file.write_text(json_state, encoding="utf8")


async def _async_reset_energy_counter(opp: OpenPeerPowerType, service: ServiceCallType):
    """Service to reset the energy counter."""
    entity_id_list = service.data[ATTR_ENTITY_ID]

    for hap in opp.data[HMIPC_DOMAIN].values():
        if entity_id_list != "all":
            for entity_id in entity_id_list:
                device = hap.hmip_device_by_entity_id.get(entity_id)
                if device and isinstance(device, AsyncSwitchMeasuring):
                    await device.reset_energy_counter()
        else:
            for device in hap.home.devices:
                if isinstance(device, AsyncSwitchMeasuring):
                    await device.reset_energy_counter()


def _get_home(opp: OpenPeerPowerType, hapid: str) -> Optional[AsyncHome]:
    """Return a HmIP home."""
    hap = opp.data[HMIPC_DOMAIN].get(hapid)
    if hap:
        return hap.home

    _LOGGER.info("No matching access point found for access point id %s", hapid)
    return None
