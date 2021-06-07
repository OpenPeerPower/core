"""Analytics helper class for the analytics integration."""
import asyncio
import uuid

import aiohttp
import async_timeout

from openpeerpower.components import oppio
from openpeerpower.components.api import ATTR_INSTALLATION_TYPE
from openpeerpower.components.automation.const import DOMAIN as AUTOMATION_DOMAIN
from openpeerpower.const import ATTR_DOMAIN, __version__ as HA_VERSION
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.storage import Store
from openpeerpower.helpers.system_info import async_get_system_info
from openpeerpower.loader import IntegrationNotFound, async_get_integration
from openpeerpower.setup import async_get_loaded_integrations

from .const import (
    ANALYTICS_ENDPOINT_URL,
    ANALYTICS_ENDPOINT_URL_DEV,
    ATTR_ADDON_COUNT,
    ATTR_ADDONS,
    ATTR_ARCH,
    ATTR_AUTO_UPDATE,
    ATTR_AUTOMATION_COUNT,
    ATTR_BASE,
    ATTR_BOARD,
    ATTR_CUSTOM_INTEGRATIONS,
    ATTR_DIAGNOSTICS,
    ATTR_HEALTHY,
    ATTR_INTEGRATION_COUNT,
    ATTR_INTEGRATIONS,
    ATTR_ONBOARDED,
    ATTR_OPERATING_SYSTEM,
    ATTR_PREFERENCES,
    ATTR_PROTECTED,
    ATTR_SLUG,
    ATTR_STATE_COUNT,
    ATTR_STATISTICS,
    ATTR_SUPERVISOR,
    ATTR_SUPPORTED,
    ATTR_USAGE,
    ATTR_USER_COUNT,
    ATTR_UUID,
    ATTR_VERSION,
    LOGGER,
    PREFERENCE_SCHEMA,
    STORAGE_KEY,
    STORAGE_VERSION,
)


