"""Tests for the SRP Energy integration."""
from unittest.mock import patch

from openpeerpower import config_entries
from openpeerpower.components import srp_energy
from openpeerpower.const import CONF_ID, CONF_NAME, CONF_PASSWORD, CONF_USERNAME

from tests.common import MockConfigEntry

ENTRY_OPTIONS = {}

ENTRY_CONFIG = {
    CONF_NAME: "Test",
    CONF_ID: "123456789",
    CONF_USERNAME: "abba",
    CONF_PASSWORD: "ana",
    srp_energy.const.CONF_IS_TOU: False,
}


async def init_integration(
   .opp,
    config=None,
    options=None,
    entry_id="1",
    source="user",
    side_effect=None,
    usage=None,
):
    """Set up the srp_energy integration in Open Peer Power."""
    if not config:
        config = ENTRY_CONFIG

    if not options:
        options = ENTRY_OPTIONS

    config_entry = MockConfigEntry(
        domain=srp_energy.SRP_ENERGY_DOMAIN,
        source=source,
        data=config,
        connection_class=config_entries.CONN_CLASS_CLOUD_POLL,
        options=options,
        entry_id=entry_id,
    )

    with patch("srpenergy.client.SrpEnergyClient"), patch(
        "openpeerpower.components.srp_energy.SrpEnergyClient", side_effect=side_effect
    ), patch("srpenergy.client.SrpEnergyClient.usage", return_value=usage), patch(
        "openpeerpower.components.srp_energy.SrpEnergyClient.usage", return_value=usage
    ):

        config_entry.add_to.opp.opp)
        await.opp.config_entries.async_setup(config_entry.entry_id)
        await.opp.async_block_till_done()

    return config_entry
