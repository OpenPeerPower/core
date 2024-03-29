"""Provides device actions for lights."""
from __future__ import annotations

import voluptuous as vol

from openpeerpower.components.device_automation import toggle_entity
from openpeerpower.components.light import (
    ATTR_FLASH,
    FLASH_SHORT,
    SUPPORT_FLASH,
    VALID_BRIGHTNESS_PCT,
    VALID_FLASH,
)
from openpeerpower.const import ATTR_ENTITY_ID, CONF_DOMAIN, CONF_TYPE, SERVICE_TURN_ON
from openpeerpower.core import Context, OpenPeerPower, OpenPeerPowerError
from openpeerpower.helpers import config_validation as cv, entity_registry as er
from openpeerpower.helpers.entity import get_supported_features
from openpeerpower.helpers.typing import ConfigType, TemplateVarsType

from . import (
    ATTR_BRIGHTNESS_PCT,
    ATTR_BRIGHTNESS_STEP_PCT,
    ATTR_SUPPORTED_COLOR_MODES,
    DOMAIN,
    brightness_supported,
)

TYPE_BRIGHTNESS_INCREASE = "brightness_increase"
TYPE_BRIGHTNESS_DECREASE = "brightness_decrease"
TYPE_FLASH = "flash"

ACTION_SCHEMA = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        vol.Required(CONF_DOMAIN): DOMAIN,
        vol.Required(CONF_TYPE): vol.In(
            toggle_entity.DEVICE_ACTION_TYPES
            + [TYPE_BRIGHTNESS_INCREASE, TYPE_BRIGHTNESS_DECREASE, TYPE_FLASH]
        ),
        vol.Optional(ATTR_BRIGHTNESS_PCT): VALID_BRIGHTNESS_PCT,
        vol.Optional(ATTR_FLASH): VALID_FLASH,
    }
)


def get_supported_color_modes(opp: OpenPeerPower, entity_id: str) -> set | None:
    """Get supported color modes for a light entity.

    First try the statemachine, then entity registry.
    """
    state = opp.states.get(entity_id)
    if state:
        return state.attributes.get(ATTR_SUPPORTED_COLOR_MODES)

    entity_registry = er.async_get(opp)
    entry = entity_registry.async_get(entity_id)
    if not entry:
        raise OpenPeerPowerError(f"Unknown entity {entity_id}")
    if not entry.capabilities:
        return None

    return entry.capabilities.get(ATTR_SUPPORTED_COLOR_MODES)


async def async_call_action_from_config(
    opp: OpenPeerPower,
    config: ConfigType,
    variables: TemplateVarsType,
    context: Context,
) -> None:
    """Change state based on configuration."""
    if (
        config[CONF_TYPE] in toggle_entity.DEVICE_ACTION_TYPES
        and config[CONF_TYPE] != toggle_entity.CONF_TURN_ON
    ):
        await toggle_entity.async_call_action_from_config(
            opp, config, variables, context, DOMAIN
        )
        return

    data = {ATTR_ENTITY_ID: config[ATTR_ENTITY_ID]}

    if config[CONF_TYPE] == TYPE_BRIGHTNESS_INCREASE:
        data[ATTR_BRIGHTNESS_STEP_PCT] = 10
    elif config[CONF_TYPE] == TYPE_BRIGHTNESS_DECREASE:
        data[ATTR_BRIGHTNESS_STEP_PCT] = -10
    elif ATTR_BRIGHTNESS_PCT in config:
        data[ATTR_BRIGHTNESS_PCT] = config[ATTR_BRIGHTNESS_PCT]

    if config[CONF_TYPE] == TYPE_FLASH:
        if ATTR_FLASH in config:
            data[ATTR_FLASH] = config[ATTR_FLASH]
        else:
            data[ATTR_FLASH] = FLASH_SHORT

    await opp.services.async_call(
        DOMAIN, SERVICE_TURN_ON, data, blocking=True, context=context
    )


async def async_get_actions(opp: OpenPeerPower, device_id: str) -> list[dict]:
    """List device actions."""
    actions = await toggle_entity.async_get_actions(opp, device_id, DOMAIN)

    entity_registry = er.async_get(opp)

    for entry in er.async_entries_for_device(entity_registry, device_id):
        if entry.domain != DOMAIN:
            continue

        supported_color_modes = get_supported_color_modes(opp, entry.entity_id)
        supported_features = get_supported_features(opp, entry.entity_id)

        if brightness_supported(supported_color_modes):
            actions.extend(
                (
                    {
                        CONF_TYPE: TYPE_BRIGHTNESS_INCREASE,
                        "device_id": device_id,
                        "entity_id": entry.entity_id,
                        "domain": DOMAIN,
                    },
                    {
                        CONF_TYPE: TYPE_BRIGHTNESS_DECREASE,
                        "device_id": device_id,
                        "entity_id": entry.entity_id,
                        "domain": DOMAIN,
                    },
                )
            )

        if supported_features & SUPPORT_FLASH:
            actions.extend(
                (
                    {
                        CONF_TYPE: TYPE_FLASH,
                        "device_id": device_id,
                        "entity_id": entry.entity_id,
                        "domain": DOMAIN,
                    },
                )
            )

    return actions


async def async_get_action_capabilities(opp: OpenPeerPower, config: dict) -> dict:
    """List action capabilities."""
    if config[CONF_TYPE] != toggle_entity.CONF_TURN_ON:
        return {}

    try:
        supported_color_modes = get_supported_color_modes(opp, config[ATTR_ENTITY_ID])
    except OpenPeerPowerError:
        supported_color_modes = None

    try:
        supported_features = get_supported_features(opp, config[ATTR_ENTITY_ID])
    except OpenPeerPowerError:
        supported_features = 0

    extra_fields = {}

    if brightness_supported(supported_color_modes):
        extra_fields[vol.Optional(ATTR_BRIGHTNESS_PCT)] = VALID_BRIGHTNESS_PCT

    if supported_features & SUPPORT_FLASH:
        extra_fields[vol.Optional(ATTR_FLASH)] = VALID_FLASH

    return {"extra_fields": vol.Schema(extra_fields)} if extra_fields else {}
