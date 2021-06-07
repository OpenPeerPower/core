"""The tests for the Netatmo climate platform."""
from unittest.mock import Mock, patch

from openpeerpower.components.climate import (
    DOMAIN as CLIMATE_DOMAIN,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_PRESET_MODE,
    SERVICE_SET_TEMPERATURE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from openpeerpower.components.climate.const import (
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    HVAC_MODE_AUTO,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    PRESET_AWAY,
    PRESET_BOOST,
)
from openpeerpower.components.netatmo import climate
from openpeerpower.components.netatmo.climate import PRESET_FROST_GUARD, PRESET_SCHEDULE
from openpeerpower.components.netatmo.const import (
    ATTR_SCHEDULE_NAME,
    SERVICE_SET_SCHEDULE,
)
from openpeerpower.const import ATTR_ENTITY_ID, ATTR_TEMPERATURE, CONF_WEBHOOK_ID

from .common import selected_platforms, simulate_webhook


async def test_webhook_event_handling_thermostats(opp, config_entry, netatmo_auth):
    """Test service and webhook event handling with thermostats."""
    with selected_platforms(["climate"]):
        await opp.config_entries.async_setup(config_entry.entry_id)

        await opp.async_block_till_done()

    webhook_id = config_entry.data[CONF_WEBHOOK_ID]
    climate_entity_livingroom = "climate.netatmo_livingroom"

    assert opp.states.get(climate_entity_livingroom).state == "auto"
    assert (
        opp.states.get(climate_entity_livingroom).attributes["preset_mode"]
        == "Schedule"
    )
    assert opp.states.get(climate_entity_livingroom).attributes["temperature"] == 12

    # Test service setting the temperature
    await opp.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: climate_entity_livingroom, ATTR_TEMPERATURE: 21},
        blocking=True,
    )
    await opp.async_block_till_done()

    # Fake webhook thermostat manual set point
    response = {
        "room_id": "2746182631",
        "home": {
            "id": "91763b24c43d3e344f424e8b",
            "name": "MYHOME",
            "country": "DE",
            "rooms": [
                {
                    "id": "2746182631",
                    "name": "Livingroom",
                    "type": "livingroom",
                    "therm_setpoint_mode": "manual",
                    "therm_setpoint_temperature": 21,
                    "therm_setpoint_end_time": 1612734552,
                }
            ],
            "modules": [
                {"id": "12:34:56:00:01:ae", "name": "Livingroom", "type": "NATherm1"}
            ],
        },
        "mode": "manual",
        "event_type": "set_point",
        "temperature": 21,
        "push_type": "display_change",
    }
    await simulate_webhook(opp, webhook_id, response)

    assert opp.states.get(climate_entity_livingroom).state == "heat"
    assert (
        opp.states.get(climate_entity_livingroom).attributes["preset_mode"]
        == "Schedule"
    )
    assert opp.states.get(climate_entity_livingroom).attributes["temperature"] == 21

    # Test service setting the HVAC mode to "heat"
    await opp.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: climate_entity_livingroom, ATTR_HVAC_MODE: HVAC_MODE_HEAT},
        blocking=True,
    )
    await opp.async_block_till_done()

    # Fake webhook thermostat mode change to "Max"
    response = {
        "room_id": "2746182631",
        "home": {
            "id": "91763b24c43d3e344f424e8b",
            "name": "MYHOME",
            "country": "DE",
            "rooms": [
                {
                    "id": "2746182631",
                    "name": "Livingroom",
                    "type": "livingroom",
                    "therm_setpoint_mode": "max",
                    "therm_setpoint_end_time": 1612749189,
                }
            ],
            "modules": [
                {"id": "12:34:56:00:01:ae", "name": "Livingroom", "type": "NATherm1"}
            ],
        },
        "mode": "max",
        "event_type": "set_point",
        "push_type": "display_change",
    }
    await simulate_webhook(opp, webhook_id, response)

    assert opp.states.get(climate_entity_livingroom).state == "heat"
    assert opp.states.get(climate_entity_livingroom).attributes["temperature"] == 30

    # Test service setting the HVAC mode to "off"
    await opp.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: climate_entity_livingroom, ATTR_HVAC_MODE: HVAC_MODE_OFF},
        blocking=True,
    )
    await opp.async_block_till_done()

    # Fake webhook turn thermostat off
    response = {
        "home": {
            "id": "91763b24c43d3e344f424e8b",
            "name": "MYHOME",
            "country": "DE",
            "rooms": [
                {
                    "id": "2746182631",
                    "name": "Livingroom",
                    "type": "livingroom",
                    "therm_setpoint_mode": "off",
                }
            ],
            "modules": [
                {"id": "12:34:56:00:01:ae", "name": "Livingroom", "type": "NATherm1"}
            ],
        },
        "mode": "off",
        "event_type": "set_point",
        "push_type": "display_change",
    }
    await simulate_webhook(opp, webhook_id, response)

    assert opp.states.get(climate_entity_livingroom).state == "off"

    # Test service setting the HVAC mode to "auto"
    await opp.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: climate_entity_livingroom, ATTR_HVAC_MODE: HVAC_MODE_AUTO},
        blocking=True,
    )
    await opp.async_block_till_done()

    # Fake webhook thermostat mode cancel set point
    response = {
        "room_id": "2746182631",
        "home": {
            "id": "91763b24c43d3e344f424e8b",
            "name": "MYHOME",
            "country": "DE",
            "rooms": [
                {
                    "id": "2746182631",
                    "name": "Livingroom",
                    "type": "livingroom",
                    "therm_setpoint_mode": "home",
                }
            ],
            "modules": [
                {"id": "12:34:56:00:01:ae", "name": "Livingroom", "type": "NATherm1"}
            ],
        },
        "mode": "home",
        "event_type": "cancel_set_point",
        "push_type": "display_change",
    }
    await simulate_webhook(opp, webhook_id, response)

    assert opp.states.get(climate_entity_livingroom).state == "auto"
    assert (
        opp.states.get(climate_entity_livingroom).attributes["preset_mode"]
        == "Schedule"
    )