class Analytics:
    """Analytics helper class for the analytics integration."""

    def __init__(self, opp: OpenPeerPower) -> None:
        """Initialize the Analytics class."""
        self.opp: OpenPeerPower =.opp
        self.session = async_get_clientsession(opp)
        self._data = {ATTR_PREFERENCES: {}, ATTR_ONBOARDED: False, ATTR_UUID: None}
        self._store: Store = opp.helpers.storage.Store(STORAGE_VERSION, STORAGE_KEY)

    @property
    def preferences(self) -> dict:
        """Return the current active preferences."""
        preferences = self._data[ATTR_PREFERENCES]
        return {
            ATTR_BASE: preferences.get(ATTR_BASE, False),
            ATTR_DIAGNOSTICS: preferences.get(ATTR_DIAGNOSTICS, False),
            ATTR_USAGE: preferences.get(ATTR_USAGE, False),
            ATTR_STATISTICS: preferences.get(ATTR_STATISTICS, False),
        }

    @property
    def onboarded(self) -> bool:
        """Return bool if the user has made a choice."""
        return self._data[ATTR_ONBOARDED]

    @property
    def uuid(self) -> bool:
        """Return the uuid for the analytics integration."""
        return self._data[ATTR_UUID]

    @property
    def endpoint(self) -> str:
        """Return the endpoint that will receive the payload."""
        if HA_VERSION.endswith("0.dev0"):
            # dev installations will contact the dev analytics environment
            return ANALYTICS_ENDPOINT_URL_DEV
        return ANALYTICS_ENDPOINT_URL

    @property
    def supervisor(self) -> bool:
        """Return bool if a supervisor is present."""
        return oppio.is_oppio(self.opp)

    async def load(self) -> None:
        """Load preferences."""
        stored = await self._store.async_load()
        if stored:
            self._data = stored

        if self.supervisor:
            supervisor_info = oppio.get_supervisor_info(self.opp)
            if not self.onboarded:
                # User have not configured analytics, get this setting from the supervisor
                if supervisor_info[ATTR_DIAGNOSTICS] and not self.preferences.get(
                    ATTR_DIAGNOSTICS, False
                ):
                    self._data[ATTR_PREFERENCES][ATTR_DIAGNOSTICS] = True
                elif not supervisor_info[ATTR_DIAGNOSTICS] and self.preferences.get(
                    ATTR_DIAGNOSTICS, False
                ):
                    self._data[ATTR_PREFERENCES][ATTR_DIAGNOSTICS] = False

    async def save_preferences(self, preferences: dict) -> None:
        """Save preferences."""
        preferences = PREFERENCE_SCHEMA(preferences)
        self._data[ATTR_PREFERENCES].update(preferences)
        self._data[ATTR_ONBOARDED] = True

        await self._store.async_save(self._data)

        if self.supervisor:
            await oppio.async_update_diagnostics(
                self.opp, self.preferences.get(ATTR_DIAGNOSTICS, False)
            )

    async def send_analytics(self, _=None) -> None:
        """Send analytics."""
        supervisor_info = None
        operating_system_info = {}

        if not self.onboarded or not self.preferences.get(ATTR_BASE, False):
            LOGGER.debug("Nothing to submit")
            return

        if self._data.get(ATTR_UUID) is None:
            self._data[ATTR_UUID] = uuid.uuid4().hex
            await self._store.async_save(self._data)

        if self.supervisor:
            supervisor_info = oppio.get_supervisor_info(self.opp)
            operating_system_info = oppio.get_os_info(self.opp)

        system_info = await async_get_system_info(self.opp)
        integrations = []
        custom_integrations = []
        addons = []
        payload: dict = {
            ATTR_UUID: self.uuid,
            ATTR_VERSION: HA_VERSION,
            ATTR_INSTALLATION_TYPE: system_info[ATTR_INSTALLATION_TYPE],
        }

        if supervisor_info is not None:
            payload[ATTR_SUPERVISOR] = {
                ATTR_HEALTHY: supervisor_info[ATTR_HEALTHY],
                ATTR_SUPPORTED: supervisor_info[ATTR_SUPPORTED],
                ATTR_ARCH: supervisor_info[ATTR_ARCH],
            }

        if operating_system_info.get(ATTR_BOARD) is not None:
            payload[ATTR_OPERATING_SYSTEM] = {
                ATTR_BOARD: operating_system_info[ATTR_BOARD],
                ATTR_VERSION: operating_system_info[ATTR_VERSION],
            }

        if self.preferences.get(ATTR_USAGE, False) or self.preferences.get(
            ATTR_STATISTICS, False
        ):
            configured_integrations = await asyncio.gather(
                *[
                    async_get_integration(self.opp, domain)
                    for domain in async_get_loaded_integrations(self.opp)
                ],
                return_exceptions=True,
            )

            for integration in configured_integrations:
                if isinstance(integration, IntegrationNotFound):
                    continue

                if isinstance(integration, BaseException):
                    raise integration

                if integration.disabled:
                    continue

                if not integration.is_built_in:
                    custom_integrations.append(
                        {
                            ATTR_DOMAIN: integration.domain,
                            ATTR_VERSION: integration.version,
                        }
                    )
                    continue

                integrations.append(integration.domain)

            if supervisor_info is not None:
                installed_addons = await asyncio.gather(
                    *[
                        oppio.async_get_addon_info(self.opp, addon[ATTR_SLUG])
                        for addon in supervisor_info[ATTR_ADDONS]
                    ]
                )
                for addon in installed_addons:
                    addons.append(
                        {
                            ATTR_SLUG: addon[ATTR_SLUG],
                            ATTR_PROTECTED: addon[ATTR_PROTECTED],
                            ATTR_VERSION: addon[ATTR_VERSION],
                            ATTR_AUTO_UPDATE: addon[ATTR_AUTO_UPDATE],
                        }
                    )

        if self.preferences.get(ATTR_USAGE, False):
            payload[ATTR_INTEGRATIONS] = integrations
            payload[ATTR_CUSTOM_INTEGRATIONS] = custom_integrations
            if supervisor_info is not None:
                payload[ATTR_ADDONS] = addons

        if self.preferences.get(ATTR_STATISTICS, False):
            payload[ATTR_STATE_COUNT] = len(self.opp.states.async_all())
            payload[ATTR_AUTOMATION_COUNT] = len(
                self.opp.states.async_all(AUTOMATION_DOMAIN)
            )
            payload[ATTR_INTEGRATION_COUNT] = len(integrations)
            if supervisor_info is not None:
                payload[ATTR_ADDON_COUNT] = len(addons)
            payload[ATTR_USER_COUNT] = len(
                [
                    user
                    for user in await self.opp.auth.async_get_users()
                    if not user.system_generated
                ]
            )

        try:
            with async_timeout.timeout(30):
                response = await self.session.post(self.endpoint, json=payload)
                if response.status == 200:
                    LOGGER.info(
                        (
                            "Submitted analytics to Open Peer Power servers. "
                            "Information submitted includes %s"
                        ),
                        payload,
                    )
                else:
                    LOGGER.warning(
                        "Sending analytics failed with statuscode %s from %s",
                        response.status,
                        self.endpoint,
                    )
        except asyncio.TimeoutError:
            LOGGER.error("Timeout sending analytics to %s", ANALYTICS_ENDPOINT_URL)
        except aiohttp.ClientError as err:
            LOGGER.error(
                "Error sending analytics to %s: %r", ANALYTICS_ENDPOINT_URL, err
            )
