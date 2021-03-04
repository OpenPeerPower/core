"""Config flow for Ambiclimate."""
import logging

import ambiclimate

from openpeerpower import config_entries
from openpeerpower.components.http import OpenPeerPowerView
from openpeerpower.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from openpeerpower.core import callback
from openpeerpower.helpers.aiohttp_client import async_get_clientsession
from openpeerpower.helpers.network import get_url

from .const import (
    AUTH_CALLBACK_NAME,
    AUTH_CALLBACK_PATH,
    DOMAIN,
    STORAGE_KEY,
    STORAGE_VERSION,
)

DATA_AMBICLIMATE_IMPL = "ambiclimate_flow_implementation"

_LOGGER = logging.getLogger(__name__)


@callback
def register_flow_implementation(opp, client_id, client_secret):
    """Register a ambiclimate implementation.

    client_id: Client id.
    client_secret: Client secret.
    """
    opp.data.setdefault(DATA_AMBICLIMATE_IMPL, {})

    opp.data[DATA_AMBICLIMATE_IMPL] = {
        CONF_CLIENT_ID: client_id,
        CONF_CLIENT_SECRET: client_secret,
    }


@config_entries.HANDLERS.register("ambiclimate")
class AmbiclimateFlowHandler(config_entries.ConfigFlow):
    """Handle a config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize flow."""
        self._registered_view = False
        self._oauth = None

    async def async_step_user(self, user_input=None):
        """Handle external yaml configuration."""
        if self.opp.config_entries.async_entries(DOMAIN):
            return self.async_abort(reason="already_configured")

        config = self.opp.data.get(DATA_AMBICLIMATE_IMPL, {})

        if not config:
            _LOGGER.debug("No config")
            return self.async_abort(reason="missing_configuration")

        return await self.async_step_auth()

    async def async_step_auth(self, user_input=None):
        """Handle a flow start."""
        if self.opp.config_entries.async_entries(DOMAIN):
            return self.async_abort(reason="already_configured")

        errors = {}

        if user_input is not None:
            errors["base"] = "follow_link"

        if not self._registered_view:
            self._generate_view()

        return self.async_show_form(
            step_id="auth",
            description_placeholders={
                "authorization_url": await self._get_authorize_url(),
                "cb_url": self._cb_url(),
            },
            errors=errors,
        )

    async def async_step_code(self, code=None):
        """Received code for authentication."""
        if self.opp.config_entries.async_entries(DOMAIN):
            return self.async_abort(reason="already_configured")

        token_info = await self._get_token_info(code)

        if token_info is None:
            return self.async_abort(reason="access_token")

        config = self.opp.data[DATA_AMBICLIMATE_IMPL].copy()
        config["callback_url"] = self._cb_url()

        return self.async_create_entry(title="Ambiclimate", data=config)

    async def _get_token_info(self, code):
        oauth = self._generate_oauth()
        try:
            token_info = await oauth.get_access_token(code)
        except ambiclimate.AmbiclimateOauthError:
            _LOGGER.error("Failed to get access token", exc_info=True)
            return None

        store = self.opp.helpers.storage.Store(STORAGE_VERSION, STORAGE_KEY)
        await store.async_save(token_info)

        return token_info

    def _generate_view(self):
        self.opp.http.register_view(AmbiclimateAuthCallbackView())
        self._registered_view = True

    def _generate_oauth(self):
        config = self.opp.data[DATA_AMBICLIMATE_IMPL]
        clientsession = async_get_clientsession(self.opp)
        callback_url = self._cb_url()

        return ambiclimate.AmbiclimateOAuth(
            config.get(CONF_CLIENT_ID),
            config.get(CONF_CLIENT_SECRET),
            callback_url,
            clientsession,
        )

    def _cb_url(self):
        return f"{get_url(self.opp)}{AUTH_CALLBACK_PATH}"

    async def _get_authorize_url(self):
        oauth = self._generate_oauth()
        return oauth.get_authorize_url()


class AmbiclimateAuthCallbackView(OpenPeerPowerView):
    """Ambiclimate Authorization Callback View."""

    requires_auth = False
    url = AUTH_CALLBACK_PATH
    name = AUTH_CALLBACK_NAME

    async def get(self, request):
        """Receive authorization token."""
        code = request.query.get("code")
        if code is None:
            return "No code"
        opp = request.app["opp"]
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN, context={"source": "code"}, data=code
            )
        )
        return "OK!"
