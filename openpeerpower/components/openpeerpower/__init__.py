"""Integration providing core pieces of infrastructure."""
import asyncio
import itertools as it
import logging

import voluptuous as vol

from openpeerpower.auth.permissions.const import CAT_ENTITIES, POLICY_CONTROL
import openpeerpower.config as conf_util
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    RESTART_EXIT_CODE,
    SERVICE_OPENPEERPOWER_RESTART,
    SERVICE_OPENPEERPOWER_STOP,
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
import openpeerpower.core as ha
from openpeerpower.exceptions import OpenPeerPowerError, Unauthorized, UnknownUser
from openpeerpower.helpers import config_validation as cv, recorder
from openpeerpower.helpers.service import (
    async_extract_config_entry_ids,
    async_extract_referenced_entity_ids,
)

ATTR_ENTRY_ID = "entry_id"

_LOGGER = logging.getLogger(__name__)
DOMAIN = ha.DOMAIN
SERVICE_RELOAD_CORE_CONFIG = "reload_core_config"
SERVICE_RELOAD_CONFIG_ENTRY = "reload_config_entry"
SERVICE_CHECK_CONFIG = "check_config"
SERVICE_UPDATE_ENTITY = "update_entity"
SERVICE_SET_LOCATION = "set_location"
SCHEMA_UPDATE_ENTITY = vol.Schema({ATTR_ENTITY_ID: cv.entity_ids})
SCHEMA_RELOAD_CONFIG_ENTRY = vol.All(
    vol.Schema(
        {
            vol.Optional(ATTR_ENTRY_ID): str,
            **cv.ENTITY_SERVICE_FIELDS,
        },
    ),
    cv.has_at_least_one_key(ATTR_ENTRY_ID, *cv.ENTITY_SERVICE_FIELDS),
)


SHUTDOWN_SERVICES = (SERVICE_OPENPEERPOWER_STOP, SERVICE_OPENPEERPOWER_RESTART)


