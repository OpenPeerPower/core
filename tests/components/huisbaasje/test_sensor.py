"""Test cases for the sensors of the Huisbaasje integration."""
from unittest.mock import patch

from openpeerpower.components import huisbaasje
from openpeerpower.config_entries import CONN_CLASS_CLOUD_POLL, ConfigEntry
from openpeerpower.const import CONF_ID, CONF_PASSWORD, CONF_USERNAME
from openpeerpowerr.core import OpenPeerPower

from tests.components.huisbaasje.test_data import (
    MOCK_CURRENT_MEASUREMENTS,
    MOCK_LIMITED_CURRENT_MEASUREMENTS,
)


async def test_setup_entry.opp: OpenPeerPower):
    """Test for successfully loading sensor states."""
    with patch(
        "huisbaasje.Huisbaasje.authenticate", return_value=None
    ) as mock_authenticate, patch(
        "huisbaasje.Huisbaasje.is_authenticated", return_value=True
    ) as mock_is_authenticated, patch(
        "huisbaasje.Huisbaasje.current_measurements",
        return_value=MOCK_CURRENT_MEASUREMENTS,
    ) as mock_current_measurements:

       .opp.config.components.add(huisbaasje.DOMAIN)
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
       .opp.config_entries._entries.append(config_entry)

        assert await.opp.config_entries.async_setup(config_entry.entry_id)
        await.opp.async_block_till_done()

        # Assert data is loaded
        assert.opp.states.get("sensor.huisbaasje_current_power").state == "1012.0"
        assert.opp.states.get("sensor.huisbaasje_current_power_in").state == "1012.0"
        assert (
           .opp.states.get("sensor.huisbaasje_current_power_in_low").state == "unknown"
        )
        assert.opp.states.get("sensor.huisbaasje_current_power_out").state == "unknown"
        assert (
           .opp.states.get("sensor.huisbaasje_current_power_out_low").state
            == "unknown"
        )
        assert.opp.states.get("sensor.huisbaasje_current_gas").state == "0.0"
        assert.opp.states.get("sensor.huisbaasje_energy_today").state == "3.3"
        assert.opp.states.get("sensor.huisbaasje_energy_this_week").state == "17.5"
        assert.opp.states.get("sensor.huisbaasje_energy_this_month").state == "103.3"
        assert.opp.states.get("sensor.huisbaasje_energy_this_year").state == "673.0"
        assert.opp.states.get("sensor.huisbaasje_gas_today").state == "1.1"
        assert.opp.states.get("sensor.huisbaasje_gas_this_week").state == "5.6"
        assert.opp.states.get("sensor.huisbaasje_gas_this_month").state == "39.1"
        assert.opp.states.get("sensor.huisbaasje_gas_this_year").state == "116.7"

        # Assert mocks are called
        assert len(mock_authenticate.mock_calls) == 1
        assert len(mock_is_authenticated.mock_calls) == 1
        assert len(mock_current_measurements.mock_calls) == 1


async def test_setup_entry_absent_measurement.opp: OpenPeerPower):
    """Test for successfully loading sensor states when response does not contain all measurements."""
    with patch(
        "huisbaasje.Huisbaasje.authenticate", return_value=None
    ) as mock_authenticate, patch(
        "huisbaasje.Huisbaasje.is_authenticated", return_value=True
    ) as mock_is_authenticated, patch(
        "huisbaasje.Huisbaasje.current_measurements",
        return_value=MOCK_LIMITED_CURRENT_MEASUREMENTS,
    ) as mock_current_measurements:

       .opp.config.components.add(huisbaasje.DOMAIN)
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
       .opp.config_entries._entries.append(config_entry)

        assert await.opp.config_entries.async_setup(config_entry.entry_id)
        await.opp.async_block_till_done()

        # Assert data is loaded
        assert.opp.states.get("sensor.huisbaasje_current_power").state == "1012.0"
        assert.opp.states.get("sensor.huisbaasje_current_power_in").state == "unknown"
        assert (
           .opp.states.get("sensor.huisbaasje_current_power_in_low").state == "unknown"
        )
        assert.opp.states.get("sensor.huisbaasje_current_power_out").state == "unknown"
        assert (
           .opp.states.get("sensor.huisbaasje_current_power_out_low").state
            == "unknown"
        )
        assert.opp.states.get("sensor.huisbaasje_current_gas").state == "unknown"
        assert.opp.states.get("sensor.huisbaasje_energy_today").state == "3.3"
        assert.opp.states.get("sensor.huisbaasje_gas_today").state == "unknown"

        # Assert mocks are called
        assert len(mock_authenticate.mock_calls) == 1
        assert len(mock_is_authenticated.mock_calls) == 1
        assert len(mock_current_measurements.mock_calls) == 1
