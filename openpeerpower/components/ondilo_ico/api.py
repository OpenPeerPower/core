"""API for Ondilo ICO bound to Open Peer Power OAuth."""
from asyncio import run_coroutine_threadsafe
import logging

from ondilo import Ondilo

from openpeerpower import config_entries, core
from openpeerpower.helpers import config_entry_oauth2_flow

_LOGGER = logging.getLogger(__name__)


class OndiloClient(Ondilo):
    """Provide Ondilo ICO authentication tied to an OAuth2 based config entry."""

    def __init__(
        self,
        opp: core.OpenPeerPower,
        config_entry: config_entries.ConfigEntry,
        implementation: config_entry_oauth2_flow.AbstractOAuth2Implementation,
    ):
        """Initialize Ondilo ICO Auth."""
        self.opp = opp
        self.config_entry = config_entry
        self.session = config_entry_oauth2_flow.OAuth2Session(
            opp, config_entry, implementation
        )
        super().__init__(self.session.token)

    def refresh_tokens(self) -> dict:
        """Refresh and return new Ondilo ICO tokens using Open Peer Power OAuth2 session."""
        run_coroutine_threadsafe(
            self.session.async_ensure_token_valid(), self.opp.loop
        ).result()

        return self.session.token

    def get_all_pools_data(self) -> dict:
        """Fetch pools and add pool details and last measures to pool data."""

        pools = self.get_pools()
        for pool in pools:
            _LOGGER.debug(
                "Retrieving data for pool/spa: %s, id: %d", pool["name"], pool["id"]
            )
            pool["ICO"] = self.get_ICO_details(pool["id"])
            pool["sensors"] = self.get_last_pool_measures(pool["id"])
            _LOGGER.debug("Retrieved the following sensors data: %s", pool["sensors"])

        return pools
