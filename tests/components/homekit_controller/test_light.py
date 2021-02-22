"""Basic checks for HomeKitSwitch."""
from aiohomekit.model.characteristics import CharacteristicsTypes
from aiohomekit.model.services import ServicesTypes

from openpeerpower.components.homekit_controller.const import KNOWN_DEVICES
from openpeerpower.const import STATE_UNAVAILABLE

from tests.components.homekit_controller.common import setup_test_component

LIGHT_BULB_NAME = "Light Bulb"
LIGHT_BULB_ENTITY_ID = "light.testdevice"

LIGHT_ON = ("lightbulb", "on")
LIGHT_BRIGHTNESS = ("lightbulb", "brightness")
LIGHT_HUE = ("lightbulb", "hue")
LIGHT_SATURATION = ("lightbulb", "saturation")
LIGHT_COLOR_TEMP = ("lightbulb", "color-temperature")


def create_lightbulb_service(accessory):
    """Define lightbulb characteristics."""
    service = accessory.add_service(ServicesTypes.LIGHTBULB, name=LIGHT_BULB_NAME)

    on_char = service.add_char(CharacteristicsTypes.ON)
    on_char.value = 0

    brightness = service.add_char(CharacteristicsTypes.BRIGHTNESS)
    brightness.value = 0

    return service


def create_lightbulb_service_with_hs(accessory):
    """Define a lightbulb service with hue + saturation."""
    service = create_lightbulb_service(accessory)

    hue = service.add_char(CharacteristicsTypes.HUE)
    hue.value = 0

    saturation = service.add_char(CharacteristicsTypes.SATURATION)
    saturation.value = 0

    return service


def create_lightbulb_service_with_color_temp(accessory):
    """Define a lightbulb service with color temp."""
    service = create_lightbulb_service(accessory)

    color_temp = service.add_char(CharacteristicsTypes.COLOR_TEMPERATURE)
    color_temp.value = 0

    return service


async def test_switch_change_light_state.opp, utcnow):
    """Test that we can turn a HomeKit light on and off again."""
    helper = await setup_test_component.opp, create_lightbulb_service_with_hs)

    await opp.services.async_call(
        "light",
        "turn_on",
        {"entity_id": "light.testdevice", "brightness": 255, "hs_color": [4, 5]},
        blocking=True,
    )

    assert helper.characteristics[LIGHT_ON].value == 1
    assert helper.characteristics[LIGHT_BRIGHTNESS].value == 100
    assert helper.characteristics[LIGHT_HUE].value == 4
    assert helper.characteristics[LIGHT_SATURATION].value == 5

    await opp.services.async_call(
        "light", "turn_off", {"entity_id": "light.testdevice"}, blocking=True
    )
    assert helper.characteristics[LIGHT_ON].value == 0


async def test_switch_change_light_state_color_temp.opp, utcnow):
    """Test that we can turn change color_temp."""
    helper = await setup_test_component.opp, create_lightbulb_service_with_color_temp)

    await opp.services.async_call(
        "light",
        "turn_on",
        {"entity_id": "light.testdevice", "brightness": 255, "color_temp": 400},
        blocking=True,
    )
    assert helper.characteristics[LIGHT_ON].value == 1
    assert helper.characteristics[LIGHT_BRIGHTNESS].value == 100
    assert helper.characteristics[LIGHT_COLOR_TEMP].value == 400


async def test_switch_read_light_state.opp, utcnow):
    """Test that we can read the state of a HomeKit light accessory."""
    helper = await setup_test_component.opp, create_lightbulb_service_with_hs)

    # Initial state is that the light is off
    state = await helper.poll_and_get_state()
    assert state.state == "off"

    # Simulate that someone switched on the device in the real world not via HA
    helper.characteristics[LIGHT_ON].set_value(True)
    helper.characteristics[LIGHT_BRIGHTNESS].value = 100
    helper.characteristics[LIGHT_HUE].value = 4
    helper.characteristics[LIGHT_SATURATION].value = 5
    state = await helper.poll_and_get_state()
    assert state.state == "on"
    assert state.attributes["brightness"] == 255
    assert state.attributes["hs_color"] == (4, 5)

    # Simulate that device switched off in the real world not via HA
    helper.characteristics[LIGHT_ON].set_value(False)
    state = await helper.poll_and_get_state()
    assert state.state == "off"


