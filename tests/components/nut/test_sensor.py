"""The sensor tests for the nut platform."""

from openpeerpower.const import PERCENTAGE

from .util import async_init_integration


async def test_pr3000rt2u.opp):
    """Test creation of PR3000RT2U sensors."""

    await async_init_integration(opp, "PR3000RT2U", ["battery.charge"])
    registry = await opp.helpers.entity_registry.async_get_registry()
    entry = registry.async_get("sensor.ups1_battery_charge")
    assert entry
    assert entry.unique_id == "CPS_PR3000RT2U_PYVJO2000034_battery.charge"

    state = opp.states.get("sensor.ups1_battery_charge")
    assert state.state == "100"

    expected_attributes = {
        "device_class": "battery",
        "friendly_name": "Ups1 Battery Charge",
        "state": "Online",
        "unit_of_measurement": PERCENTAGE,
    }
    # Only test for a subset of attributes in case
    # HA changes the implementation and a new one appears
    assert all(
        state.attributes[key] == expected_attributes[key] for key in expected_attributes
    )


async def test_cp1350c.opp):
    """Test creation of CP1350C sensors."""

    config_entry = await async_init_integration(opp, "CP1350C", ["battery.charge"])

    registry = await opp.helpers.entity_registry.async_get_registry()
    entry = registry.async_get("sensor.ups1_battery_charge")
    assert entry
    assert entry.unique_id == f"{config_entry.entry_id}_battery.charge"

    state = opp.states.get("sensor.ups1_battery_charge")
    assert state.state == "100"

    expected_attributes = {
        "device_class": "battery",
        "friendly_name": "Ups1 Battery Charge",
        "state": "Online",
        "unit_of_measurement": PERCENTAGE,
    }
    # Only test for a subset of attributes in case
    # HA changes the implementation and a new one appears
    assert all(
        state.attributes[key] == expected_attributes[key] for key in expected_attributes
    )


async def test_5e850i.opp):
    """Test creation of 5E850I sensors."""

    config_entry = await async_init_integration(opp, "5E850I", ["battery.charge"])
    registry = await opp.helpers.entity_registry.async_get_registry()
    entry = registry.async_get("sensor.ups1_battery_charge")
    assert entry
    assert entry.unique_id == f"{config_entry.entry_id}_battery.charge"

    state = opp.states.get("sensor.ups1_battery_charge")
    assert state.state == "100"

    expected_attributes = {
        "device_class": "battery",
        "friendly_name": "Ups1 Battery Charge",
        "state": "Online",
        "unit_of_measurement": PERCENTAGE,
    }
    # Only test for a subset of attributes in case
    # HA changes the implementation and a new one appears
    assert all(
        state.attributes[key] == expected_attributes[key] for key in expected_attributes
    )


async def test_5e650i.opp):
    """Test creation of 5E650I sensors."""

    config_entry = await async_init_integration(opp, "5E650I", ["battery.charge"])
    registry = await opp.helpers.entity_registry.async_get_registry()
    entry = registry.async_get("sensor.ups1_battery_charge")
    assert entry
    assert entry.unique_id == f"{config_entry.entry_id}_battery.charge"

    state = opp.states.get("sensor.ups1_battery_charge")
    assert state.state == "100"

    expected_attributes = {
        "device_class": "battery",
        "friendly_name": "Ups1 Battery Charge",
        "state": "Online Battery Charging",
        "unit_of_measurement": PERCENTAGE,
    }
    # Only test for a subset of attributes in case
    # HA changes the implementation and a new one appears
    assert all(
        state.attributes[key] == expected_attributes[key] for key in expected_attributes
    )


async def test_backupsses600m1.opp):
    """Test creation of BACKUPSES600M1 sensors."""

    await async_init_integration(opp, "BACKUPSES600M1", ["battery.charge"])
    registry = await opp.helpers.entity_registry.async_get_registry()
    entry = registry.async_get("sensor.ups1_battery_charge")
    assert entry
    assert (
        entry.unique_id
        == "American Power Conversion_Back-UPS ES 600M1_4B1713P32195 _battery.charge"
    )

    state = opp.states.get("sensor.ups1_battery_charge")
    assert state.state == "100"

    expected_attributes = {
        "device_class": "battery",
        "friendly_name": "Ups1 Battery Charge",
        "state": "Online",
        "unit_of_measurement": PERCENTAGE,
    }
    # Only test for a subset of attributes in case
    # HA changes the implementation and a new one appears
    assert all(
        state.attributes[key] == expected_attributes[key] for key in expected_attributes
    )


async def test_cp1500pfclcd.opp):
    """Test creation of CP1500PFCLCD sensors."""

    config_entry = await async_init_integration(
        opp. "CP1500PFCLCD", ["battery.charge"]
    )
    registry = await opp.helpers.entity_registry.async_get_registry()
    entry = registry.async_get("sensor.ups1_battery_charge")
    assert entry
    assert entry.unique_id == f"{config_entry.entry_id}_battery.charge"

    state = opp.states.get("sensor.ups1_battery_charge")
    assert state.state == "100"

    expected_attributes = {
        "device_class": "battery",
        "friendly_name": "Ups1 Battery Charge",
        "state": "Online",
        "unit_of_measurement": PERCENTAGE,
    }
    # Only test for a subset of attributes in case
    # HA changes the implementation and a new one appears
    assert all(
        state.attributes[key] == expected_attributes[key] for key in expected_attributes
    )


async def test_dl650elcd.opp):
    """Test creation of DL650ELCD sensors."""

    config_entry = await async_init_integration(opp, "DL650ELCD", ["battery.charge"])
    registry = await opp.helpers.entity_registry.async_get_registry()
    entry = registry.async_get("sensor.ups1_battery_charge")
    assert entry
    assert entry.unique_id == f"{config_entry.entry_id}_battery.charge"

    state = opp.states.get("sensor.ups1_battery_charge")
    assert state.state == "100"

    expected_attributes = {
        "device_class": "battery",
        "friendly_name": "Ups1 Battery Charge",
        "state": "Online",
        "unit_of_measurement": PERCENTAGE,
    }
    # Only test for a subset of attributes in case
    # HA changes the implementation and a new one appears
    assert all(
        state.attributes[key] == expected_attributes[key] for key in expected_attributes
    )


async def test_blazer_usb.opp):
    """Test creation of blazer_usb sensors."""

    config_entry = await async_init_integration(opp, "blazer_usb", ["battery.charge"])
    registry = await opp.helpers.entity_registry.async_get_registry()
    entry = registry.async_get("sensor.ups1_battery_charge")
    assert entry
    assert entry.unique_id == f"{config_entry.entry_id}_battery.charge"

    state = opp.states.get("sensor.ups1_battery_charge")
    assert state.state == "100"

    expected_attributes = {
        "device_class": "battery",
        "friendly_name": "Ups1 Battery Charge",
        "state": "Online",
        "unit_of_measurement": PERCENTAGE,
    }
    # Only test for a subset of attributes in case
    # HA changes the implementation and a new one appears
    assert all(
        state.attributes[key] == expected_attributes[key] for key in expected_attributes
    )
