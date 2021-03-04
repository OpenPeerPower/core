"""deCONZ climate platform tests."""

from copy import deepcopy

import pytest

from openpeerpower.components.climate import (
    DOMAIN as CLIMATE_DOMAIN,
    SERVICE_SET_FAN_MODE,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_PRESET_MODE,
    SERVICE_SET_TEMPERATURE,
)
from openpeerpower.components.climate.const import (
    ATTR_FAN_MODE,
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_OFF,
    FAN_ON,
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    PRESET_COMFORT,
)
from openpeerpower.components.deconz.climate import (
    DECONZ_FAN_SMART,
    DECONZ_PRESET_MANUAL,
)
from openpeerpower.components.deconz.const import CONF_ALLOW_CLIP_SENSOR
from openpeerpower.components.deconz.gateway import get_gateway_from_config_entry
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
    STATE_OFF,
    STATE_UNAVAILABLE,
)

from .test_gateway import (
    DECONZ_WEB_REQUEST,
    mock_deconz_put_request,
    setup_deconz_integration,
)

SENSORS = {
    "1": {
        "id": "Thermostat id",
        "name": "Thermostat",
        "type": "ZHAThermostat",
        "state": {"on": True, "temperature": 2260, "valve": 30},
        "config": {
            "battery": 100,
            "heatsetpoint": 2200,
            "mode": "auto",
            "offset": 10,
            "reachable": True,
        },
        "uniqueid": "00:00:00:00:00:00:00:00-00",
    },
    "2": {
        "id": "CLIP thermostat id",
        "name": "CLIP thermostat",
        "type": "CLIPThermostat",
        "state": {"on": True, "temperature": 2260, "valve": 30},
        "config": {"reachable": True},
        "uniqueid": "00:00:00:00:00:00:00:02-00",
    },
}


async def test_no_sensors(opp, aioclient_mock):
    """Test that no sensors in deconz results in no climate entities."""
    await setup_deconz_integration(opp, aioclient_mock)
    assert len(opp.states.async_all()) == 0


async def test_simple_climate_device(opp, aioclient_mock):
    """Test successful creation of climate entities.

    This is a simple water heater that only supports setting temperature and on and off.
    """
    data = deepcopy(DECONZ_WEB_REQUEST)
    data["sensors"] = {
        "0": {
            "config": {
                "battery": 59,
                "displayflipped": None,
                "heatsetpoint": 2100,
                "locked": True,
                "mountingmode": None,
                "offset": 0,
                "on": True,
                "reachable": True,
            },
            "ep": 1,
            "etag": "6130553ac247174809bae47144ee23f8",
            "lastseen": "2020-11-29T19:31Z",
            "manufacturername": "Danfoss",
            "modelid": "eTRV0100",
            "name": "thermostat",
            "state": {
                "errorcode": None,
                "lastupdated": "2020-11-29T19:28:40.665",
                "mountingmodeactive": False,
                "on": True,
                "temperature": 2102,
                "valve": 24,
                "windowopen": "Closed",
            },
            "swversion": "01.02.0008 01.02",
            "type": "ZHAThermostat",
            "uniqueid": "14:b4:57:ff:fe:d5:4e:77-01-0201",
        }
    }
    config_entry = await setup_deconz_integration(
        opp, aioclient_mock, get_state_response=data
    )
    gateway = get_gateway_from_config_entry(opp, config_entry)

    assert len(opp.states.async_all()) == 2
    climate_thermostat = opp.states.get("climate.thermostat")
    assert climate_thermostat.state == HVAC_MODE_HEAT
    assert climate_thermostat.attributes["hvac_modes"] == [
        HVAC_MODE_HEAT,
        HVAC_MODE_OFF,
    ]
    assert climate_thermostat.attributes["current_temperature"] == 21.0
    assert climate_thermostat.attributes["temperature"] == 21.0
    assert climate_thermostat.attributes["locked"] is True
    assert opp.states.get("sensor.thermostat_battery_level").state == "59"

    # Event signals thermostat configured off

    state_changed_event = {
        "t": "event",
        "e": "changed",
        "r": "sensors",
        "id": "0",
        "state": {"on": False},
    }
    gateway.api.event_handler(state_changed_event)
    await opp.async_block_till_done()

    assert opp.states.get("climate.thermostat").state == STATE_OFF

    # Event signals thermostat state on

    state_changed_event = {
        "t": "event",
        "e": "changed",
        "r": "sensors",
        "id": "0",
        "state": {"on": True},
    }
    gateway.api.event_handler(state_changed_event)
    await opp.async_block_till_done()

    assert opp.states.get("climate.thermostat").state == HVAC_MODE_HEAT

    # Verify service calls

    mock_deconz_put_request(aioclient_mock, config_entry.data, "/sensors/0/config")

    # Service turn on thermostat

    await opp.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: "climate.thermostat", ATTR_HVAC_MODE: HVAC_MODE_HEAT},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[1][2] == {"on": True}

    # Service turn on thermostat

    await opp.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: "climate.thermostat", ATTR_HVAC_MODE: HVAC_MODE_OFF},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[2][2] == {"on": False}

    # Service set HVAC mode to unsupported value

    with pytest.raises(ValueError):
        await opp.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.thermostat", ATTR_HVAC_MODE: HVAC_MODE_AUTO},
            blocking=True,
        )


