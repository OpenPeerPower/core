"""Account linking via the cloud."""
import asyncio
import logging
from typing import Any

import aiohttp
from opp_net import account_link

from openpeerpower.const import MAJOR_VERSION, MINOR_VERSION, PATCH_VERSION
from openpeerpower.core import OpenPeerPower, callback
from openpeerpower.helpers import config_entry_oauth2_flow, event

from .const import DOMAIN

DATA_SERVICES = "cloud_account_link_services"
CACHE_TIMEOUT = 3600
_LOGGER = logging.getLogger(__name__)


@callback
def async_setup(opp: OpenPeerPower):
    """Set up cloud account link."""
    config_entry_oauth2_flow.async_add_implementation_provider(
        opp, DOMAIN, async_provide_implementation
    )


async def async_provide_implementation(opp: OpenPeerPower, domain: str):
    """Provide an implementation for a domain."""
    services = await _get_services(opp)

    for service in services:
        if service["service"] == domain and _is_older(service["min_version"]):
            return CloudOAuth2Implementation(opp, domain)

    return


@callback
def _is_older(version: str) -> bool:
    """Test if a version is older than the current OP version."""
    version_parts = version.split(".")

    if len(version_parts) != 3:
        return False

    try:
        version_parts = [int(val) for val in version_parts]
    except ValueError:
        return False

    patch_number_str = ""

    for char in PATCH_VERSION:
        if char.isnumeric():
            patch_number_str += char
        else:
            break

    try:
        patch_number = int(patch_number_str)
    except ValueError:
        patch_number = 0

    cur_version_parts = [MAJOR_VERSION, MINOR_VERSION, patch_number]

    return version_parts <= cur_version_parts


async def _get_services(opp):
    """Get the available services."""
    services = opp.data.get(DATA_SERVICES)

    if services is not None:
        return services

    try:
        services = await account_link.async_fetch_available_services(opp.data[DOMAIN])
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return []

    opp.data[DATA_SERVICES] = services

    @callback
    def clear_services(_now):
        """Clear services cache."""
        opp.data.pop(DATA_SERVICES, None)

    event.async_call_later(opp, CACHE_TIMEOUT, clear_services)

    return services


class CloudOAuth2Implementation(config_entry_oauth2_flow.AbstractOAuth2Implementation):
    """Cloud implementation of the OAuth2 flow."""

    def __init__(self, opp: OpenPeerPower, service: str):
        """Initialize cloud OAuth2 implementation."""
        self.opp = opp
        self.service = service

    @property
    def name(self) -> str:
        """Name of the implementation."""
        return "Open Peer Power Cloud"

    @property
    def domain(self) -> str:
        """Domain that is providing the implementation."""
        return DOMAIN

    async def async_generate_authorize_url(self, flow_id: str) -> str:
        """Generate a url for the user to authorize."""
        helper = account_link.AuthorizeAccountHelper(
            self.opp.data[DOMAIN], self.service
        )
        authorize_url = await helper.async_get_authorize_url()

        async def await_tokens():
            """Wait for tokens and pass them on when received."""
            try:
                tokens = await helper.async_get_tokens()

            except asyncio.TimeoutError:
                _LOGGER.info("Timeout fetching tokens for flow %s", flow_id)
            except account_link.AccountLinkException as err:
                _LOGGER.info(
                    "Failed to fetch tokens for flow %s: %s", flow_id, err.code
                )
            else:
                await self.opp.config_entries.flow.async_configure(
                    flow_id=flow_id, user_input=tokens
                )

        self.opp.async_create_task(await_tokens())

        return authorize_url

    async def async_resolve_external_data(self, external_data: Any) -> dict:
        """Resolve external data to tokens."""
        # We already passed in tokens
        return external_data

    async def _async_refresh_token(self, token: dict) -> dict:
        """Refresh a token."""
        return await account_link.async_fetch_access_token(
            self.opp.data[DOMAIN], self.service, token["refresh_token"]
        )
