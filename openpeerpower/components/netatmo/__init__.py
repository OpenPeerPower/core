"""The Netatmo integration."""
import asyncio
import logging
import secrets

import pyatmo
import voluptuous as vol

from openpeerpower.components import cloud
from openpeerpower.components.webhook import (
    async_register as webhook_register,
    async_unregister as webhook_unregister,
)
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_WEBHOOK_ID,
    EVENT_OPENPEERPOWER_START,
    EVENT_OPENPEERPOWER_STOP,
)
from openpeerpower.core import CoreState, OpenPeerPower
from openpeerpower.helpers import config_entry_oauth2_flow, config_validation as cv
from openpeerpower.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from openpeerpower.helpers.event import async_call_later

from . import api, config_flow
from .const import (
    AUTH,
    CONF_CLOUDHOOK_URL,
    DATA_CAMERAS,
    DATA_DEVICE_IDS,
    DATA_EVENTS,
    DATA_HANDLER,
    DATA_HOMES,
    DATA_PERSONS,
    DATA_SCHEDULES,
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
)
from .data_handler import NetatmoDataHandler
from .webhook import async_handle_webhook

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID): cv.string,
                vol.Required(CONF_CLIENT_SECRET): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = ["camera", "climate", "light", "sensor"]


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the Netatmo component."""
    opp.data[DOMAIN] = {
        DATA_PERSONS: {},
        DATA_DEVICE_IDS: {},
        DATA_SCHEDULES: {},
        DATA_HOMES: {},
        DATA_EVENTS: {},
        DATA_CAMERAS: {},
    }

    if DOMAIN not in config:
        return True

    config_flow.NetatmoFlowHandler.async_register_implementation(
        opp,
        config_entry_oauth2_flow.LocalOAuth2Implementation(
            opp,
            DOMAIN,
            config[DOMAIN][CONF_CLIENT_ID],
            config[DOMAIN][CONF_CLIENT_SECRET],
            OAUTH2_AUTHORIZE,
            OAUTH2_TOKEN,
        ),
    )

    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Netatmo from a config entry."""
    implementation = (
        await config_entry_oauth2_flow.async_get_config_entry_implementation(opp, entry)
    )

    # Set unique id if non was set (migration)
    if not entry.unique_id:
        opp.config_entries.async_update_entry(entry, unique_id=DOMAIN)

    opp.data[DOMAIN][entry.entry_id] = {
        AUTH: api.ConfigEntryNetatmoAuth(opp, entry, implementation)
    }

    data_handler = NetatmoDataHandler(opp, entry)
    await data_handler.async_setup()
    opp.data[DOMAIN][entry.entry_id][DATA_HANDLER] = data_handler

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    async def unregister_webhook(_):
        if CONF_WEBHOOK_ID not in entry.data:
            return
        _LOGGER.debug("Unregister Netatmo webhook (%s)", entry.data[CONF_WEBHOOK_ID])
        async_dispatcher_send(
            opp,
            f"signal-{DOMAIN}-webhook-None",
            {"type": "None", "data": {"push_type": "webhook_deactivation"}},
        )
        webhook_unregister(opp, entry.data[CONF_WEBHOOK_ID])

    async def register_webhook(event):
        if CONF_WEBHOOK_ID not in entry.data:
            data = {**entry.data, CONF_WEBHOOK_ID: secrets.token_hex()}
            opp.config_entries.async_update_entry(entry, data=data)

        if opp.components.cloud.async_active_subscription():
            if CONF_CLOUDHOOK_URL not in entry.data:
                webhook_url = await opp.components.cloud.async_create_cloudhook(
                    entry.data[CONF_WEBHOOK_ID]
                )
                data = {**entry.data, CONF_CLOUDHOOK_URL: webhook_url}
                opp.config_entries.async_update_entry(entry, data=data)
            else:
                webhook_url = entry.data[CONF_CLOUDHOOK_URL]
        else:
            webhook_url = opp.components.webhook.async_generate_url(
                entry.data[CONF_WEBHOOK_ID]
            )

        if entry.data["auth_implementation"] == "cloud" and not webhook_url.startswith(
            "https://"
        ):
            _LOGGER.warning(
                "Webhook not registered - "
                "https and port 443 is required to register the webhook"
            )
            return

        try:
            webhook_register(
                opp,
                DOMAIN,
                "Netatmo",
                entry.data[CONF_WEBHOOK_ID],
                async_handle_webhook,
            )

            async def handle_event(event):
                """Handle webhook events."""
                if event["data"]["push_type"] == "webhook_activation":
                    if activation_listener is not None:
                        activation_listener()

                    if activation_timeout is not None:
                        activation_timeout()

            activation_listener = async_dispatcher_connect(
                opp,
                f"signal-{DOMAIN}-webhook-None",
                handle_event,
            )

            activation_timeout = async_call_later(opp, 10, unregister_webhook)

            await opp.async_add_executor_job(
                opp.data[DOMAIN][entry.entry_id][AUTH].addwebhook, webhook_url
            )
            _LOGGER.info("Register Netatmo webhook: %s", webhook_url)
        except pyatmo.ApiError as err:
            _LOGGER.error("Error during webhook registration - %s", err)

        opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STOP, unregister_webhook)

    if opp.state == CoreState.running:
        await register_webhook(None)
    else:
        opp.bus.async_listen_once(EVENT_OPENPEERPOWER_START, register_webhook)

    opp.services.async_register(DOMAIN, "register_webhook", register_webhook)
    opp.services.async_register(DOMAIN, "unregister_webhook", unregister_webhook)

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    if CONF_WEBHOOK_ID in entry.data:
        await opp.async_add_executor_job(
            opp.data[DOMAIN][entry.entry_id][AUTH].dropwebhook
        )
        _LOGGER.info("Unregister Netatmo webhook.")

    await opp.data[DOMAIN][entry.entry_id][DATA_HANDLER].async_cleanup()

    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    if unload_ok:
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_remove_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Cleanup when entry is removed."""
    if (
        CONF_WEBHOOK_ID in entry.data
        and opp.components.cloud.async_active_subscription()
    ):
        try:
            _LOGGER.debug(
                "Removing Netatmo cloudhook (%s)", entry.data[CONF_WEBHOOK_ID]
            )
            await cloud.async_delete_cloudhook(opp, entry.data[CONF_WEBHOOK_ID])
        except cloud.CloudNotAvailable:
            pass