async def test_service_preset_mode_frost_guard_thermostat(
    opp, config_entry, netatmo_auth
):
    """Test service with frost guard preset for thermostats."""
    with selected_platforms(["climate"]):
        await opp.config_entries.async_setup(config_entry.entry_id)

        await opp.async_block_till_done()

    webhook_id = config_entry.data[CONF_WEBHOOK_ID]
    climate_entity_livingroom = "climate.netatmo_livingroom"

    assert opp.states.get(climate_entity_livingroom).state == "auto"
    assert (
        opp.states.get(climate_entity_livingroom).attributes["preset_mode"]
        == "Schedule"
    )

    # Test service setting the preset mode to "frost guard"
    await opp.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {
            ATTR_ENTITY_ID: climate_entity_livingroom,
            ATTR_PRESET_MODE: PRESET_FROST_GUARD,
        },
        blocking=True,
    )
    await opp.async_block_till_done()

    # Fake webhook thermostat mode change to "Frost Guard"
    response = {
        "event_type": "therm_mode",
        "home": {"id": "91763b24c43d3e344f424e8b", "therm_mode": "hg"},
        "mode": "hg",
        "previous_mode": "schedule",
        "push_type": "home_event_changed",
    }
    await simulate_webhook(opp, webhook_id, response)

    assert opp.states.get(climate_entity_livingroom).state == "auto"
    assert (
        opp.states.get(climate_entity_livingroom).attributes["preset_mode"]
        == "Frost Guard"
    )

    # Test service setting the preset mode to "frost guard"
    await opp.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {
            ATTR_ENTITY_ID: climate_entity_livingroom,
            ATTR_PRESET_MODE: PRESET_SCHEDULE,
        },
        blocking=True,
    )
    await opp.async_block_till_done()

    # Test webhook thermostat mode change to "Schedule"
    response = {
        "event_type": "therm_mode",
        "home": {"id": "91763b24c43d3e344f424e8b", "therm_mode": "schedule"},
        "mode": "schedule",
        "previous_mode": "hg",
        "push_type": "home_event_changed",
    }
    await simulate_webhook(opp, webhook_id, response)

    assert opp.states.get(climate_entity_livingroom).state == "auto"
    assert (
        opp.states.get(climate_entity_livingroom).attributes["preset_mode"]
        == "Schedule"
    )


