"""The Flick Electric integration."""

from datetime import datetime as dt

from pyflick import FlickAPI
from pyflick.authentication import AbstractFlickAuth
from pyflick.const import DEFAULT_CLIENT_ID, DEFAULT_CLIENT_SECRET

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import (
    CONF_ACCESS_TOKEN,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_PASSWORD,
    CONF_USERNAME,
)
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers import aiohttp_client

from .const import CONF_TOKEN_EXPIRES_IN, CONF_TOKEN_EXPIRY, DOMAIN

CONF_ID_TOKEN = "id_token"


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the Flick Electric component."""
    opp.data[DOMAIN] = {}
    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Set up Flick Electric from a config entry."""
    auth = OppFlickAuth.opp, entry)

    opp.data[DOMAIN][entry.entry_id] = FlickAPI(auth)

    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    if await opp.config_entries.async_forward_entry_unload(entry, "sensor"):
        opp.data[DOMAIN].pop(entry.entry_id)
        return True

    return False


class OppFlickAuth(AbstractFlickAuth):
    """Implementation of AbstractFlickAuth based on a Open Peer Power entity config."""

    def __init__(self, opp: OpenPeerPower, entry: ConfigEntry):
        """Flick authention based on a Open Peer Power entity config."""
        super().__init__(aiohttp_client.async_get_clientsession(opp))
        self._entry = entry
        self.opp = opp

    async def _get_entry_token(self):
        # No token saved, generate one
        if (
            CONF_TOKEN_EXPIRY not in self._entry.data
            or CONF_ACCESS_TOKEN not in self._entry.data
        ):
            await self._update_token()

        # Token is expired, generate a new one
        if self._entry.data[CONF_TOKEN_EXPIRY] <= dt.now().timestamp():
            await self._update_token()

        return self._entry.data[CONF_ACCESS_TOKEN]

    async def _update_token(self):
        token = await self.get_new_token(
            username=self._entry.data[CONF_USERNAME],
            password=self._entry.data[CONF_PASSWORD],
            client_id=self._entry.data.get(CONF_CLIENT_ID, DEFAULT_CLIENT_ID),
            client_secret=self._entry.data.get(
                CONF_CLIENT_SECRET, DEFAULT_CLIENT_SECRET
            ),
        )

        # Reduce expiry by an hour to avoid API being called after expiry
        expiry = dt.now().timestamp() + int(token[CONF_TOKEN_EXPIRES_IN] - 3600)

        self.opp.config_entries.async_update_entry(
            self._entry,
            data={
                **self._entry.data,
                CONF_ACCESS_TOKEN: token,
                CONF_TOKEN_EXPIRY: expiry,
            },
        )

    async def async_get_access_token(self):
        """Get Access Token from OPP Storage."""
        token = await self._get_entry_token()

        return token[CONF_ID_TOKEN]