async def test_climate_device_without_cooling_support(opp, aioclient_mock):
    """Test successful creation of sensor entities."""
    data = deepcopy(DECONZ_WEB_REQUEST)
    data["sensors"] = deepcopy(SENSORS)
    config_entry = await setup_deconz_integration(
        opp, aioclient_mock, get_state_response=data
    )
    gateway = get_gateway_from_config_entry(opp, config_entry)

    assert len(opp.states.async_all()) == 2
    climate_thermostat = opp.states.get("climate.thermostat")
    assert climate_thermostat.state == HVAC_MODE_AUTO
    assert climate_thermostat.attributes["hvac_modes"] == [
        HVAC_MODE_AUTO,
        HVAC_MODE_HEAT,
        HVAC_MODE_OFF,
    ]
    assert climate_thermostat.attributes["current_temperature"] == 22.6
    assert climate_thermostat.attributes["temperature"] == 22.0
    assert opp.states.get("sensor.thermostat") is None
    assert opp.states.get("sensor.thermostat_battery_level").state == "100"
    assert opp.states.get("climate.presence_sensor") is None
    assert opp.states.get("climate.clip_thermostat") is None

    # Event signals thermostat configured off

    state_changed_event = {
        "t": "event",
        "e": "changed",
        "r": "sensors",
        "id": "1",
        "config": {"mode": "off"},
    }
    gateway.api.event_handler(state_changed_event)
    await opp.async_block_till_done()

    assert opp.states.get("climate.thermostat").state == STATE_OFF

    # Event signals thermostat state on

    state_changed_event = {
        "t": "event",
        "e": "changed",
        "r": "sensors",
        "id": "1",
        "config": {"mode": "other"},
        "state": {"on": True},
    }
    gateway.api.event_handler(state_changed_event)
    await opp.async_block_till_done()

    assert opp.states.get("climate.thermostat").state == HVAC_MODE_HEAT

    # Event signals thermostat state off

    state_changed_event = {
        "t": "event",
        "e": "changed",
        "r": "sensors",
        "id": "1",
        "state": {"on": False},
    }
    gateway.api.event_handler(state_changed_event)
    await opp.async_block_till_done()

    assert opp.states.get("climate.thermostat").state == STATE_OFF

    # Verify service calls

    mock_deconz_put_request(aioclient_mock, config_entry.data, "/sensors/1/config")

    # Service set HVAC mode to auto

    await opp.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: "climate.thermostat", ATTR_HVAC_MODE: HVAC_MODE_AUTO},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[1][2] == {"mode": "auto"}

    # Service set HVAC mode to heat

    await opp.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: "climate.thermostat", ATTR_HVAC_MODE: HVAC_MODE_HEAT},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[2][2] == {"mode": "heat"}

    # Service set HVAC mode to off

    await opp.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: "climate.thermostat", ATTR_HVAC_MODE: HVAC_MODE_OFF},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[3][2] == {"mode": "off"}

    # Service set HVAC mode to unsupported value

    with pytest.raises(ValueError):
        await opp.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: "climate.thermostat", ATTR_HVAC_MODE: HVAC_MODE_COOL},
            blocking=True,
        )

    # Service set temperature to 20

    await opp.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: "climate.thermostat", ATTR_TEMPERATURE: 20},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[4][2] == {"heatsetpoint": 2000.0}

    # Service set temperature without providing temperature attribute

    with pytest.raises(ValueError):
        await opp.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {
                ATTR_ENTITY_ID: "climate.thermostat",
                ATTR_TARGET_TEMP_HIGH: 30,
                ATTR_TARGET_TEMP_LOW: 10,
            },
            blocking=True,
        )

    await opp.config_entries.async_unload(config_entry.entry_id)

    states = opp.states.async_all()
    assert len(opp.states.async_all()) == 2
    for state in states:
        assert state.state == STATE_UNAVAILABLE

    await opp.config_entries.async_remove(config_entry.entry_id)
    await opp.async_block_till_done()
    assert len(opp.states.async_all()) == 0


