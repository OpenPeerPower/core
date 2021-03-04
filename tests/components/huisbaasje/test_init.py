"""Test cases for the initialisation of the Huisbaasje integration."""
from unittest.mock import patch

from huisbaasje import HuisbaasjeException

from openpeerpower.components import huisbaasje
from openpeerpower.config_entries import (
    CONN_CLASS_CLOUD_POLL,
    ENTRY_STATE_LOADED,
    ENTRY_STATE_NOT_LOADED,
    ENTRY_STATE_SETUP_ERROR,
    ConfigEntry,
)
from openpeerpower.const import CONF_ID, CONF_PASSWORD, CONF_USERNAME, STATE_UNAVAILABLE
from openpeerpower.core import OpenPeerPower
from openpeerpower.setup import async_setup_component

from tests.components.huisbaasje.test_data import MOCK_CURRENT_MEASUREMENTS


async def test_setup(opp: OpenPeerPower):
    """Test for successfully setting up the platform."""
    assert await async_setup_component(opp, huisbaasje.DOMAIN, {})
    await opp.async_block_till_done()
    assert huisbaasje.DOMAIN in opp.config.components


async def test_setup_entry(opp: OpenPeerPower):
    """Test for successfully setting a config entry."""
    with patch(
        "huisbaasje.Huisbaasje.authenticate", return_value=None
    ) as mock_authenticate, patch(
        "huisbaasje.Huisbaasje.is_authenticated", return_value=True
    ) as mock_is_authenticated, patch(
        "huisbaasje.Huisbaasje.current_measurements",
        return_value=MOCK_CURRENT_MEASUREMENTS,
    ) as mock_current_measurements:
        opp.config.components.add(huisbaasje.DOMAIN)
        config_entry = ConfigEntry(
            1,
            huisbaasje.DOMAIN,
            "userId",
            {
                CONF_ID: "userId",
                CONF_USERNAME: "username",
                CONF_PASSWORD: "password",
            },
            "test",
            CONN_CLASS_CLOUD_POLL,
            system_options={},
        )
        opp.config_entries._entries.append(config_entry)

        assert config_entry.state == ENTRY_STATE_NOT_LOADED
        assert await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()

        # Assert integration is loaded
        assert config_entry.state == ENTRY_STATE_LOADED
        assert huisbaasje.DOMAIN in opp.config.components
        assert huisbaasje.DOMAIN in opp.data
        assert config_entry.entry_id in opp.data[huisbaasje.DOMAIN]

        # Assert entities are loaded
        entities = opp.states.async_entity_ids("sensor")
        assert len(entities) == 14

        # Assert mocks are called
        assert len(mock_authenticate.mock_calls) == 1
        assert len(mock_is_authenticated.mock_calls) == 1
        assert len(mock_current_measurements.mock_calls) == 1


async def test_setup_entry_error(opp: OpenPeerPower):
    """Test for successfully setting a config entry."""
    with patch(
        "huisbaasje.Huisbaasje.authenticate", side_effect=HuisbaasjeException
    ) as mock_authenticate:
        opp.config.components.add(huisbaasje.DOMAIN)
        config_entry = ConfigEntry(
            1,
            huisbaasje.DOMAIN,
            "userId",
            {
                CONF_ID: "userId",
                CONF_USERNAME: "username",
                CONF_PASSWORD: "password",
            },
            "test",
            CONN_CLASS_CLOUD_POLL,
            system_options={},
        )
        opp.config_entries._entries.append(config_entry)

        assert config_entry.state == ENTRY_STATE_NOT_LOADED
        await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()

        # Assert integration is loaded with error
        assert config_entry.state == ENTRY_STATE_SETUP_ERROR
        assert huisbaasje.DOMAIN not in opp.data

        # Assert entities are not loaded
        entities = opp.states.async_entity_ids("sensor")
        assert len(entities) == 0

        # Assert mocks are called
        assert len(mock_authenticate.mock_calls) == 1


async def test_unload_entry(opp: OpenPeerPower):
    """Test for successfully unloading the config entry."""
    with patch(
        "huisbaasje.Huisbaasje.authenticate", return_value=None
    ) as mock_authenticate, patch(
        "huisbaasje.Huisbaasje.is_authenticated", return_value=True
    ) as mock_is_authenticated, patch(
        "huisbaasje.Huisbaasje.current_measurements",
        return_value=MOCK_CURRENT_MEASUREMENTS,
    ) as mock_current_measurements:
        opp.config.components.add(huisbaasje.DOMAIN)
        config_entry = ConfigEntry(
            1,
            huisbaasje.DOMAIN,
            "userId",
            {
                CONF_ID: "userId",
                CONF_USERNAME: "username",
                CONF_PASSWORD: "password",
            },
            "test",
            CONN_CLASS_CLOUD_POLL,
            system_options={},
        )
        opp.config_entries._entries.append(config_entry)

        # Load config entry
        assert await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()
        assert config_entry.state == ENTRY_STATE_LOADED
        entities = opp.states.async_entity_ids("sensor")
        assert len(entities) == 14

        # Unload config entry
        await opp.config_entries.async_unload(config_entry.entry_id)
        assert config_entry.state == ENTRY_STATE_NOT_LOADED
        entities = opp.states.async_entity_ids("sensor")
        assert len(entities) == 14
        for entity in entities:
            assert opp.states.get(entity).state == STATE_UNAVAILABLE

        # Remove config entry
        await opp.config_entries.async_remove(config_entry.entry_id)
        await opp.async_block_till_done()
        entities = opp.states.async_entity_ids("sensor")
        assert len(entities) == 0

        # Assert mocks are called
        assert len(mock_authenticate.mock_calls) == 1
        assert len(mock_is_authenticated.mock_calls) == 1
        assert len(mock_current_measurements.mock_calls) == 1