async def test_service_preset_modes_thermostat(opp, config_entry, netatmo_auth):
    """Test service with preset modes for thermostats."""
    with selected_platforms(["climate"]):
        await opp.config_entries.async_setup(config_entry.entry_id)

        await opp.async_block_till_done()

    webhook_id = config_entry.data[CONF_WEBHOOK_ID]
    climate_entity_livingroom = "climate.netatmo_livingroom"

    assert opp.states.get(climate_entity_livingroom).state == "auto"
    assert (
        opp.states.get(climate_entity_livingroom).attributes["preset_mode"]
        == "Schedule"
    )

    # Test service setting the preset mode to "away"
    await opp.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: climate_entity_livingroom, ATTR_PRESET_MODE: PRESET_AWAY},
        blocking=True,
    )
    await opp.async_block_till_done()

    # Fake webhook thermostat mode change to "Away"
    response = {
        "event_type": "therm_mode",
        "home": {"id": "91763b24c43d3e344f424e8b", "therm_mode": "away"},
        "mode": "away",
        "previous_mode": "schedule",
        "push_type": "home_event_changed",
    }
    await simulate_webhook(opp, webhook_id, response)

    assert opp.states.get(climate_entity_livingroom).state == "auto"
    assert opp.states.get(climate_entity_livingroom).attributes["preset_mode"] == "away"

    # Test service setting the preset mode to "boost"
    await opp.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: climate_entity_livingroom, ATTR_PRESET_MODE: PRESET_BOOST},
        blocking=True,
    )
    await opp.async_block_till_done()

    # Test webhook thermostat mode change to "Max"
    response = {
        "room_id": "2746182631",
        "home": {
            "id": "91763b24c43d3e344f424e8b",
            "name": "MYHOME",
            "country": "DE",
            "rooms": [
                {
                    "id": "2746182631",
                    "name": "Livingroom",
                    "type": "livingroom",
                    "therm_setpoint_mode": "max",
                    "therm_setpoint_end_time": 1612749189,
                }
            ],
            "modules": [
                {"id": "12:34:56:00:01:ae", "name": "Livingroom", "type": "NATherm1"}
            ],
        },
        "mode": "max",
        "event_type": "set_point",
        "push_type": "display_change",
    }
    await simulate_webhook(opp, webhook_id, response)

    assert opp.states.get(climate_entity_livingroom).state == "heat"
    assert opp.states.get(climate_entity_livingroom).attributes["temperature"] == 30


async def test_webhook_event_handling_no_data(opp, config_entry, netatmo_auth):
    """Test service and webhook event handling with erroneous data."""
    with selected_platforms(["climate"]):
        await opp.config_entries.async_setup(config_entry.entry_id)

        await opp.async_block_till_done()

    # Test webhook without home entry
    webhook_id = config_entry.data[CONF_WEBHOOK_ID]

    response = {
        "push_type": "home_event_changed",
    }
    await simulate_webhook(opp, webhook_id, response)

    # Test webhook with different home id
    response = {
        "home_id": "3d3e344f491763b24c424e8b",
        "room_id": "2746182631",
        "home": {
            "id": "3d3e344f491763b24c424e8b",
            "name": "MYHOME",
            "country": "DE",
            "rooms": [],
            "modules": [],
        },
        "mode": "home",
        "event_type": "cancel_set_point",
        "push_type": "display_change",
    }
    await simulate_webhook(opp, webhook_id, response)

    # Test webhook without room entries
    response = {
        "room_id": "2746182631",
        "home": {
            "id": "91763b24c43d3e344f424e8b",
            "name": "MYHOME",
            "country": "DE",
            "rooms": [],
            "modules": [],
        },
        "mode": "home",
        "event_type": "cancel_set_point",
        "push_type": "display_change",
    }
    await simulate_webhook(opp, webhook_id, response)