async def test_climate_device_with_cooling_support(opp, aioclient_mock):
    """Test successful creation of sensor entities."""
    data = deepcopy(DECONZ_WEB_REQUEST)
    data["sensors"] = {
        "0": {
            "config": {
                "battery": 25,
                "coolsetpoint": None,
                "fanmode": None,
                "heatsetpoint": 2222,
                "mode": "heat",
                "offset": 0,
                "on": True,
                "reachable": True,
            },
            "ep": 1,
            "etag": "074549903686a77a12ef0f06c499b1ef",
            "lastseen": "2020-11-27T13:45Z",
            "manufacturername": "Zen Within",
            "modelid": "Zen-01",
            "name": "Zen-01",
            "state": {
                "lastupdated": "2020-11-27T13:42:40.863",
                "on": False,
                "temperature": 2320,
            },
            "type": "ZHAThermostat",
            "uniqueid": "00:24:46:00:00:11:6f:56-01-0201",
        }
    }
    config_entry = await setup_deconz_integration(
        opp, aioclient_mock, get_state_response=data
    )
    gateway = get_gateway_from_config_entry(opp, config_entry)

    assert len(opp.states.async_all()) == 2
    climate_thermostat = opp.states.get("climate.zen_01")
    assert climate_thermostat.state == HVAC_MODE_HEAT
    assert climate_thermostat.attributes["hvac_modes"] == [
        HVAC_MODE_AUTO,
        HVAC_MODE_COOL,
        HVAC_MODE_HEAT,
        HVAC_MODE_OFF,
    ]
    assert climate_thermostat.attributes["current_temperature"] == 23.2
    assert climate_thermostat.attributes["temperature"] == 22.2
    assert opp.states.get("sensor.zen_01_battery_level").state == "25"

    # Event signals thermostat state cool

    state_changed_event = {
        "t": "event",
        "e": "changed",
        "r": "sensors",
        "id": "0",
        "config": {"mode": "cool"},
    }
    gateway.api.event_handler(state_changed_event)
    await opp.async_block_till_done()

    assert opp.states.get("climate.zen_01").state == HVAC_MODE_COOL

    # Verify service calls

    mock_deconz_put_request(aioclient_mock, config_entry.data, "/sensors/0/config")

    # Service set temperature to 20

    await opp.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: "climate.zen_01", ATTR_TEMPERATURE: 20},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[1][2] == {"coolsetpoint": 2000.0}


