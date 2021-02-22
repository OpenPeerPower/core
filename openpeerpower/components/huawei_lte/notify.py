"""Support for Huawei LTE router notifications."""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

import attr
from huawei_lte_api.exceptions import ResponseErrorException

from openpeerpower.components.notify import ATTR_TARGET, BaseNotificationService
from openpeerpower.const import CONF_RECIPIENT, CONF_URL
from openpeerpower.helpers.typing import OpenPeerPowerType

from . import Router
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_get_service(
    opp: OpenPeerPowerType,
    config: Dict[str, Any],
    discovery_info: Optional[Dict[str, Any]] = None,
) -> Optional[HuaweiLteSmsNotificationService]:
    """Get the notification service."""
    if discovery_info is None:
        return None

    router = opp.data[DOMAIN].routers[discovery_info[CONF_URL]]
    default_targets = discovery_info[CONF_RECIPIENT] or []

    return HuaweiLteSmsNotificationService(router, default_targets)


@attr.s
class HuaweiLteSmsNotificationService(BaseNotificationService):
    """Huawei LTE router SMS notification service."""

    router: Router = attr.ib()
    default_targets: List[str] = attr.ib()

    def send_message(self, message: str = "", **kwargs: Any) -> None:
        """Send message to target numbers."""

        targets = kwargs.get(ATTR_TARGET, self.default_targets)
        if not targets or not message:
            return

        if self.router.suspended:
            _LOGGER.debug(
                "Integration suspended, not sending notification to %s", targets
            )
            return

        try:
            resp = self.router.client.sms.send_sms(
                phone_numbers=targets, message=message
            )
            _LOGGER.debug("Sent to %s: %s", targets, resp)
        except ResponseErrorException as ex:
            _LOGGER.error("Could not send to %s: %s", targets, ex)
        finally:
            self.router.notify_last_attempt = time.monotonic()
