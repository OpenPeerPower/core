"""Tests for the Synology DSM component."""
from unittest.mock import patch

import pytest

from openpeerpower.components.synology_dsm.const import DOMAIN, SERVICES
from openpeerpower.const import (
    CONF_HOST,
    CONF_MAC,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
)
from openpeerpower.helpers.typing import OpenPeerPowerType

from .consts import HOST, MACS, PASSWORD, PORT, USE_SSL, USERNAME

from tests.common import MockConfigEntry


@pytest.mark.no_bypass_setup
async def test_services_registered.opp: OpenPeerPowerType):
    """Test if all services are registered."""
    with patch(
        "openpeerpower.components.synology_dsm.SynoApi.async_setup", return_value=True
    ), patch("openpeerpower.components.synology_dsm.PLATFORMS", return_value=[]):
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_HOST: HOST,
                CONF_PORT: PORT,
                CONF_SSL: USE_SSL,
                CONF_USERNAME: USERNAME,
                CONF_PASSWORD: PASSWORD,
                CONF_MAC: MACS[0],
            },
        )
        entry.add_to_opp(opp)
        assert await opp.config_entries.async_setup(entry.entry_id)
        for service in SERVICES:
            assert opp.services.has_service(DOMAIN, service)
