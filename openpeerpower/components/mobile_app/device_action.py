"""Provides device actions for Mobile App."""
from typing import List, Optional

import voluptuous as vol

from openpeerpower.components import notify
from openpeerpower.components.device_automation import InvalidDeviceAutomationConfig
from openpeerpower.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_TYPE
from openpeerpower.core import Context, OpenPeerPower
from openpeerpower.helpers import config_validation as cv, template

from .const import DOMAIN
from .util import get_notify_service, supports_push, webhook_id_from_device_id

ACTION_SCHEMA = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): "notify",
        vol.Required(notify.ATTR_MESSAGE): cv.template,
        vol.Optional(notify.ATTR_TITLE): cv.template,
        vol.Optional(notify.ATTR_DATA): cv.template_complex,
    }
)


async def async_get_actions(opp: OpenPeerPower, device_id: str) -> List[dict]:
    """List device actions for Mobile App devices."""
    webhook_id = webhook_id_from_device_id(opp, device_id)

    if webhook_id is None or not supports_push(opp, webhook_id):
        return []

    return [{CONF_DEVICE_ID: device_id, CONF_DOMAIN: DOMAIN, CONF_TYPE: "notify"}]


async def async_call_action_from_config(
    opp: OpenPeerPower, config: dict, variables: dict, context: Optional[Context]
) -> None:
    """Execute a device action."""
    webhook_id = webhook_id_from_device_id(opp, config[CONF_DEVICE_ID])

    if webhook_id is None:
        raise InvalidDeviceAutomationConfig(
            "Unable to resolve webhook ID from the device ID"
        )

    service_name = get_notify_service(opp, webhook_id)

    if service_name is None:
        raise InvalidDeviceAutomationConfig(
            "Unable to find notify service for webhook ID"
        )

    service_data = {notify.ATTR_TARGET: webhook_id}

    # Render it here because we have access to variables here.
    for key in (notify.ATTR_MESSAGE, notify.ATTR_TITLE, notify.ATTR_DATA):
        if key not in config:
            continue

        value_template = config[key]
        template.attach(opp, value_template)

        try:
            service_data[key] = template.render_complex(value_template, variables)
        except template.TemplateError as err:
            raise InvalidDeviceAutomationConfig(
                f"Error rendering {key}: {err}"
            ) from err

    await opp.services.async_call(
        notify.DOMAIN, service_name, service_data, blocking=True, context=context
    )


async def async_get_action_capabilities(opp, config):
    """List action capabilities."""
    if config[CONF_TYPE] != "notify":
        return {}

    return {
        "extra_fields": vol.Schema(
            {
                vol.Required(notify.ATTR_MESSAGE): str,
                vol.Optional(notify.ATTR_TITLE): str,
            }
        )
    }