async def test_service_schedule_thermostats(opp, config_entry, caplog, netatmo_auth):
    """Test service for selecting Netatmo schedule with thermostats."""
    with selected_platforms(["climate"]):
        await opp.config_entries.async_setup(config_entry.entry_id)

        await opp.async_block_till_done()

    webhook_id = config_entry.data[CONF_WEBHOOK_ID]
    climate_entity_livingroom = "climate.netatmo_livingroom"

    # Test setting a valid schedule
    with patch(
        "pyatmo.thermostat.AsyncHomeData.async_switch_home_schedule"
    ) as mock_switch_home_schedule:
        await opp.services.async_call(
            "netatmo",
            SERVICE_SET_SCHEDULE,
            {ATTR_ENTITY_ID: climate_entity_livingroom, ATTR_SCHEDULE_NAME: "Winter"},
            blocking=True,
        )
        await opp.async_block_till_done()
        mock_switch_home_schedule.assert_called_once_with(
            home_id="91763b24c43d3e344f424e8b", schedule_id="b1b54a2f45795764f59d50d8"
        )

    # Fake backend response for valve being turned on
    response = {
        "event_type": "schedule",
        "schedule_id": "b1b54a2f45795764f59d50d8",
        "previous_schedule_id": "59d32176d183948b05ab4dce",
        "push_type": "home_event_changed",
    }
    await simulate_webhook(opp, webhook_id, response)

    assert (
        opp.states.get(climate_entity_livingroom).attributes["selected_schedule"]
        == "Winter"
    )

    # Test setting an invalid schedule
    with patch(
        "pyatmo.thermostat.AsyncHomeData.async_switch_home_schedule"
    ) as mock_switch_home_schedule:
        await opp.services.async_call(
            "netatmo",
            SERVICE_SET_SCHEDULE,
            {ATTR_ENTITY_ID: climate_entity_livingroom, ATTR_SCHEDULE_NAME: "summer"},
            blocking=True,
        )
        await opp.async_block_till_done()
        mock_switch_home_schedule.assert_not_called()

    assert "summer is not a valid schedule" in caplog.text


async def test_service_preset_mode_already_boost_valves(
    opp, config_entry, netatmo_auth
):
    """Test service with boost preset for valves when already in boost mode."""
    with selected_platforms(["climate"]):
        await opp.config_entries.async_setup(config_entry.entry_id)

        await opp.async_block_till_done()

    webhook_id = config_entry.data[CONF_WEBHOOK_ID]
    climate_entity_entrada = "climate.netatmo_entrada"

    assert opp.states.get(climate_entity_entrada).state == "auto"
    assert (
        opp.states.get(climate_entity_entrada).attributes["preset_mode"]
        == "Frost Guard"
    )
    assert opp.states.get(climate_entity_entrada).attributes["temperature"] == 7

    # Test webhook valve mode change to "Max"
    response = {
        "room_id": "2833524037",
        "home": {
            "id": "91763b24c43d3e344f424e8b",
            "name": "MYHOME",
            "country": "DE",
            "rooms": [
                {
                    "id": "2833524037",
                    "name": "Entrada",
                    "type": "lobby",
                    "therm_setpoint_mode": "max",
                    "therm_setpoint_end_time": 1612749189,
                }
            ],
            "modules": [{"id": "12:34:56:00:01:ae", "name": "Entrada", "type": "NRV"}],
        },
        "mode": "max",
        "event_type": "set_point",
        "push_type": "display_change",
    }
    await simulate_webhook(opp, webhook_id, response)

    # Test service setting the preset mode to "boost"
    await opp.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: climate_entity_entrada, ATTR_PRESET_MODE: PRESET_BOOST},
        blocking=True,
    )
    await opp.async_block_till_done()

    # Test webhook valve mode change to "Max"
    response = {
        "room_id": "2833524037",
        "home": {
            "id": "91763b24c43d3e344f424e8b",
            "name": "MYHOME",
            "country": "DE",
            "rooms": [
                {
                    "id": "2833524037",
                    "name": "Entrada",
                    "type": "lobby",
                    "therm_setpoint_mode": "max",
                    "therm_setpoint_end_time": 1612749189,
                }
            ],
            "modules": [{"id": "12:34:56:00:01:ae", "name": "Entrada", "type": "NRV"}],
        },
        "mode": "max",
        "event_type": "set_point",
        "push_type": "display_change",
    }
    await simulate_webhook(opp, webhook_id, response)

    assert opp.states.get(climate_entity_entrada).state == "heat"
    assert opp.states.get(climate_entity_entrada).attributes["temperature"] == 30


