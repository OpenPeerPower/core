"""Mobile app utility functions."""
from typing import TYPE_CHECKING, Optional

from openpeerpower.core import callback

from .const import (
    ATTR_APP_DATA,
    ATTR_PUSH_TOKEN,
    ATTR_PUSH_URL,
    DATA_CONFIG_ENTRIES,
    DATA_DEVICES,
    DATA_NOTIFY,
    DOMAIN,
)

if TYPE_CHECKING:
    from .notify import MobileAppNotificationService


@callback
def webhook_id_from_device_id(opp, device_id: str) -> Optional[str]:
    """Get webhook ID from device ID."""
    if DOMAIN not in opp.data:
        return None

    for cur_webhook_id, cur_device in opp.data[DOMAIN][DATA_DEVICES].items():
        if cur_device.id == device_id:
            return cur_webhook_id

    return None


@callback
def supports_push(opp, webhook_id: str) -> bool:
    """Return if push notifications is supported."""
    config_entry = opp.data[DOMAIN][DATA_CONFIG_ENTRIES][webhook_id]
    app_data = config_entry.data[ATTR_APP_DATA]
    return ATTR_PUSH_TOKEN in app_data and ATTR_PUSH_URL in app_data


@callback
def get_notify_service(opp, webhook_id: str) -> Optional[str]:
    """Return the notify service for this webhook ID."""
    notify_service: "MobileAppNotificationService" = opp.data[DOMAIN][DATA_NOTIFY]

    for target_service, target_webhook_id in notify_service.registered_targets.items():
        if target_webhook_id == webhook_id:
            return target_service

    return None