async def test_switch_push_light_state.opp, utcnow):
    """Test that we can read the state of a HomeKit light accessory."""
    helper = await setup_test_component.opp, create_lightbulb_service_with_hs)

    # Initial state is that the light is off
    state = opp.states.get(LIGHT_BULB_ENTITY_ID)
    assert state.state == "off"

    await helper.update_named_service(
        LIGHT_BULB_NAME,
        {
            CharacteristicsTypes.ON: True,
            CharacteristicsTypes.BRIGHTNESS: 100,
            CharacteristicsTypes.HUE: 4,
            CharacteristicsTypes.SATURATION: 5,
        },
    )

    state = opp.states.get(LIGHT_BULB_ENTITY_ID)
    assert state.state == "on"
    assert state.attributes["brightness"] == 255
    assert state.attributes["hs_color"] == (4, 5)

    # Simulate that device switched off in the real world not via HA
    await helper.update_named_service(LIGHT_BULB_NAME, {CharacteristicsTypes.ON: False})
    state = opp.states.get(LIGHT_BULB_ENTITY_ID)
    assert state.state == "off"


async def test_switch_read_light_state_color_temp.opp, utcnow):
    """Test that we can read the color_temp of a  light accessory."""
    helper = await setup_test_component.opp, create_lightbulb_service_with_color_temp)

    # Initial state is that the light is off
    state = await helper.poll_and_get_state()
    assert state.state == "off"

    # Simulate that someone switched on the device in the real world not via HA
    helper.characteristics[LIGHT_ON].set_value(True)
    helper.characteristics[LIGHT_BRIGHTNESS].value = 100
    helper.characteristics[LIGHT_COLOR_TEMP].value = 400

    state = await helper.poll_and_get_state()
    assert state.state == "on"
    assert state.attributes["brightness"] == 255
    assert state.attributes["color_temp"] == 400


async def test_switch_push_light_state_color_temp.opp, utcnow):
    """Test that we can read the state of a HomeKit light accessory."""
    helper = await setup_test_component.opp, create_lightbulb_service_with_color_temp)

    # Initial state is that the light is off
    state = opp.states.get(LIGHT_BULB_ENTITY_ID)
    assert state.state == "off"

    await helper.update_named_service(
        LIGHT_BULB_NAME,
        {
            CharacteristicsTypes.ON: True,
            CharacteristicsTypes.BRIGHTNESS: 100,
            CharacteristicsTypes.COLOR_TEMPERATURE: 400,
        },
    )

    state = opp.states.get(LIGHT_BULB_ENTITY_ID)
    assert state.state == "on"
    assert state.attributes["brightness"] == 255
    assert state.attributes["color_temp"] == 400


async def test_light_becomes_unavailable_but_recovers.opp, utcnow):
    """Test transition to and from unavailable state."""
    helper = await setup_test_component.opp, create_lightbulb_service_with_color_temp)

    # Initial state is that the light is off
    state = await helper.poll_and_get_state()
    assert state.state == "off"

    # Test device goes offline
    helper.pairing.available = False
    state = await helper.poll_and_get_state()
    assert state.state == "unavailable"

    # Simulate that someone switched on the device in the real world not via HA
    helper.characteristics[LIGHT_ON].set_value(True)
    helper.characteristics[LIGHT_BRIGHTNESS].value = 100
    helper.characteristics[LIGHT_COLOR_TEMP].value = 400
    helper.pairing.available = True

    state = await helper.poll_and_get_state()
    assert state.state == "on"
    assert state.attributes["brightness"] == 255
    assert state.attributes["color_temp"] == 400


async def test_light_unloaded_removed.opp, utcnow):
    """Test entity and HKDevice are correctly unloaded and removed."""
    helper = await setup_test_component.opp, create_lightbulb_service_with_color_temp)

    # Initial state is that the light is off
    state = await helper.poll_and_get_state()
    assert state.state == "off"

    unload_result = await helper.config_entry.async_unload.opp)
    assert unload_result is True

    # Make sure entity is set to unavailable state
    assert.opp.states.get(helper.entity_id).state == STATE_UNAVAILABLE

    # Make sure HKDevice is no longer set to poll this accessory
    conn = opp.data[KNOWN_DEVICES]["00:00:00:00:00:00"]
    assert not conn.pollable_characteristics

    await helper.config_entry.async_remove.opp)
    await opp.async_block_till_done()

    # Make sure entity is removed
    assert.opp.states.get(helper.entity_id).state == STATE_UNAVAILABLE