async def test_service_preset_mode_boost_valves(opp, config_entry, netatmo_auth):
    """Test service with boost preset for valves."""
    with selected_platforms(["climate"]):
        await opp.config_entries.async_setup(config_entry.entry_id)

        await opp.async_block_till_done()

    webhook_id = config_entry.data[CONF_WEBHOOK_ID]
    climate_entity_entrada = "climate.netatmo_entrada"

    # Test service setting the preset mode to "boost"
    assert opp.states.get(climate_entity_entrada).state == "auto"
    assert opp.states.get(climate_entity_entrada).attributes["temperature"] == 7

    await opp.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: climate_entity_entrada, ATTR_PRESET_MODE: PRESET_BOOST},
        blocking=True,
    )
    await opp.async_block_till_done()

    # Fake backend response
    response = {
        "room_id": "2833524037",
        "home": {
            "id": "91763b24c43d3e344f424e8b",
            "name": "MYHOME",
            "country": "DE",
            "rooms": [
                {
                    "id": "2833524037",
                    "name": "Entrada",
                    "type": "lobby",
                    "therm_setpoint_mode": "max",
                    "therm_setpoint_end_time": 1612749189,
                }
            ],
            "modules": [{"id": "12:34:56:00:01:ae", "name": "Entrada", "type": "NRV"}],
        },
        "mode": "max",
        "event_type": "set_point",
        "push_type": "display_change",
    }
    await simulate_webhook(opp, webhook_id, response)

    assert opp.states.get(climate_entity_entrada).state == "heat"
    assert opp.states.get(climate_entity_entrada).attributes["temperature"] == 30


async def test_service_preset_mode_invalid(opp, config_entry, caplog, netatmo_auth):
    """Test service with invalid preset."""
    with selected_platforms(["climate"]):
        await opp.config_entries.async_setup(config_entry.entry_id)

        await opp.async_block_till_done()

    await opp.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: "climate.netatmo_cocina", ATTR_PRESET_MODE: "invalid"},
        blocking=True,
    )
    await opp.async_block_till_done()

    assert "Preset mode 'invalid' not available" in caplog.text


async def test_valves_service_turn_off(opp, config_entry, netatmo_auth):
    """Test service turn off for valves."""
    with selected_platforms(["climate"]):
        await opp.config_entries.async_setup(config_entry.entry_id)

        await opp.async_block_till_done()

    webhook_id = config_entry.data[CONF_WEBHOOK_ID]
    climate_entity_entrada = "climate.netatmo_entrada"

    # Test turning valve off
    await opp.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: climate_entity_entrada},
        blocking=True,
    )
    await opp.async_block_till_done()

    # Fake backend response for valve being turned off
    response = {
        "room_id": "2833524037",
        "home": {
            "id": "91763b24c43d3e344f424e8b",
            "name": "MYHOME",
            "country": "DE",
            "rooms": [
                {
                    "id": "2833524037",
                    "name": "Entrada",
                    "type": "lobby",
                    "therm_setpoint_mode": "off",
                }
            ],
            "modules": [{"id": "12:34:56:00:01:ae", "name": "Entrada", "type": "NRV"}],
        },
        "mode": "off",
        "event_type": "set_point",
        "push_type": "display_change",
    }
    await simulate_webhook(opp, webhook_id, response)

    assert opp.states.get(climate_entity_entrada).state == "off"


