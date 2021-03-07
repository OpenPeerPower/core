"""The xbox integration."""
import asyncio
from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Dict, Optional

import voluptuous as vol
from xbox.webapi.api.client import XboxLiveClient
from xbox.webapi.api.provider.catalog.const import SYSTEM_PFN_ID_MAP
from xbox.webapi.api.provider.catalog.models import AlternateIdType, Product
from xbox.webapi.api.provider.people.models import (
    PeopleResponse,
    Person,
    PresenceDetail,
)
from xbox.webapi.api.provider.smartglass.models import (
    SmartglassConsoleList,
    SmartglassConsoleStatus,
)

from openpeerpower.config_entries import ConfigEntry
from openpeerpower.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from openpeerpower.core import OpenPeerPower
from openpeerpower.helpers import (
    aiohttp_client,
    config_entry_oauth2_flow,
    config_validation as cv,
)
from openpeerpower.helpers.typing import OpenPeerPowerType
from openpeerpower.helpers.update_coordinator import DataUpdateCoordinator

from . import api, config_flow
from .const import DOMAIN, OAUTH2_AUTHORIZE, OAUTH2_TOKEN

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

PLATFORMS = ["media_player", "remote", "binary_sensor", "sensor"]


async def async_setup(opp: OpenPeerPower, config: dict):
    """Set up the xbox component."""
    opp.data[DOMAIN] = {}

    if DOMAIN not in config:
        return True

    config_flow.OAuth2FlowHandler.async_register_implementation(
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
    """Set up xbox from a config entry."""
    implementation = (
        await config_entry_oauth2_flow.async_get_config_entry_implementation(opp, entry)
    )
    session = config_entry_oauth2_flow.OAuth2Session(opp, entry, implementation)
    auth = api.AsyncConfigEntryAuth(
        aiohttp_client.async_get_clientsession(opp), session
    )

    client = XboxLiveClient(auth)
    consoles: SmartglassConsoleList = await client.smartglass.get_console_list()
    _LOGGER.debug(
        "Found %d consoles: %s",
        len(consoles.result),
        consoles.dict(),
    )

    coordinator = XboxUpdateCoordinator(opp, client, consoles)
    await coordinator.async_refresh()

    opp.data[DOMAIN][entry.entry_id] = {
        "client": XboxLiveClient(auth),
        "consoles": consoles,
        "coordinator": coordinator,
    }

    for platform in PLATFORMS:
        opp.async_create_task(
            opp.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(opp: OpenPeerPower, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                opp.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        # Unsub from coordinator updates
        opp.data[DOMAIN][entry.entry_id]["sensor_unsub"]()
        opp.data[DOMAIN][entry.entry_id]["binary_sensor_unsub"]()
        opp.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


@dataclass
class ConsoleData:
    """Xbox console status data."""

    status: SmartglassConsoleStatus
    app_details: Optional[Product]


@dataclass
class PresenceData:
    """Xbox user presence data."""

    xuid: str
    gamertag: str
    display_pic: str
    online: bool
    status: str
    in_party: bool
    in_game: bool
    in_multiplayer: bool
    gamer_score: str
    gold_tenure: Optional[str]
    account_tier: str


@dataclass
class XboxData:
    """Xbox dataclass for update coordinator."""

    consoles: Dict[str, ConsoleData]
    presence: Dict[str, PresenceData]


class XboxUpdateCoordinator(DataUpdateCoordinator):
    """Store Xbox Console Status."""

    def __init__(
        self,
        opp: OpenPeerPowerType,
        client: XboxLiveClient,
        consoles: SmartglassConsoleList,
    ) -> None:
        """Initialize."""
        super().__init__(
            opp,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=10),
        )
        self.data: XboxData = XboxData({}, [])
        self.client: XboxLiveClient = client
        self.consoles: SmartglassConsoleList = consoles

    async def _async_update_data(self) -> XboxData:
        """Fetch the latest console status."""
        # Update Console Status
        new_console_data: Dict[str, ConsoleData] = {}
        for console in self.consoles.result:
            current_state: Optional[ConsoleData] = self.data.consoles.get(console.id)
            status: SmartglassConsoleStatus = (
                await self.client.smartglass.get_console_status(console.id)
            )

            _LOGGER.debug(
                "%s status: %s",
                console.name,
                status.dict(),
            )

            # Setup focus app
            app_details: Optional[Product] = None
            if current_state is not None:
                app_details = current_state.app_details

            if status.focus_app_aumid:
                if (
                    not current_state
                    or status.focus_app_aumid != current_state.status.focus_app_aumid
                ):
                    app_id = status.focus_app_aumid.split("!")[0]
                    id_type = AlternateIdType.PACKAGE_FAMILY_NAME
                    if app_id in SYSTEM_PFN_ID_MAP:
                        id_type = AlternateIdType.LEGACY_XBOX_PRODUCT_ID
                        app_id = SYSTEM_PFN_ID_MAP[app_id][id_type]
                    catalog_result = (
                        await self.client.catalog.get_product_from_alternate_id(
                            app_id, id_type
                        )
                    )
                    if catalog_result and catalog_result.products:
                        app_details = catalog_result.products[0]
            else:
                app_details = None

            new_console_data[console.id] = ConsoleData(
                status=status, app_details=app_details
            )

        # Update user presence
        presence_data = {}
        batch: PeopleResponse = await self.client.people.get_friends_own_batch(
            [self.client.xuid]
        )
        own_presence: Person = batch.people[0]
        presence_data[own_presence.xuid] = _build_presence_data(own_presence)

        friends: PeopleResponse = await self.client.people.get_friends_own()
        for friend in friends.people:
            if not friend.is_favorite:
                continue

            presence_data[friend.xuid] = _build_presence_data(friend)

        return XboxData(new_console_data, presence_data)


def _build_presence_data(person: Person) -> PresenceData:
    """Build presence data from a person."""
    active_app: Optional[PresenceDetail] = None
    try:
        active_app = next(
            presence for presence in person.presence_details if presence.is_primary
        )
    except StopIteration:
        pass

    return PresenceData(
        xuid=person.xuid,
        gamertag=person.gamertag,
        display_pic=person.display_pic_raw,
        online=person.presence_state == "Online",
        status=person.presence_text,
        in_party=person.multiplayer_summary.in_party > 0,
        in_game=active_app and active_app.is_game,
        in_multiplayer=person.multiplayer_summary.in_multiplayer_session,
        gamer_score=person.gamer_score,
        gold_tenure=person.detail.tenure,
        account_tier=person.detail.account_tier,
    )
