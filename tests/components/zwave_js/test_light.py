"""Test the Z-Wave JS light platform."""
from copy import deepcopy

from zwave_js_server.event import Event

from openpeerpower.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_MODE,
    ATTR_COLOR_TEMP,
    ATTR_MAX_MIREDS,
    ATTR_MIN_MIREDS,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    ATTR_SUPPORTED_COLOR_MODES,
    SUPPORT_TRANSITION,
)
from openpeerpower.const import ATTR_SUPPORTED_FEATURES, STATE_OFF, STATE_ON

from .common import (
    AEON_SMART_SWITCH_LIGHT_ENTITY,
    BULB_6_MULTI_COLOR_LIGHT_ENTITY,
    EATON_RF9640_ENTITY,
    ZEN_31_ENTITY,
)


async def test_light(opp, client, bulb_6_multi_color, integration):
    """Test the light entity."""
    node = bulb_6_multi_color
    state = opp.states.get(BULB_6_MULTI_COLOR_LIGHT_ENTITY)

    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_MIN_MIREDS] == 153
    assert state.attributes[ATTR_MAX_MIREDS] == 370
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == SUPPORT_TRANSITION
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == ["color_temp", "hs"]

    # Test turning on
    await opp.services.async_call(
        "light",
        "turn_on",
        {"entity_id": BULB_6_MULTI_COLOR_LIGHT_ENTITY},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 39
    assert args["valueId"] == {
        "commandClassName": "Multilevel Switch",
        "commandClass": 38,
        "endpoint": 0,
        "property": "targetValue",
        "propertyName": "targetValue",
        "metadata": {
            "label": "Target value",
            "max": 99,
            "min": 0,
            "type": "number",
            "readable": True,
            "writeable": True,
            "label": "Target value",
        },
    }
    assert args["value"] == 255

    client.async_send_command.reset_mock()

    # Test brightness update from value updated event
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 39,
            "args": {
                "commandClassName": "Multilevel Switch",
                "commandClass": 38,
                "endpoint": 0,
                "property": "currentValue",
                "newValue": 99,
                "prevValue": 0,
                "propertyName": "currentValue",
            },
        },
    )
    node.receive_event(event)

    state = opp.states.get(BULB_6_MULTI_COLOR_LIGHT_ENTITY)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_COLOR_MODE] == "color_temp"
    assert state.attributes[ATTR_BRIGHTNESS] == 255
    assert state.attributes[ATTR_COLOR_TEMP] == 370
    assert ATTR_RGB_COLOR not in state.attributes

    # Test turning on with same brightness
    await opp.services.async_call(
        "light",
        "turn_on",
        {"entity_id": BULB_6_MULTI_COLOR_LIGHT_ENTITY, ATTR_BRIGHTNESS: 255},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1

    client.async_send_command.reset_mock()

    # Test turning on with brightness
    await opp.services.async_call(
        "light",
        "turn_on",
        {"entity_id": BULB_6_MULTI_COLOR_LIGHT_ENTITY, ATTR_BRIGHTNESS: 129},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 39
    assert args["valueId"] == {
        "commandClassName": "Multilevel Switch",
        "commandClass": 38,
        "endpoint": 0,
        "property": "targetValue",
        "propertyName": "targetValue",
        "metadata": {
            "label": "Target value",
            "max": 99,
            "min": 0,
            "type": "number",
            "readable": True,
            "writeable": True,
            "label": "Target value",
        },
    }
    assert args["value"] == 50

    client.async_send_command.reset_mock()

    # Test turning on with rgb color
    await opp.services.async_call(
        "light",
        "turn_on",
        {"entity_id": BULB_6_MULTI_COLOR_LIGHT_ENTITY, ATTR_RGB_COLOR: (255, 76, 255)},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 6
    warm_args = client.async_send_command.call_args_list[0][0][0]  # red 255
    assert warm_args["command"] == "node.set_value"
    assert warm_args["nodeId"] == 39
    assert warm_args["valueId"]["commandClassName"] == "Color Switch"
    assert warm_args["valueId"]["commandClass"] == 51
    assert warm_args["valueId"]["endpoint"] == 0
    assert warm_args["valueId"]["metadata"]["label"] == "Target value (Red)"
    assert warm_args["valueId"]["property"] == "targetColor"
    assert warm_args["valueId"]["propertyName"] == "targetColor"
    assert warm_args["value"] == 255

    cold_args = client.async_send_command.call_args_list[1][0][0]  # green 76
    assert cold_args["command"] == "node.set_value"
    assert cold_args["nodeId"] == 39
    assert cold_args["valueId"]["commandClassName"] == "Color Switch"
    assert cold_args["valueId"]["commandClass"] == 51
    assert cold_args["valueId"]["endpoint"] == 0
    assert cold_args["valueId"]["metadata"]["label"] == "Target value (Green)"
    assert cold_args["valueId"]["property"] == "targetColor"
    assert cold_args["valueId"]["propertyName"] == "targetColor"
    assert cold_args["value"] == 76
    red_args = client.async_send_command.call_args_list[2][0][0]  # blue 255
    assert red_args["command"] == "node.set_value"
    assert red_args["nodeId"] == 39
    assert red_args["valueId"]["commandClassName"] == "Color Switch"
    assert red_args["valueId"]["commandClass"] == 51
    assert red_args["valueId"]["endpoint"] == 0
    assert red_args["valueId"]["metadata"]["label"] == "Target value (Blue)"
    assert red_args["valueId"]["property"] == "targetColor"
    assert red_args["valueId"]["propertyName"] == "targetColor"
    assert red_args["value"] == 255
    green_args = client.async_send_command.call_args_list[3][0][0]  # warm white 0
    assert green_args["command"] == "node.set_value"
    assert green_args["nodeId"] == 39
    assert green_args["valueId"]["commandClassName"] == "Color Switch"
    assert green_args["valueId"]["commandClass"] == 51
    assert green_args["valueId"]["endpoint"] == 0
    assert green_args["valueId"]["metadata"]["label"] == "Target value (Warm White)"
    assert green_args["valueId"]["property"] == "targetColor"
    assert green_args["valueId"]["propertyName"] == "targetColor"
    assert green_args["value"] == 0
    blue_args = client.async_send_command.call_args_list[4][0][0]  # cold white 0
    assert blue_args["command"] == "node.set_value"
    assert blue_args["nodeId"] == 39
    assert blue_args["valueId"]["commandClassName"] == "Color Switch"
    assert blue_args["valueId"]["commandClass"] == 51
    assert blue_args["valueId"]["endpoint"] == 0
    assert blue_args["valueId"]["metadata"]["label"] == "Target value (Cold White)"
    assert blue_args["valueId"]["property"] == "targetColor"
    assert blue_args["valueId"]["propertyName"] == "targetColor"
    assert blue_args["value"] == 0

    # Test rgb color update from value updated event
    red_event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 39,
            "args": {
                "commandClassName": "Color Switch",
                "commandClass": 51,
                "endpoint": 0,
                "property": "currentColor",
                "newValue": 255,
                "prevValue": 0,
                "propertyKey": 2,
                "propertyKeyName": "Red",
            },
        },
    )
    green_event = deepcopy(red_event)
    green_event.data["args"].update(
        {"newValue": 76, "propertyKey": 3, "propertyKeyName": "Green"}
    )
    blue_event = deepcopy(red_event)
    blue_event.data["args"]["propertyKey"] = 4
    blue_event.data["args"]["propertyKeyName"] = "Blue"
    warm_white_event = deepcopy(red_event)
    warm_white_event.data["args"].update(
        {"newValue": 0, "propertyKey": 0, "propertyKeyName": "Warm White"}
    )
    node.receive_event(warm_white_event)
    node.receive_event(red_event)
    node.receive_event(green_event)
    node.receive_event(blue_event)

    state = opp.states.get(BULB_6_MULTI_COLOR_LIGHT_ENTITY)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_COLOR_MODE] == "hs"
    assert state.attributes[ATTR_BRIGHTNESS] == 255
    assert state.attributes[ATTR_RGB_COLOR] == (255, 76, 255)
    assert ATTR_COLOR_TEMP not in state.attributes

    client.async_send_command.reset_mock()

    # Test turning on with same rgb color
    await opp.services.async_call(
        "light",
        "turn_on",
        {"entity_id": BULB_6_MULTI_COLOR_LIGHT_ENTITY, ATTR_RGB_COLOR: (255, 76, 255)},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 6

    client.async_send_command.reset_mock()

    # Test turning on with color temp
    await opp.services.async_call(
        "light",
        "turn_on",
        {"entity_id": BULB_6_MULTI_COLOR_LIGHT_ENTITY, ATTR_COLOR_TEMP: 170},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 6
    red_args = client.async_send_command.call_args_list[0][0][0]  # red 0
    assert red_args["command"] == "node.set_value"
    assert red_args["nodeId"] == 39
    assert red_args["valueId"]["commandClassName"] == "Color Switch"
    assert red_args["valueId"]["commandClass"] == 51
    assert red_args["valueId"]["endpoint"] == 0
    assert red_args["valueId"]["metadata"]["label"] == "Target value (Red)"
    assert red_args["valueId"]["property"] == "targetColor"
    assert red_args["valueId"]["propertyName"] == "targetColor"
    assert red_args["value"] == 0
    red_args = client.async_send_command.call_args_list[1][0][0]  # green 0
    assert red_args["command"] == "node.set_value"
    assert red_args["nodeId"] == 39
    assert red_args["valueId"]["commandClassName"] == "Color Switch"
    assert red_args["valueId"]["commandClass"] == 51
    assert red_args["valueId"]["endpoint"] == 0
    assert red_args["valueId"]["metadata"]["label"] == "Target value (Green)"
    assert red_args["valueId"]["property"] == "targetColor"
    assert red_args["valueId"]["propertyName"] == "targetColor"
    assert red_args["value"] == 0
    red_args = client.async_send_command.call_args_list[2][0][0]  # blue 0
    assert red_args["command"] == "node.set_value"
    assert red_args["nodeId"] == 39
    assert red_args["valueId"]["commandClassName"] == "Color Switch"
    assert red_args["valueId"]["commandClass"] == 51
    assert red_args["valueId"]["endpoint"] == 0
    assert red_args["valueId"]["metadata"]["label"] == "Target value (Blue)"
    assert red_args["valueId"]["property"] == "targetColor"
    assert red_args["valueId"]["propertyName"] == "targetColor"
    assert red_args["value"] == 0
    warm_args = client.async_send_command.call_args_list[3][0][0]  # warm white 0
    assert warm_args["command"] == "node.set_value"
    assert warm_args["nodeId"] == 39
    assert warm_args["valueId"]["commandClassName"] == "Color Switch"
    assert warm_args["valueId"]["commandClass"] == 51
    assert warm_args["valueId"]["endpoint"] == 0
    assert warm_args["valueId"]["metadata"]["label"] == "Target value (Warm White)"
    assert warm_args["valueId"]["property"] == "targetColor"
    assert warm_args["valueId"]["propertyName"] == "targetColor"
    assert warm_args["value"] == 20
    red_args = client.async_send_command.call_args_list[4][0][0]  # cold white
    assert red_args["command"] == "node.set_value"
    assert red_args["nodeId"] == 39
    assert red_args["valueId"]["commandClassName"] == "Color Switch"
    assert red_args["valueId"]["commandClass"] == 51
    assert red_args["valueId"]["endpoint"] == 0
    assert red_args["valueId"]["metadata"]["label"] == "Target value (Cold White)"
    assert red_args["valueId"]["property"] == "targetColor"
    assert red_args["valueId"]["propertyName"] == "targetColor"
    assert red_args["value"] == 235

    client.async_send_command.reset_mock()

    # Test color temp update from value updated event
    red_event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 39,
            "args": {
                "commandClassName": "Color Switch",
                "commandClass": 51,
                "endpoint": 0,
                "property": "currentColor",
                "newValue": 0,
                "prevValue": 255,
                "propertyKey": 2,
                "propertyKeyName": "Red",
            },
        },
    )
    green_event = deepcopy(red_event)
    green_event.data["args"].update(
        {"newValue": 0, "prevValue": 76, "propertyKey": 3, "propertyKeyName": "Green"}
    )
    blue_event = deepcopy(red_event)
    blue_event.data["args"]["propertyKey"] = 4
    blue_event.data["args"]["propertyKeyName"] = "Blue"
    warm_white_event = deepcopy(red_event)
    warm_white_event.data["args"].update(
        {"newValue": 20, "propertyKey": 0, "propertyKeyName": "Warm White"}
    )
    cold_white_event = deepcopy(red_event)
    cold_white_event.data["args"].update(
        {"newValue": 235, "propertyKey": 1, "propertyKeyName": "Cold White"}
    )
    node.receive_event(red_event)
    node.receive_event(green_event)
    node.receive_event(blue_event)
    node.receive_event(warm_white_event)
    node.receive_event(cold_white_event)

    state = opp.states.get(BULB_6_MULTI_COLOR_LIGHT_ENTITY)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_COLOR_MODE] == "color_temp"
    assert state.attributes[ATTR_BRIGHTNESS] == 255
    assert state.attributes[ATTR_COLOR_TEMP] == 170
    assert ATTR_RGB_COLOR not in state.attributes

    # Test turning on with same color temp
    await opp.services.async_call(
        "light",
        "turn_on",
        {"entity_id": BULB_6_MULTI_COLOR_LIGHT_ENTITY, ATTR_COLOR_TEMP: 170},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 6

    client.async_send_command.reset_mock()

    # Test turning off
    await opp.services.async_call(
        "light",
        "turn_off",
        {"entity_id": BULB_6_MULTI_COLOR_LIGHT_ENTITY},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 39
    assert args["valueId"] == {
        "commandClassName": "Multilevel Switch",
        "commandClass": 38,
        "endpoint": 0,
        "property": "targetValue",
        "propertyName": "targetValue",
        "metadata": {
            "label": "Target value",
            "max": 99,
            "min": 0,
            "type": "number",
            "readable": True,
            "writeable": True,
            "label": "Target value",
        },
    }
    assert args["value"] == 0


async def test_v4_dimmer_light(opp, client, eaton_rf9640_dimmer, integration):
    """Test a light that supports MultiLevelSwitch CommandClass version 4."""
    state = opp.states.get(EATON_RF9640_ENTITY)

    assert state
    assert state.state == STATE_ON
    # the light should pick currentvalue which has zwave value 22
    assert state.attributes[ATTR_BRIGHTNESS] == 57


async def test_optional_light(opp, client, aeon_smart_switch_6, integration):
    """Test a device that has an additional light endpoint being identified as light."""
    state = opp.states.get(AEON_SMART_SWITCH_LIGHT_ENTITY)
    assert state.state == STATE_ON


async def test_rgbw_light(opp, client, zen_31, integration):
    """Test the light entity."""
    zen_31
    state = opp.states.get(ZEN_31_ENTITY)

    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == SUPPORT_TRANSITION

    # Test turning on
    await opp.services.async_call(
        "light",
        "turn_on",
        {"entity_id": ZEN_31_ENTITY, ATTR_RGBW_COLOR: (0, 0, 0, 128)},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 2
    args = client.async_send_command.call_args_list[0][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 94
    assert args["valueId"] == {
        "commandClassName": "Color Switch",
        "commandClass": 51,
        "endpoint": 1,
        "property": "targetColor",
        "propertyName": "targetColor",
        "ccVersion": 0,
        "metadata": {
            "label": "Target Color",
            "type": "any",
            "readable": True,
            "writeable": True,
        },
        "value": {"blue": 70, "green": 159, "red": 255, "warmWhite": 141},
    }
    assert args["value"] == {"blue": 0, "green": 0, "red": 0, "warmWhite": 128}

    args = client.async_send_command.call_args_list[1][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 94
    assert args["valueId"] == {
        "commandClassName": "Multilevel Switch",
        "commandClass": 38,
        "endpoint": 1,
        "property": "targetValue",
        "propertyName": "targetValue",
        "ccVersion": 0,
        "metadata": {
            "label": "Target value",
            "max": 99,
            "min": 0,
            "type": "number",
            "readable": True,
            "writeable": True,
            "label": "Target value",
        },
        "value": 59,
    }
    assert args["value"] == 255

    client.async_send_command.reset_mock()


async def test_light_none_color_value(opp, light_color_null_values, integration):
    """Test the light entity can handle None value in current color Value."""
    entity_id = "light.repeater"
    state = opp.states.get(entity_id)

    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == SUPPORT_TRANSITION
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == ["hs"]