async def test_valves_service_turn_on(opp, config_entry, netatmo_auth):
    """Test service turn on for valves."""
    with selected_platforms(["climate"]):
        await opp.config_entries.async_setup(config_entry.entry_id)

        await opp.async_block_till_done()

    webhook_id = config_entry.data[CONF_WEBHOOK_ID]
    climate_entity_entrada = "climate.netatmo_entrada"

    # Test turning valve on
    await opp.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: climate_entity_entrada},
        blocking=True,
    )
    await opp.async_block_till_done()

    # Fake backend response for valve being turned on
    response = {
        "room_id": "2833524037",
        "home": {
            "id": "91763b24c43d3e344f424e8b",
            "name": "MYHOME",
            "country": "DE",
            "rooms": [
                {
                    "id": "2833524037",
                    "name": "Entrada",
                    "type": "lobby",
                    "therm_setpoint_mode": "home",
                }
            ],
            "modules": [{"id": "12:34:56:00:01:ae", "name": "Entrada", "type": "NRV"}],
        },
        "mode": "home",
        "event_type": "cancel_set_point",
        "push_type": "display_change",
    }
    await simulate_webhook(opp, webhook_id, response)

    assert opp.states.get(climate_entity_entrada).state == "auto"


async def test_get_all_home_ids():
    """Test extracting all home ids returned by NetAtmo API."""
    # Test with backend returning no data
    assert climate.get_all_home_ids(None) == []

    # Test with fake data
    home_data = Mock()
    home_data.homes = {
        "123": {"id": "123", "name": "Home 1", "modules": [], "therm_schedules": []},
        "987": {"id": "987", "name": "Home 2", "modules": [], "therm_schedules": []},
    }
    expected = ["123", "987"]
    assert climate.get_all_home_ids(home_data) == expected


async def test_webhook_home_id_mismatch(opp, config_entry, netatmo_auth):
    """Test service turn on for valves."""
    with selected_platforms(["climate"]):
        await opp.config_entries.async_setup(config_entry.entry_id)

        await opp.async_block_till_done()

    webhook_id = config_entry.data[CONF_WEBHOOK_ID]
    climate_entity_entrada = "climate.netatmo_entrada"

    assert opp.states.get(climate_entity_entrada).state == "auto"

    # Fake backend response for valve being turned on
    response = {
        "room_id": "2833524037",
        "home": {
            "id": "123",
            "name": "MYHOME",
            "country": "DE",
            "rooms": [
                {
                    "id": "2833524037",
                    "name": "Entrada",
                    "type": "lobby",
                    "therm_setpoint_mode": "home",
                }
            ],
            "modules": [{"id": "12:34:56:00:01:ae", "name": "Entrada", "type": "NRV"}],
        },
        "mode": "home",
        "event_type": "cancel_set_point",
        "push_type": "display_change",
    }
    await simulate_webhook(opp, webhook_id, response)

    assert opp.states.get(climate_entity_entrada).state == "auto"


async def test_webhook_set_point(opp, config_entry, netatmo_auth):
    """Test service turn on for valves."""
    with selected_platforms(["climate"]):
        await opp.config_entries.async_setup(config_entry.entry_id)

        await opp.async_block_till_done()

    webhook_id = config_entry.data[CONF_WEBHOOK_ID]
    climate_entity_entrada = "climate.netatmo_entrada"

    # Fake backend response for valve being turned on
    response = {
        "room_id": "2746182631",
        "home": {
            "id": "91763b24c43d3e344f424e8b",
            "name": "MYHOME",
            "country": "DE",
            "rooms": [
                {
                    "id": "2833524037",
                    "name": "Entrada",
                    "type": "lobby",
                    "therm_setpoint_mode": "home",
                    "therm_setpoint_temperature": 30,
                }
            ],
            "modules": [{"id": "12:34:56:00:01:ae", "name": "Entrada", "type": "NRV"}],
        },
        "mode": "home",
        "event_type": "set_point",
        "temperature": 21,
        "push_type": "display_change",
    }
    await simulate_webhook(opp, webhook_id, response)

    assert opp.states.get(climate_entity_entrada).state == "heat"
