"""Tests of the initialization of the twinly integration."""

from unittest.mock import patch
from uuid import uuid4

from openpeerpower.components.twinkly import async_setup_entry, async_unload_entry
from openpeerpower.components.twinkly.const import (
    CONF_ENTRY_HOST,
    CONF_ENTRY_ID,
    CONF_ENTRY_MODEL,
    CONF_ENTRY_NAME,
    DOMAIN as TWINKLY_DOMAIN,
)
from openpeerpower.core import OpenPeerPower

from tests.common import MockConfigEntry
from tests.components.twinkly import TEST_HOST, TEST_MODEL, TEST_NAME_ORIGINAL


async def test_setup_entry(opp: OpenPeerPower):
    """Validate that setup entry also configure the client."""

    id = str(uuid4())
    config_entry = MockConfigEntry(
        domain=TWINKLY_DOMAIN,
        data={
            CONF_ENTRY_HOST: TEST_HOST,
            CONF_ENTRY_ID: id,
            CONF_ENTRY_NAME: TEST_NAME_ORIGINAL,
            CONF_ENTRY_MODEL: TEST_MODEL,
        },
        entry_id=id,
    )

    def setup_mock(_, __):
        return True

    with patch(
        "openpeerpower.config_entries.ConfigEntries.async_forward_entry_setup",
        side_effect=setup_mock,
    ):
        await async_setup_entry(opp, config_entry)

    assert opp.data[TWINKLY_DOMAIN][id] is not None


async def test_unload_entry(opp: OpenPeerPower):
    """Validate that unload entry also clear the client."""

    id = str(uuid4())
    config_entry = MockConfigEntry(
        domain=TWINKLY_DOMAIN,
        data={
            CONF_ENTRY_HOST: TEST_HOST,
            CONF_ENTRY_ID: id,
            CONF_ENTRY_NAME: TEST_NAME_ORIGINAL,
            CONF_ENTRY_MODEL: TEST_MODEL,
        },
        entry_id=id,
    )

    # Put random content at the location where the client should have been placed by setup
    opp.data.setdefault(TWINKLY_DOMAIN, {})[id] = config_entry

    await async_unload_entry(opp, config_entry)

    assert opp.data[TWINKLY_DOMAIN].get(id) is None
