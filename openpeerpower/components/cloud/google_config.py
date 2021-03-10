"""Google config for Cloud."""
import asyncio
import logging

from opp_net import Cloud, cloud_api
from opp_net.google_report_state import ErrorResponse

from openpeerpower.components.google_assistant.helpers import AbstractConfig
from openpeerpower.const import (
    CLOUD_NEVER_EXPOSED_ENTITIES,
    EVENT_OPENPEERPOWER_STARTED,
    HTTP_OK,
)
from openpeerpower.core import CoreState, split_entity_id
from openpeerpower.helpers import entity_registry

from .const import (
    CONF_ENTITY_CONFIG,
    DEFAULT_DISABLE_2FA,
    PREF_DISABLE_2FA,
    PREF_SHOULD_EXPOSE,
)
from .prefs import CloudPreferences

_LOGGER = logging.getLogger(__name__)


class CloudGoogleConfig(AbstractConfig):
    """HA Cloud Configuration for Google Assistant."""

    def __init__(
        self, opp, config, cloud_user: str, prefs: CloudPreferences, cloud: Cloud
    ):
        """Initialize the Google config."""
        super().__init__(opp)
        self._config = config
        self._user = cloud_user
        self._prefs = prefs
        self._cloud = cloud
        self._cur_entity_prefs = self._prefs.google_entity_configs
        self._cur_default_expose = self._prefs.google_default_expose
        self._sync_entities_lock = asyncio.Lock()
        self._sync_on_started = False

    @property
    def enabled(self):
        """Return if Google is enabled."""
        return (
            self._cloud.is_logged_in
            and not self._cloud.subscription_expired
            and self._prefs.google_enabled
        )

    @property
    def entity_config(self):
        """Return entity config."""
        return self._config.get(CONF_ENTITY_CONFIG) or {}

    @property
    def secure_devices_pin(self):
        """Return entity config."""
        return self._prefs.google_secure_devices_pin

    @property
    def should_report_state(self):
        """Return if states should be proactively reported."""
        return self._cloud.is_logged_in and self._prefs.google_report_state

    @property
    def local_sdk_webhook_id(self):
        """Return the local SDK webhook.

        Return None to disable the local SDK.
        """
        return self._prefs.google_local_webhook_id

    @property
    def local_sdk_user_id(self):
        """Return the user ID to be used for actions received via the local SDK."""
        return self._user

    @property
    def cloud_user(self):
        """Return Cloud User account."""
        return self._user

    async def async_initialize(self):
        """Perform async initialization of config."""
        await super().async_initialize()
        # Remove bad data that was there until 0.103.6 - Jan 6, 2020
        self._store.pop_agent_user_id(self._user)

        self._prefs.async_listen_updates(self._async_prefs_updated)

        self.opp.bus.async_listen(
            entity_registry.EVENT_ENTITY_REGISTRY_UPDATED,
            self._handle_entity_registry_updated,
        )

    def should_expose(self, state):
        """If a state object should be exposed."""
        return self._should_expose_entity_id(state.entity_id)

    def _should_expose_entity_id(self, entity_id):
        """If an entity ID should be exposed."""
        if entity_id in CLOUD_NEVER_EXPOSED_ENTITIES:
            return False

        if not self._config["filter"].empty_filter:
            return self._config["filter"](entity_id)

        entity_configs = self._prefs.google_entity_configs
        entity_config = entity_configs.get(entity_id, {})
        entity_expose = entity_config.get(PREF_SHOULD_EXPOSE)
        if entity_expose is not None:
            return entity_expose

        default_expose = self._prefs.google_default_expose

        # Backwards compat
        if default_expose is None:
            return True

        return split_entity_id(entity_id)[0] in default_expose

    @property
    def agent_user_id(self):
        """Return Agent User Id to use for query responses."""
        return self._cloud.username

    def get_agent_user_id(self, context):
        """Get agent user ID making request."""
        return self.agent_user_id

    def should_2fa(self, state):
        """If an entity should be checked for 2FA."""
        entity_configs = self._prefs.google_entity_configs
        entity_config = entity_configs.get(state.entity_id, {})
        return not entity_config.get(PREF_DISABLE_2FA, DEFAULT_DISABLE_2FA)

    async def async_report_state(self, message, agent_user_id: str):
        """Send a state report to Google."""
        try:
            await self._cloud.google_report_state.async_send_message(message)
        except ErrorResponse as err:
            _LOGGER.warning("Error reporting state - %s: %s", err.code, err.message)

    async def _async_request_sync_devices(self, agent_user_id: str):
        """Trigger a sync with Google."""
        if self._sync_entities_lock.locked():
            return HTTP_OK

        async with self._sync_entities_lock:
            resp = await cloud_api.async_google_actions_request_sync(self._cloud)
            return resp.status

    async def _async_prefs_updated(self, prefs):
        """Handle updated preferences."""
        if self.should_report_state != self.is_reporting_state:
            if self.should_report_state:
                self.async_enable_report_state()
            else:
                self.async_disable_report_state()

            # State reporting is reported as a property on entities.
            # So when we change it, we need to sync all entities.
            await self.async_sync_entities_all()

        # If entity prefs are the same or we have filter in config.yaml,
        # don't sync.
        elif (
            self._cur_entity_prefs is not prefs.google_entity_configs
            or self._cur_default_expose is not prefs.google_default_expose
        ) and self._config["filter"].empty_filter:
            self.async_schedule_google_sync_all()

        if self.enabled and not self.is_local_sdk_active:
            self.async_enable_local_sdk()
        elif not self.enabled and self.is_local_sdk_active:
            self.async_disable_local_sdk()

        self._cur_entity_prefs = prefs.google_entity_configs
        self._cur_default_expose = prefs.google_default_expose

    async def _handle_entity_registry_updated(self, event):
        """Handle when entity registry updated."""
        if not self.enabled or not self._cloud.is_logged_in:
            return

        # Only consider entity registry updates if info relevant for Google has changed
        if event.data["action"] == "update" and not bool(
            set(event.data["changes"]) & entity_registry.ENTITY_DESCRIBING_ATTRIBUTES
        ):
            return

        entity_id = event.data["entity_id"]

        if not self._should_expose_entity_id(entity_id):
            return

        if self.opp.state == CoreState.running:
            self.async_schedule_google_sync_all()
            return

        if self._sync_on_started:
            return

        self._sync_on_started = True

        async def sync_google(_):
            """Sync entities to Google."""
            await self.async_sync_entities_all()

        self.opp.bus.async_listen_once(EVENT_OPENPEERPOWER_STARTED, sync_google)
