"""Interface implementation for cloud client."""
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict

import aiohttp
from opp_net.client import CloudClient as Interface

from openpeerpower.components.alexa import (
    errors as alexa_errors,
    smart_home as alexa_sh,
)
from openpeerpower.components.google_assistant import const as gc, smart_home as ga
from openpeerpower.const import HTTP_OK
from openpeerpower.core import Context, callback
from openpeerpower.helpers.dispatcher import async_dispatcher_send
from openpeerpower.helpers.event import async_call_later
from openpeerpower.helpers.typing import OpenPeerPowerType
from openpeerpower.util.aiohttp import MockRequest

from . import alexa_config, google_config, utils
from .const import DISPATCHER_REMOTE_UPDATE, DOMAIN
from .prefs import CloudPreferences


class CloudClient(Interface):
    """Interface class for Open Peer Power Cloud."""

    def __init__(
        self,
        opp: OpenPeerPowerType,
        prefs: CloudPreferences,
        websession: aiohttp.ClientSession,
        alexa_user_config: Dict[str, Any],
        google_user_config: Dict[str, Any],
    ):
        """Initialize client interface to Cloud."""
        self._opp = opp
        self._prefs = prefs
        self._websession = websession
        self.google_user_config = google_user_config
        self.alexa_user_config = alexa_user_config
        self._alexa_config = None
        self._google_config = None

    @property
    def base_path(self) -> Path:
        """Return path to base dir."""
        return Path(self._opp.config.config_dir)

    @property
    def prefs(self) -> CloudPreferences:
        """Return Cloud preferences."""
        return self._prefs

    @property
    def loop(self) -> asyncio.BaseEventLoop:
        """Return client loop."""
        return self._opp.loop

    @property
    def websession(self) -> aiohttp.ClientSession:
        """Return client session for aiohttp."""
        return self._websession

    @property
    def aiohttp_runner(self) -> aiohttp.web.AppRunner:
        """Return client webinterface aiohttp application."""
        return self._opp.http.runner

    @property
    def cloudhooks(self) -> Dict[str, Dict[str, str]]:
        """Return list of cloudhooks."""
        return self._prefs.cloudhooks

    @property
    def remote_autostart(self) -> bool:
        """Return true if we want start a remote connection."""
        return self._prefs.remote_enabled

    async def get_alexa_config(self) -> alexa_config.AlexaConfig:
        """Return Alexa config."""
        if self._alexa_config is None:
            assert self.cloud is not None

            cloud_user = await self._prefs.get_cloud_user()

            self._alexa_config = alexa_config.AlexaConfig(
                self._opp, self.alexa_user_config, cloud_user, self._prefs, self.cloud
            )

        return self._alexa_config

    async def get_google_config(self) -> google_config.CloudGoogleConfig:
        """Return Google config."""
        if not self._google_config:
            assert self.cloud is not None

            cloud_user = await self._prefs.get_cloud_user()

            self._google_config = google_config.CloudGoogleConfig(
                self._opp, self.google_user_config, cloud_user, self._prefs, self.cloud
            )
            await self._google_config.async_initialize()

        return self._google_config

    async def logged_in(self) -> None:
        """When user logs in."""
        await self.prefs.async_set_username(self.cloud.username)

        async def enable_alexa(_):
            """Enable Alexa."""
            aconf = await self.get_alexa_config()
            try:
                await aconf.async_enable_proactive_mode()
            except aiohttp.ClientError as err:  # If no internet available yet
                if self._opp.is_running:
                    logging.getLogger(__package__).warning(
                        "Unable to activate Alexa Report State: %s. Retrying in 30 seconds",
                        err,
                    )
                async_call_later(self._opp, 30, enable_alexa)
            except alexa_errors.NoTokenAvailable:
                pass

        async def enable_google(_):
            """Enable Google."""
            gconf = await self.get_google_config()

            gconf.async_enable_local_sdk()

            if gconf.should_report_state:
                gconf.async_enable_report_state()

        tasks = []

        if self._prefs.alexa_enabled and self._prefs.alexa_report_state:
            tasks.append(enable_alexa)

        if self._prefs.google_enabled:
            tasks.append(enable_google)

        if tasks:
            await asyncio.gather(*[task(None) for task in tasks])

    async def cleanups(self) -> None:
        """Cleanup some stuff after logout."""
        await self.prefs.async_set_username(None)

        self._google_config = None

    @callback
    def user_message(self, identifier: str, title: str, message: str) -> None:
        """Create a message for user to UI."""
        self._opp.components.persistent_notification.async_create(
            message, title, identifier
        )

    @callback
    def dispatcher_message(self, identifier: str, data: Any = None) -> None:
        """Match cloud notification to dispatcher."""
        if identifier.startswith("remote_"):
            async_dispatcher_send(self._opp, DISPATCHER_REMOTE_UPDATE, data)

    async def async_alexa_message(self, payload: Dict[Any, Any]) -> Dict[Any, Any]:
        """Process cloud alexa message to client."""
        cloud_user = await self._prefs.get_cloud_user()
        aconfig = await self.get_alexa_config()
        return await alexa_sh.async_handle_message(
            self._opp,
            aconfig,
            payload,
            context=Context(user_id=cloud_user),
            enabled=self._prefs.alexa_enabled,
        )

    async def async_google_message(self, payload: Dict[Any, Any]) -> Dict[Any, Any]:
        """Process cloud google message to client."""
        if not self._prefs.google_enabled:
            return ga.turned_off_response(payload)

        gconf = await self.get_google_config()

        return await ga.async_handle_message(
            self._opp, gconf, gconf.cloud_user, payload, gc.SOURCE_CLOUD
        )

    async def async_webhook_message(self, payload: Dict[Any, Any]) -> Dict[Any, Any]:
        """Process cloud webhook message to client."""
        cloudhook_id = payload["cloudhook_id"]

        found = None
        for cloudhook in self._prefs.cloudhooks.values():
            if cloudhook["cloudhook_id"] == cloudhook_id:
                found = cloudhook
                break

        if found is None:
            return {"status": HTTP_OK}

        request = MockRequest(
            content=payload["body"].encode("utf-8"),
            headers=payload["headers"],
            method=payload["method"],
            query_string=payload["query"],
            mock_source=DOMAIN,
        )

        response = await self._opp.components.webhook.async_handle_webhook(
            found["webhook_id"], request
        )

        response_dict = utils.aiohttp_serialize_response(response)
        body = response_dict.get("body")

        return {
            "body": body,
            "status": response_dict["status"],
            "headers": {"Content-Type": response.content_type},
        }

    async def async_cloudhooks_update(self, data: Dict[str, Dict[str, str]]) -> None:
        """Update local list of cloudhooks."""
        await self._prefs.async_update(cloudhooks=data)
