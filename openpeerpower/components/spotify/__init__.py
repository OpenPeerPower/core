"""The spotify integration."""

import aiohttp
from spotipy import Spotify, SpotifyException
import voluptuous as vol

from openpeerpower.components.media_player import DOMAIN as MEDIA_PLAYER_DOMAIN
from openpeerpower.components.spotify import config_flow
from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import ATTR_CREDENTIALS, CONF_CLIENT_ID, CONF_CLIENT_SECRET
from openpeerpower.core import OpenPeerPower
from openpeerpower.exceptions import ConfigEntryNotReady
from openpeerpower.helpers import config_entry_oauth2_flow, config_validation as cv
from openpeerpower.helpers.config_entry_oauth2_flow import (
    OAuth2Session,
    async_get_config_entry_implementation,
)
from openpeerpower.helpers.typing import ConfigType

from .const import (
    DATA_SPOTIFY_CLIENT,
    DATA_SPOTIFY_ME,
    DATA_SPOTIFY_SESSION,
    DOMAIN,
    SPOTIFY_SCOPES,
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Inclusive(CONF_CLIENT_ID, ATTR_CREDENTIALS): cv.string,
                vol.Inclusive(CONF_CLIENT_SECRET, ATTR_CREDENTIALS): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(opp: OpenPeerPower, config: ConfigType) -> bool:
    """Set up the Spotify integration."""
    if DOMAIN not in config:
        return True

    if CONF_CLIENT_ID in config[DOMAIN]:
        config_flow.SpotifyFlowHandler.async_register_implementation(
            opp,
            config_entry_oauth2_flow.LocalOAuth2Implementation(
                opp,
                DOMAIN,
                config[DOMAIN][CONF_CLIENT_ID],
                config[DOMAIN][CONF_CLIENT_SECRET],
                "https://accounts.spotify.com/authorize",
                "https://accounts.spotify.com/api/token",
            ),
        )

    return True


async def async_setup_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Set up Spotify from a config entry."""
    implementation = await async_get_config_entry_implementation(opp, entry)
    session = OAuth2Session(opp, entry, implementation)

    try:
        await session.async_ensure_token_valid()
    except aiohttp.ClientError as err:
        raise ConfigEntryNotReady from err

    spotify = Spotify(auth=session.token["access_token"])

    try:
        current_user = await opp.async_add_executor_job(spotify.me)
    except SpotifyException as err:
        raise ConfigEntryNotReady from err

    opp.data.setdefault(DOMAIN, {})
    opp.data[DOMAIN][entry.entry_id] = {
        DATA_SPOTIFY_CLIENT: spotify,
        DATA_SPOTIFY_ME: current_user,
        DATA_SPOTIFY_SESSION: session,
    }

    if not set(session.token["scope"].split(" ")).issuperset(SPOTIFY_SCOPES):
        opp.async_create_task(
            opp.config_entries.flow.async_init(
                DOMAIN,
                context={"source": "reauth"},
                data=entry.data,
            )
        )

    opp.async_create_task(
        opp.config_entries.async_forward_entry_setup(entry, MEDIA_PLAYER_DOMAIN)
    )
    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry) -> bool:
    """Unload Spotify config entry."""
    # Unload entities for this entry/device.
    await opp.config_entries.async_forward_entry_unload(entry, MEDIA_PLAYER_DOMAIN)

    # Cleanup
    del opp.data[DOMAIN][entry.entry_id]
    if not opp.data[DOMAIN]:
        del opp.data[DOMAIN]

    return True