async def test_climate_device_with_fan_support(opp, aioclient_mock):
    """Test successful creation of sensor entities."""
    data = deepcopy(DECONZ_WEB_REQUEST)
    data["sensors"] = {
        "0": {
            "config": {
                "battery": 25,
                "coolsetpoint": None,
                "fanmode": "auto",
                "heatsetpoint": 2222,
                "mode": "heat",
                "offset": 0,
                "on": True,
                "reachable": True,
            },
            "ep": 1,
            "etag": "074549903686a77a12ef0f06c499b1ef",
            "lastseen": "2020-11-27T13:45Z",
            "manufacturername": "Zen Within",
            "modelid": "Zen-01",
            "name": "Zen-01",
            "state": {
                "lastupdated": "2020-11-27T13:42:40.863",
                "on": False,
                "temperature": 2320,
            },
            "type": "ZHAThermostat",
            "uniqueid": "00:24:46:00:00:11:6f:56-01-0201",
        }
    }
    config_entry = await setup_deconz_integration(
        opp, aioclient_mock, get_state_response=data
    )
    gateway = get_gateway_from_config_entry(opp, config_entry)

    assert len(opp.states.async_all()) == 2
    climate_thermostat = opp.states.get("climate.zen_01")
    assert climate_thermostat.state == HVAC_MODE_HEAT
    assert climate_thermostat.attributes["fan_mode"] == FAN_AUTO
    assert climate_thermostat.attributes["fan_modes"] == [
        DECONZ_FAN_SMART,
        FAN_AUTO,
        FAN_HIGH,
        FAN_MEDIUM,
        FAN_LOW,
        FAN_ON,
        FAN_OFF,
    ]

    # Event signals fan mode defaults to off

    state_changed_event = {
        "t": "event",
        "e": "changed",
        "r": "sensors",
        "id": "0",
        "config": {"fanmode": "unsupported"},
    }
    gateway.api.event_handler(state_changed_event)
    await opp.async_block_till_done()

    assert opp.states.get("climate.zen_01").attributes["fan_mode"] == FAN_OFF

    # Event signals unsupported fan mode

    state_changed_event = {
        "t": "event",
        "e": "changed",
        "r": "sensors",
        "id": "0",
        "config": {"fanmode": "unsupported"},
        "state": {"on": True},
    }
    gateway.api.event_handler(state_changed_event)
    await opp.async_block_till_done()

    assert opp.states.get("climate.zen_01").attributes["fan_mode"] == FAN_ON

    # Event signals unsupported fan mode

    state_changed_event = {
        "t": "event",
        "e": "changed",
        "r": "sensors",
        "id": "0",
        "config": {"fanmode": "unsupported"},
    }
    gateway.api.event_handler(state_changed_event)
    await opp.async_block_till_done()

    assert opp.states.get("climate.zen_01").attributes["fan_mode"] == FAN_ON

    # Verify service calls

    mock_deconz_put_request(aioclient_mock, config_entry.data, "/sensors/0/config")

    # Service set fan mode to off

    await opp.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_FAN_MODE,
        {ATTR_ENTITY_ID: "climate.zen_01", ATTR_FAN_MODE: FAN_OFF},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[1][2] == {"fanmode": "off"}

    # Service set fan mode to custom deCONZ mode smart

    await opp.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_FAN_MODE,
        {ATTR_ENTITY_ID: "climate.zen_01", ATTR_FAN_MODE: DECONZ_FAN_SMART},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[2][2] == {"fanmode": "smart"}

    # Service set fan mode to unsupported value

    with pytest.raises(ValueError):
        await opp.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_FAN_MODE,
            {ATTR_ENTITY_ID: "climate.zen_01", ATTR_FAN_MODE: "unsupported"},
            blocking=True,
        )


async def test_climate_device_with_preset(opp, aioclient_mock):
    """Test successful creation of sensor entities."""
    data = deepcopy(DECONZ_WEB_REQUEST)
    data["sensors"] = {
        "0": {
            "config": {
                "battery": 25,
                "coolsetpoint": None,
                "fanmode": None,
                "heatsetpoint": 2222,
                "mode": "heat",
                "preset": "auto",
                "offset": 0,
                "on": True,
                "reachable": True,
            },
            "ep": 1,
            "etag": "074549903686a77a12ef0f06c499b1ef",
            "lastseen": "2020-11-27T13:45Z",
            "manufacturername": "Zen Within",
            "modelid": "Zen-01",
            "name": "Zen-01",
            "state": {
                "lastupdated": "2020-11-27T13:42:40.863",
                "on": False,
                "temperature": 2320,
            },
            "type": "ZHAThermostat",
            "uniqueid": "00:24:46:00:00:11:6f:56-01-0201",
        }
    }
    config_entry = await setup_deconz_integration(
        opp, aioclient_mock, get_state_response=data
    )
    gateway = get_gateway_from_config_entry(opp, config_entry)

    assert len(opp.states.async_all()) == 2

    climate_zen_01 = opp.states.get("climate.zen_01")
    assert climate_zen_01.state == HVAC_MODE_HEAT
    assert climate_zen_01.attributes["current_temperature"] == 23.2
    assert climate_zen_01.attributes["temperature"] == 22.2
    assert climate_zen_01.attributes["preset_mode"] == "auto"
    assert climate_zen_01.attributes["preset_modes"] == [
        "auto",
        "boost",
        "comfort",
        "complex",
        "eco",
        "holiday",
        "manual",
    ]

    # Event signals deCONZ preset

    state_changed_event = {
        "t": "event",
        "e": "changed",
        "r": "sensors",
        "id": "0",
        "config": {"preset": "manual"},
    }
    gateway.api.event_handler(state_changed_event)
    await opp.async_block_till_done()

    assert (
        opp.states.get("climate.zen_01").attributes["preset_mode"]
        == DECONZ_PRESET_MANUAL
    )

    # Event signals unknown preset

    state_changed_event = {
        "t": "event",
        "e": "changed",
        "r": "sensors",
        "id": "0",
        "config": {"preset": "unsupported"},
    }
    gateway.api.event_handler(state_changed_event)
    await opp.async_block_till_done()

    assert opp.states.get("climate.zen_01").attributes["preset_mode"] is None

    # Verify service calls

    mock_deconz_put_request(aioclient_mock, config_entry.data, "/sensors/0/config")

    # Service set preset to OPP preset

    await opp.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: "climate.zen_01", ATTR_PRESET_MODE: PRESET_COMFORT},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[1][2] == {"preset": "comfort"}

    # Service set preset to custom deCONZ preset

    await opp.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: "climate.zen_01", ATTR_PRESET_MODE: DECONZ_PRESET_MANUAL},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[2][2] == {"preset": "manual"}

    # Service set preset to unsupported value

    with pytest.raises(ValueError):
        await opp.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_PRESET_MODE,
            {ATTR_ENTITY_ID: "climate.zen_01", ATTR_PRESET_MODE: "unsupported"},
            blocking=True,
        )