async def async_setup(opp: ha.OpenPeerPower, config: dict) -> bool:  # noqa: C901
    """Set up general services related to Open Peer Power."""

    async def async_handle_turn_service(service):
        """Handle calls to openpeerpower.turn_on/off."""
        referenced = await async_extract_referenced_entity_ids(opp, service)
        all_referenced = referenced.referenced | referenced.indirectly_referenced

        # Generic turn on/off method requires entity id
        if not all_referenced:
            _LOGGER.error(
                "The service openpeerpower.%s cannot be called without a target",
                service.service,
            )
            return

        # Group entity_ids by domain. groupby requires sorted data.
        by_domain = it.groupby(
            sorted(all_referenced), lambda item: ha.split_entity_id(item)[0]
        )

        tasks = []
        unsupported_entities = set()

        for domain, ent_ids in by_domain:
            # This leads to endless loop.
            if domain == DOMAIN:
                _LOGGER.warning(
                    "Called service openpeerpower.%s with invalid entities %s",
                    service.service,
                    ", ".join(ent_ids),
                )
                continue

            if not opp.services.has_service(domain, service.service):
                unsupported_entities.update(set(ent_ids) & referenced.referenced)
                continue

            # Create a new dict for this call
            data = dict(service.data)

            # ent_ids is a generator, convert it to a list.
            data[ATTR_ENTITY_ID] = list(ent_ids)

            tasks.append(
                opp.services.async_call(
                    domain,
                    service.service,
                    data,
                    blocking=True,
                    context=service.context,
                )
            )

        if unsupported_entities:
            _LOGGER.warning(
                "The service openpeerpower.%s does not support entities %s",
                service.service,
                ", ".join(sorted(unsupported_entities)),
            )

        if tasks:
            await asyncio.gather(*tasks)

    service_schema = vol.Schema({ATTR_ENTITY_ID: cv.entity_ids}, extra=vol.ALLOW_EXTRA)

    opp.services.async_register(
        ha.DOMAIN, SERVICE_TURN_OFF, async_handle_turn_service, schema=service_schema
    )
    opp.services.async_register(
        ha.DOMAIN, SERVICE_TURN_ON, async_handle_turn_service, schema=service_schema
    )
    opp.services.async_register(
        ha.DOMAIN, SERVICE_TOGGLE, async_handle_turn_service, schema=service_schema
    )

    async def async_handle_core_service(call):
        """Service handler for handling core services."""
        if (
            call.service in SHUTDOWN_SERVICES
            and await recorder.async_migration_in_progress(opp)
        ):
            _LOGGER.error(
                "The system cannot %s while a database upgrade is in progress",
                call.service,
            )
            raise OpenPeerPowerError(
                f"The system cannot {call.service} "
                "while a database upgrade is in progress."
            )

        if call.service == SERVICE_OPENPEERPOWER_STOP:
            asyncio.create_task(opp.async_stop())
            return

        errors = await conf_util.async_check_op_config_file(opp)

        if errors:
            _LOGGER.error(
                "The system cannot %s because the configuration is not valid: %s",
                call.service,
                errors,
            )
            opp.components.persistent_notification.async_create(
                "Config error. See [the logs](/config/logs) for details.",
                "Config validating",
                f"{ha.DOMAIN}.check_config",
            )
            raise OpenPeerPowerError(
                f"The system cannot {call.service} "
                f"because the configuration is not valid: {errors}"
            )

        if call.service == SERVICE_OPENPEERPOWER_RESTART:
            asyncio.create_task(opp.async_stop(RESTART_EXIT_CODE))

    async def async_handle_update_service(call):
        """Service handler for updating an entity."""
        if call.context.user_id:
            user = await opp.auth.async_get_user(call.context.user_id)

            if user is None:
                raise UnknownUser(
                    context=call.context,
                    permission=POLICY_CONTROL,
                    user_id=call.context.user_id,
                )

            for entity in call.data[ATTR_ENTITY_ID]:
                if not user.permissions.check_entity(entity, POLICY_CONTROL):
                    raise Unauthorized(
                        context=call.context,
                        permission=POLICY_CONTROL,
                        user_id=call.context.user_id,
                        perm_category=CAT_ENTITIES,
                    )

        tasks = [
            opp.helpers.entity_component.async_update_entity(entity)
            for entity in call.data[ATTR_ENTITY_ID]
        ]

        if tasks:
            await asyncio.wait(tasks)

    opp.helpers.service.async_register_admin_service(
        ha.DOMAIN, SERVICE_OPENPEERPOWER_STOP, async_handle_core_service
    )
    opp.helpers.service.async_register_admin_service(
        ha.DOMAIN, SERVICE_OPENPEERPOWER_RESTART, async_handle_core_service
    )
    opp.helpers.service.async_register_admin_service(
        ha.DOMAIN, SERVICE_CHECK_CONFIG, async_handle_core_service
    )
    opp.services.async_register(
        ha.DOMAIN,
        SERVICE_UPDATE_ENTITY,
        async_handle_update_service,
        schema=SCHEMA_UPDATE_ENTITY,
    )

    async def async_handle_reload_config(call):
        """Service handler for reloading core config."""
        try:
            conf = await conf_util.async_opp_config_yaml(opp)
        except OpenPeerPowerError as err:
            _LOGGER.error(err)
            return

        # auth only processed during startup
        await conf_util.async_process_op_core_config(opp, conf.get(ha.DOMAIN) or {})

    opp.helpers.service.async_register_admin_service(
        ha.DOMAIN, SERVICE_RELOAD_CORE_CONFIG, async_handle_reload_config
    )

    async def async_set_location(call):
        """Service handler to set location."""
        await opp.config.async_update(
            latitude=call.data[ATTR_LATITUDE], longitude=call.data[ATTR_LONGITUDE]
        )

    opp.helpers.service.async_register_admin_service(
        ha.DOMAIN,
        SERVICE_SET_LOCATION,
        async_set_location,
        vol.Schema({ATTR_LATITUDE: cv.latitude, ATTR_LONGITUDE: cv.longitude}),
    )

    async def async_handle_reload_config_entry(call):
        """Service handler for reloading a config entry."""
        reload_entries = set()
        if ATTR_ENTRY_ID in call.data:
            reload_entries.add(call.data[ATTR_ENTRY_ID])
        reload_entries.update(await async_extract_config_entry_ids(opp, call))
        if not reload_entries:
            raise ValueError("There were no matching config entries to reload")
        await asyncio.gather(
            *[
                opp.config_entries.async_reload(config_entry_id)
                for config_entry_id in reload_entries
            ]
        )

    opp.helpers.service.async_register_admin_service(
        ha.DOMAIN,
        SERVICE_RELOAD_CONFIG_ENTRY,
        async_handle_reload_config_entry,
        schema=SCHEMA_RELOAD_CONFIG_ENTRY,
    )

    return True
