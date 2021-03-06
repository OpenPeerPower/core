"""Provides data updates from the Control4 controller for platforms."""
import logging

from pyControl4.account import C4Account
from pyControl4.director import C4Director
from pyControl4.error_handling import BadToken

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_HOST, CONF_PASSWORD, CONF_TOKEN, CONF_USERNAME
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers import aiohttp_client

from .const import (
    CONF_ACCOUNT,
    CONF_CONTROLLER_UNIQUE_ID,
    CONF_DIRECTOR,
    CONF_DIRECTOR_TOKEN_EXPIRATION,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def director_update_data(
    opp: OpenPeerPower, entry: ConfigEntry, var: str
) -> dict:
    """Retrieve data from the Control4 director for update_coordinator."""
    # possibly implement usage of director_token_expiration to start
    # token refresh without waiting for error to occur
    try:
        director = opp.data[DOMAIN][entry.entry_id][CONF_DIRECTOR]
        data = await director.getAllItemVariableValue(var)
    except BadToken:
        _LOGGER.info("Updating Control4 director token")
        await refresh_tokens(opp, entry)
        director = opp.data[DOMAIN][entry.entry_id][CONF_DIRECTOR]
        data = await director.getAllItemVariableValue(var)
    return {key["id"]: key for key in data}


async def refresh_tokens(opp: OpenPeerPower, entry: ConfigEntry):
    """Store updated authentication and director tokens in opp.data."""
    config = entry.data
    account_session = aiohttp_client.async_get_clientsession(opp)

    account = C4Account(config[CONF_USERNAME], config[CONF_PASSWORD], account_session)
    await account.getAccountBearerToken()

    controller_unique_id = config[CONF_CONTROLLER_UNIQUE_ID]
    director_token_dict = await account.getDirectorBearerToken(controller_unique_id)
    director_session = aiohttp_client.async_get_clientsession(opp, verify_ssl=False)

    director = C4Director(
        config[CONF_HOST], director_token_dict[CONF_TOKEN], director_session
    )
    director_token_expiry = director_token_dict["token_expiration"]

    _LOGGER.debug("Saving new tokens in opp data")
    entry_data = opp.data[DOMAIN][entry.entry_id]
    entry_data[CONF_ACCOUNT] = account
    entry_data[CONF_DIRECTOR] = director
    entry_data[CONF_DIRECTOR_TOKEN_EXPIRATION] = director_token_expiry