async def test_clip_climate_device(opp, aioclient_mock):
    """Test successful creation of sensor entities."""
    data = deepcopy(DECONZ_WEB_REQUEST)
    data["sensors"] = deepcopy(SENSORS)
    config_entry = await setup_deconz_integration(
        opp,
        aioclient_mock,
        options={CONF_ALLOW_CLIP_SENSOR: True},
        get_state_response=data,
    )

    assert len(opp.states.async_all()) == 3
    assert opp.states.get("climate.thermostat").state == HVAC_MODE_AUTO
    assert opp.states.get("sensor.thermostat") is None
    assert opp.states.get("sensor.thermostat_battery_level").state == "100"
    assert opp.states.get("climate.clip_thermostat").state == HVAC_MODE_HEAT

    # Disallow clip sensors

    opp.config_entries.async_update_entry(
        config_entry, options={CONF_ALLOW_CLIP_SENSOR: False}
    )
    await opp.async_block_till_done()

    assert len(opp.states.async_all()) == 2
    assert opp.states.get("climate.clip_thermostat") is None

    # Allow clip sensors

    opp.config_entries.async_update_entry(
        config_entry, options={CONF_ALLOW_CLIP_SENSOR: True}
    )
    await opp.async_block_till_done()

    assert len(opp.states.async_all()) == 3
    assert opp.states.get("climate.clip_thermostat").state == HVAC_MODE_HEAT


async def test_verify_state_update(opp, aioclient_mock):
    """Test that state update properly."""
    data = deepcopy(DECONZ_WEB_REQUEST)
    data["sensors"] = deepcopy(SENSORS)
    config_entry = await setup_deconz_integration(
        opp, aioclient_mock, get_state_response=data
    )
    gateway = get_gateway_from_config_entry(opp, config_entry)

    assert opp.states.get("climate.thermostat").state == HVAC_MODE_AUTO

    state_changed_event = {
        "t": "event",
        "e": "changed",
        "r": "sensors",
        "id": "1",
        "state": {"on": False},
    }
    gateway.api.event_handler(state_changed_event)
    await opp.async_block_till_done()

    assert opp.states.get("climate.thermostat").state == HVAC_MODE_AUTO
    assert gateway.api.sensors["1"].changed_keys == {"state", "r", "t", "on", "e", "id"}


async def test_add_new_climate_device(opp, aioclient_mock):
    """Test that adding a new climate device works."""
    config_entry = await setup_deconz_integration(opp, aioclient_mock)
    gateway = get_gateway_from_config_entry(opp, config_entry)
    assert len(opp.states.async_all()) == 0

    state_added_event = {
        "t": "event",
        "e": "added",
        "r": "sensors",
        "id": "1",
        "sensor": deepcopy(SENSORS["1"]),
    }
    gateway.api.event_handler(state_added_event)
    await opp.async_block_till_done()

    assert len(opp.states.async_all()) == 2
    assert opp.states.get("climate.thermostat").state == HVAC_MODE_AUTO
    assert opp.states.get("sensor.thermostat_battery_level").state == "100"
