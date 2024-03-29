"""Test deCONZ component setup process."""

import asyncio
from unittest.mock import patch

from openpeerpower.components.deconz import (
    DeconzGateway,
    async_setup_entry,
    async_unload_entry,
    async_update_group_unique_id,
)
from openpeerpower.components.deconz.const import (
    CONF_GROUP_ID_BASE,
    DOMAIN as DECONZ_DOMAIN,
)
from openpeerpower.components.light import DOMAIN as LIGHT_DOMAIN
from openpeerpower.const import CONF_API_KEY, CONF_HOST, CONF_PORT
from openpeerpower.helpers import entity_registry as er

from .test_gateway import DECONZ_WEB_REQUEST, setup_deconz_integration

from tests.common import MockConfigEntry

ENTRY1_HOST = "1.2.3.4"
ENTRY1_PORT = 80
ENTRY1_API_KEY = "1234567890ABCDEF"
ENTRY1_BRIDGEID = "12345ABC"
ENTRY1_UUID = "456DEF"

ENTRY2_HOST = "2.3.4.5"
ENTRY2_PORT = 80
ENTRY2_API_KEY = "1234567890ABCDEF"
ENTRY2_BRIDGEID = "23456DEF"
ENTRY2_UUID = "789ACE"


async def setup_entry(opp, entry):
    """Test that setup entry works."""
    with patch.object(DeconzGateway, "async_setup", return_value=True), patch.object(
        DeconzGateway, "async_update_device_registry", return_value=True
    ):
        assert await async_setup_entry(opp, entry) is True


async def test_setup_entry_fails(opp):
    """Test setup entry fails if deCONZ is not available."""
    with patch("pydeconz.DeconzSession.initialize", side_effect=Exception):
        await setup_deconz_integration(opp)
    assert not opp.data[DECONZ_DOMAIN]


async def test_setup_entry_no_available_bridge(opp):
    """Test setup entry fails if deCONZ is not available."""
    with patch("pydeconz.DeconzSession.initialize", side_effect=asyncio.TimeoutError):
        await setup_deconz_integration(opp)
    assert not opp.data[DECONZ_DOMAIN]


async def test_setup_entry_successful(opp, aioclient_mock):
    """Test setup entry is successful."""
    config_entry = await setup_deconz_integration(opp, aioclient_mock)

    assert opp.data[DECONZ_DOMAIN]
    assert config_entry.unique_id in opp.data[DECONZ_DOMAIN]
    assert opp.data[DECONZ_DOMAIN][config_entry.unique_id].master


async def test_setup_entry_multiple_gateways(opp, aioclient_mock):
    """Test setup entry is successful with multiple gateways."""
    config_entry = await setup_deconz_integration(opp, aioclient_mock)
    aioclient_mock.clear_requests()

    data = {"config": {"bridgeid": "01234E56789B"}}
    with patch.dict(DECONZ_WEB_REQUEST, data):
        config_entry2 = await setup_deconz_integration(
            opp,
            aioclient_mock,
            entry_id="2",
            unique_id="01234E56789B",
        )

    assert len(opp.data[DECONZ_DOMAIN]) == 2
    assert opp.data[DECONZ_DOMAIN][config_entry.unique_id].master
    assert not opp.data[DECONZ_DOMAIN][config_entry2.unique_id].master


async def test_unload_entry(opp, aioclient_mock):
    """Test being able to unload an entry."""
    config_entry = await setup_deconz_integration(opp, aioclient_mock)
    assert opp.data[DECONZ_DOMAIN]

    assert await async_unload_entry(opp, config_entry)
    assert not opp.data[DECONZ_DOMAIN]


async def test_unload_entry_multiple_gateways(opp, aioclient_mock):
    """Test being able to unload an entry and master gateway gets moved."""
    config_entry = await setup_deconz_integration(opp, aioclient_mock)
    aioclient_mock.clear_requests()

    data = {"config": {"bridgeid": "01234E56789B"}}
    with patch.dict(DECONZ_WEB_REQUEST, data):
        config_entry2 = await setup_deconz_integration(
            opp,
            aioclient_mock,
            entry_id="2",
            unique_id="01234E56789B",
        )

    assert len(opp.data[DECONZ_DOMAIN]) == 2

    assert await async_unload_entry(opp, config_entry)

    assert len(opp.data[DECONZ_DOMAIN]) == 1
    assert opp.data[DECONZ_DOMAIN][config_entry2.unique_id].master


async def test_update_group_unique_id(opp):
    """Test successful migration of entry data."""
    old_unique_id = "123"
    new_unique_id = "1234"
    entry = MockConfigEntry(
        domain=DECONZ_DOMAIN,
        unique_id=new_unique_id,
        data={
            CONF_API_KEY: "1",
            CONF_HOST: "2",
            CONF_GROUP_ID_BASE: old_unique_id,
            CONF_PORT: "3",
        },
    )

    registry = er.async_get(opp)
    # Create entity entry to migrate to new unique ID
    registry.async_get_or_create(
        LIGHT_DOMAIN,
        DECONZ_DOMAIN,
        f"{old_unique_id}-OLD",
        suggested_object_id="old",
        config_entry=entry,
    )
    # Create entity entry with new unique ID
    registry.async_get_or_create(
        LIGHT_DOMAIN,
        DECONZ_DOMAIN,
        f"{new_unique_id}-NEW",
        suggested_object_id="new",
        config_entry=entry,
    )

    await async_update_group_unique_id(opp, entry)

    assert entry.data == {CONF_API_KEY: "1", CONF_HOST: "2", CONF_PORT: "3"}
    assert registry.async_get(f"{LIGHT_DOMAIN}.old").unique_id == f"{new_unique_id}-OLD"
    assert registry.async_get(f"{LIGHT_DOMAIN}.new").unique_id == f"{new_unique_id}-NEW"


async def test_update_group_unique_id_no_legacy_group_id(opp):
    """Test migration doesn't trigger without old legacy group id in entry data."""
    old_unique_id = "123"
    new_unique_id = "1234"
    entry = MockConfigEntry(
        domain=DECONZ_DOMAIN,
        unique_id=new_unique_id,
        data={},
    )

    registry = er.async_get(opp)
    # Create entity entry to migrate to new unique ID
    registry.async_get_or_create(
        LIGHT_DOMAIN,
        DECONZ_DOMAIN,
        f"{old_unique_id}-OLD",
        suggested_object_id="old",
        config_entry=entry,
    )

    await async_update_group_unique_id(opp, entry)

    assert registry.async_get(f"{LIGHT_DOMAIN}.old").unique_id == f"{old_unique_id}-OLD"
