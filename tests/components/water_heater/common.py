"""Collection of helper methods.

All containing methods are legacy helpers that should not be used by new
components. Instead call the service directly.
"""
from openpeerpower.components.water_heater import (
    _LOGGER,
    ATTR_AWAY_MODE,
    ATTR_OPERATION_MODE,
    DOMAIN,
    SERVICE_SET_AWAY_MODE,
    SERVICE_SET_OPERATION_MODE,
    SERVICE_SET_TEMPERATURE,
)
from openpeerpower.const import ATTR_ENTITY_ID, ATTR_TEMPERATURE, ENTITY_MATCH_ALL


async def async_set_away_mode(opp, away_mode, entity_id=ENTITY_MATCH_ALL):
    """Turn all or specified water_heater devices away mode on."""
    data = {ATTR_AWAY_MODE: away_mode}

    if entity_id:
        data[ATTR_ENTITY_ID] = entity_id

    await opp.services.async_call(DOMAIN, SERVICE_SET_AWAY_MODE, data, blocking=True)


async def async_set_temperature(
    opp, temperature=None, entity_id=ENTITY_MATCH_ALL, operation_mode=None
):
    """Set new target temperature."""
    kwargs = {
        key: value
        for key, value in [
            (ATTR_TEMPERATURE, temperature),
            (ATTR_ENTITY_ID, entity_id),
            (ATTR_OPERATION_MODE, operation_mode),
        ]
        if value is not None
    }
    _LOGGER.debug("set_temperature start data=%s", kwargs)
    await opp.services.async_call(
        DOMAIN, SERVICE_SET_TEMPERATURE, kwargs, blocking=True
    )


async def async_set_operation_mode(opp, operation_mode, entity_id=ENTITY_MATCH_ALL):
    """Set new target operation mode."""
    data = {ATTR_OPERATION_MODE: operation_mode}

    if entity_id is not None:
        data[ATTR_ENTITY_ID] = entity_id

    await opp.services.async_call(
        DOMAIN, SERVICE_SET_OPERATION_MODE, data, blocking=True
    )
