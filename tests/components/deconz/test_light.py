"""deCONZ light platform tests."""

from copy import deepcopy

import pytest

from openpeerpower.components.deconz.const import CONF_ALLOW_DECONZ_GROUPS
from openpeerpower.components.deconz.gateway import get_gateway_from_config_entry
from openpeerpower.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_EFFECT,
    ATTR_FLASH,
    ATTR_HS_COLOR,
    ATTR_MAX_MIREDS,
    ATTR_MIN_MIREDS,
    ATTR_TRANSITION,
    DOMAIN as LIGHT_DOMAIN,
    EFFECT_COLORLOOP,
    FLASH_LONG,
    FLASH_SHORT,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)

from .test_gateway import (
    DECONZ_WEB_REQUEST,
    mock_deconz_put_request,
    setup_deconz_integration,
)

GROUPS = {
    "1": {
        "id": "Light group id",
        "name": "Light group",
        "type": "LightGroup",
        "state": {"all_on": False, "any_on": True},
        "action": {},
        "scenes": [],
        "lights": ["1", "2"],
    },
    "2": {
        "id": "Empty group id",
        "name": "Empty group",
        "type": "LightGroup",
        "state": {},
        "action": {},
        "scenes": [],
        "lights": [],
    },
}

LIGHTS = {
    "1": {
        "id": "RGB light id",
        "name": "RGB light",
        "state": {
            "on": True,
            "bri": 255,
            "colormode": "xy",
            "effect": "colorloop",
            "xy": (500, 500),
            "reachable": True,
        },
        "type": "Extended color light",
        "uniqueid": "00:00:00:00:00:00:00:00-00",
    },
    "2": {
        "ctmax": 454,
        "ctmin": 155,
        "id": "Tunable white light id",
        "name": "Tunable white light",
        "state": {"on": True, "colormode": "ct", "ct": 2500, "reachable": True},
        "type": "Tunable white light",
        "uniqueid": "00:00:00:00:00:00:00:01-00",
    },
    "3": {
        "id": "On off switch id",
        "name": "On off switch",
        "type": "On/Off plug-in unit",
        "state": {"reachable": True},
        "uniqueid": "00:00:00:00:00:00:00:02-00",
    },
    "4": {
        "name": "On off light",
        "state": {"on": True, "reachable": True},
        "type": "On and Off light",
        "uniqueid": "00:00:00:00:00:00:00:03-00",
    },
    "5": {
        "ctmax": 1000,
        "ctmin": 0,
        "id": "Tunable white light with bad maxmin values id",
        "name": "Tunable white light with bad maxmin values",
        "state": {"on": True, "colormode": "ct", "ct": 2500, "reachable": True},
        "type": "Tunable white light",
        "uniqueid": "00:00:00:00:00:00:00:04-00",
    },
}


async def test_no_lights_or_groups.opp, aioclient_mock):
    """Test that no lights or groups entities are created."""
    await setup_deconz_integration.opp, aioclient_mock)
    assert len.opp.states.async_all()) == 0


async def test_lights_and_groups.opp, aioclient_mock):
    """Test that lights or groups entities are created."""
    data = deepcopy(DECONZ_WEB_REQUEST)
    data["groups"] = deepcopy(GROUPS)
    data["lights"] = deepcopy(LIGHTS)
    config_entry = await setup_deconz_integration(
       .opp, aioclient_mock, get_state_response=data
    )
    gateway = get_gateway_from_config_entry.opp, config_entry)

    assert len.opp.states.async_all()) == 6

    rgb_light = opp.states.get("light.rgb_light")
    assert rgb_light.state == STATE_ON
    assert rgb_light.attributes[ATTR_BRIGHTNESS] == 255
    assert rgb_light.attributes[ATTR_HS_COLOR] == (224.235, 100.0)
    assert rgb_light.attributes["is_deconz_group"] is False
    assert rgb_light.attributes[ATTR_SUPPORTED_FEATURES] == 61

    tunable_white_light = opp.states.get("light.tunable_white_light")
    assert tunable_white_light.state == STATE_ON
    assert tunable_white_light.attributes[ATTR_COLOR_TEMP] == 2500
    assert tunable_white_light.attributes[ATTR_MAX_MIREDS] == 454
    assert tunable_white_light.attributes[ATTR_MIN_MIREDS] == 155
    assert tunable_white_light.attributes[ATTR_SUPPORTED_FEATURES] == 2

    tunable_white_light_bad_maxmin = opp.states.get(
        "light.tunable_white_light_with_bad_maxmin_values"
    )
    assert tunable_white_light_bad_maxmin.state == STATE_ON
    assert tunable_white_light_bad_maxmin.attributes[ATTR_COLOR_TEMP] == 2500
    assert tunable_white_light_bad_maxmin.attributes[ATTR_MAX_MIREDS] == 650
    assert tunable_white_light_bad_maxmin.attributes[ATTR_MIN_MIREDS] == 140
    assert tunable_white_light_bad_maxmin.attributes[ATTR_SUPPORTED_FEATURES] == 2

    on_off_light = opp.states.get("light.on_off_light")
    assert on_off_light.state == STATE_ON
    assert on_off_light.attributes[ATTR_SUPPORTED_FEATURES] == 0

    light_group = opp.states.get("light.light_group")
    assert light_group.state == STATE_ON
    assert light_group.attributes["all_on"] is False

    empty_group = opp.states.get("light.empty_group")
    assert empty_group is None

    state_changed_event = {
        "t": "event",
        "e": "changed",
        "r": "lights",
        "id": "1",
        "state": {"on": False},
    }
    gateway.api.event_op.dler(state_changed_event)
    await.opp.async_block_till_done()

    rgb_light = opp.states.get("light.rgb_light")
    assert rgb_light.state == STATE_OFF

    # Verify service calls

    mock_deconz_put_request(aioclient_mock, config_entry.data, "/lights/1/state")

    # Service turn on light with short color loop

    await.opp.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: "light.rgb_light",
            ATTR_COLOR_TEMP: 2500,
            ATTR_BRIGHTNESS: 200,
            ATTR_TRANSITION: 5,
            ATTR_FLASH: FLASH_SHORT,
            ATTR_EFFECT: EFFECT_COLORLOOP,
        },
        blocking=True,
    )
    assert aioclient_mock.mock_calls[1][2] == {
        "ct": 2500,
        "bri": 200,
        "transitiontime": 50,
        "alert": "select",
        "effect": "colorloop",
    }

    # Service turn on light disabling color loop with long flashing

    await.opp.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: "light.rgb_light",
            ATTR_HS_COLOR: (20, 30),
            ATTR_FLASH: FLASH_LONG,
            ATTR_EFFECT: "None",
        },
        blocking=True,
    )
    assert aioclient_mock.mock_calls[2][2] == {
        "xy": (0.411, 0.351),
        "alert": "lselect",
        "effect": "none",
    }

    # Service turn on light with short flashing not supported

    await.opp.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {
            ATTR_ENTITY_ID: "light.rgb_light",
            ATTR_TRANSITION: 5,
            ATTR_FLASH: FLASH_SHORT,
        },
        blocking=True,
    )
    assert len(aioclient_mock.mock_calls) == 3  # Not called

    state_changed_event = {
        "t": "event",
        "e": "changed",
        "r": "lights",
        "id": "1",
        "state": {"on": True},
    }
    gateway.api.event_op.dler(state_changed_event)
    await.opp.async_block_till_done()

    # Service turn off light with short flashing

    await.opp.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {
            ATTR_ENTITY_ID: "light.rgb_light",
            ATTR_TRANSITION: 5,
            ATTR_FLASH: FLASH_SHORT,
        },
        blocking=True,
    )
    assert aioclient_mock.mock_calls[3][2] == {
        "bri": 0,
        "transitiontime": 50,
        "alert": "select",
    }

    # Service turn off light with long flashing

    await.opp.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "light.rgb_light", ATTR_FLASH: FLASH_LONG},
        blocking=True,
    )
    assert aioclient_mock.mock_calls[4][2] == {"alert": "lselect"}

    await.opp.config_entries.async_unload(config_entry.entry_id)

    states = opp.states.async_all()
    assert len.opp.states.async_all()) == 6
    for state in states:
        assert state.state == STATE_UNAVAILABLE

    await.opp.config_entries.async_remove(config_entry.entry_id)
    await.opp.async_block_till_done()
    assert len.opp.states.async_all()) == 0


async def test_disable_light_groups.opp, aioclient_mock):
    """Test disallowing light groups work."""
    data = deepcopy(DECONZ_WEB_REQUEST)
    data["groups"] = deepcopy(GROUPS)
    data["lights"] = deepcopy(LIGHTS)
    config_entry = await setup_deconz_integration(
       .opp,
        aioclient_mock,
        options={CONF_ALLOW_DECONZ_GROUPS: False},
        get_state_response=data,
    )

    assert len.opp.states.async_all()) == 5
    assert.opp.states.get("light.rgb_light")
    assert.opp.states.get("light.tunable_white_light")
    assert.opp.states.get("light.light_group") is None
    assert.opp.states.get("light.empty_group") is None

   .opp.config_entries.async_update_entry(
        config_entry, options={CONF_ALLOW_DECONZ_GROUPS: True}
    )
    await.opp.async_block_till_done()

    assert len.opp.states.async_all()) == 6
    assert.opp.states.get("light.light_group")

   .opp.config_entries.async_update_entry(
        config_entry, options={CONF_ALLOW_DECONZ_GROUPS: False}
    )
    await.opp.async_block_till_done()

    assert len.opp.states.async_all()) == 5
    assert.opp.states.get("light.light_group") is None


async def test_configuration_tool.opp, aioclient_mock):
    """Test that lights or groups entities are created."""
    data = deepcopy(DECONZ_WEB_REQUEST)
    data["lights"] = {
        "0": {
            "etag": "26839cb118f5bf7ba1f2108256644010",
            "hascolor": False,
            "lastannounced": None,
            "lastseen": "2020-11-22T11:27Z",
            "manufacturername": "dresden elektronik",
            "modelid": "ConBee II",
            "name": "Configuration tool 1",
            "state": {"reachable": True},
            "swversion": "0x264a0700",
            "type": "Configuration tool",
            "uniqueid": "00:21:2e:ff:ff:05:a7:a3-01",
        }
    }
    await setup_deconz_integration.opp, aioclient_mock, get_state_response=data)

    assert len.opp.states.async_all()) == 0


async def test_lidl_christmas_light.opp, aioclient_mock):
    """Test that lights or groups entities are created."""
    data = deepcopy(DECONZ_WEB_REQUEST)
    data["lights"] = {
        "0": {
            "etag": "87a89542bf9b9d0aa8134919056844f8",
            "hascolor": True,
            "lastannounced": None,
            "lastseen": "2020-12-05T22:57Z",
            "manufacturername": "_TZE200_s8gkrkxk",
            "modelid": "TS0601",
            "name": "xmas light",
            "state": {
                "bri": 25,
                "colormode": "hs",
                "effect": "none",
                "hue": 53691,
                "on": True,
                "reachable": True,
                "sat": 141,
            },
            "swversion": None,
            "type": "Color dimmable light",
            "uniqueid": "58:8e:81:ff:fe:db:7b:be-01",
        }
    }
    config_entry = await setup_deconz_integration(
       .opp, aioclient_mock, get_state_response=data
    )

    mock_deconz_put_request(aioclient_mock, config_entry.data, "/lights/0/state")

    await.opp.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: "light.xmas_light",
            ATTR_HS_COLOR: (20, 30),
        },
        blocking=True,
    )
    assert aioclient_mock.mock_calls[1][2] == {"on": True, "hue": 3640, "sat": 76}

    assert.opp.states.get("light.xmas_light")


async def test_non_color_light_reports_color.opp, aioclient_mock):
    """Verify hs_color does not crash when a group gets updated with a bad color value.

    After calling a scene color temp light of certain manufacturers
    report color temp in color space.
    """
    data = deepcopy(DECONZ_WEB_REQUEST)

    data["groups"] = {
        "0": {
            "action": {
                "alert": "none",
                "bri": 127,
                "colormode": "hs",
                "ct": 0,
                "effect": "none",
                "hue": 0,
                "on": True,
                "sat": 127,
                "scene": None,
                "xy": [0, 0],
            },
            "devicemembership": [],
            "etag": "81e42cf1b47affb72fa72bc2e25ba8bf",
            "id": "0",
            "lights": ["0", "1"],
            "name": "All",
            "scenes": [],
            "state": {"all_on": False, "any_on": True},
            "type": "LightGroup",
        }
    }

    data["lights"] = {
        "0": {
            "ctmax": 500,
            "ctmin": 153,
            "etag": "026bcfe544ad76c7534e5ca8ed39047c",
            "hascolor": True,
            "manufacturername": "dresden elektronik",
            "modelid": "FLS-PP3",
            "name": "Light 1",
            "pointsymbol": {},
            "state": {
                "alert": None,
                "bri": 111,
                "colormode": "ct",
                "ct": 307,
                "effect": None,
                "hascolor": True,
                "hue": 7998,
                "on": False,
                "reachable": True,
                "sat": 172,
                "xy": [0.421253, 0.39921],
            },
            "swversion": "020C.201000A0",
            "type": "Extended color light",
            "uniqueid": "00:21:2E:FF:FF:EE:DD:CC-0A",
        },
        "1": {
            "colorcapabilities": 0,
            "ctmax": 65535,
            "ctmin": 0,
            "etag": "9dd510cd474791481f189d2a68a3c7f1",
            "hascolor": True,
            "lastannounced": "2020-12-17T17:44:38Z",
            "lastseen": "2021-01-11T18:36Z",
            "manufacturername": "IKEA of Sweden",
            "modelid": "TRADFRI bulb E27 WS opal 1000lm",
            "name": "Küchenlicht",
            "state": {
                "alert": "none",
                "bri": 156,
                "colormode": "ct",
                "ct": 250,
                "on": True,
                "reachable": True,
            },
            "swversion": "2.0.022",
            "type": "Color temperature light",
            "uniqueid": "ec:1b:bd:ff:fe:ee:ed:dd-01",
        },
    }
    config_entry = await setup_deconz_integration(
       .opp, aioclient_mock, get_state_response=data
    )
    gateway = get_gateway_from_config_entry.opp, config_entry)

    assert len.opp.states.async_all()) == 3
    assert.opp.states.get("light.all").attributes[ATTR_COLOR_TEMP] == 307

    # Updating a scene will return a faulty color value for a non-color light causing an exception in hs_color
    state_changed_event = {
        "e": "changed",
        "id": "1",
        "r": "lights",
        "state": {
            "alert": None,
            "bri": 216,
            "colormode": "xy",
            "ct": 410,
            "on": True,
            "reachable": True,
        },
        "t": "event",
        "uniqueid": "ec:1b:bd:ff:fe:ee:ed:dd-01",
    }
    gateway.api.event_op.dler(state_changed_event)
    await.opp.async_block_till_done()

    # Bug is fixed if we reach this point, but device won't have neither color temp nor color
    with pytest.raises(KeyError):
        assert.opp.states.get("light.all").attributes[ATTR_COLOR_TEMP]
        assert.opp.states.get("light.all").attributes[ATTR_HS_COLOR]


async def test_verify_group_supported_features.opp, aioclient_mock):
    """Test that group supported features reflect what included lights support."""
    data = deepcopy(DECONZ_WEB_REQUEST)
    data["groups"] = deepcopy(
        {
            "1": {
                "id": "Group1",
                "name": "group",
                "type": "LightGroup",
                "state": {"all_on": False, "any_on": True},
                "action": {},
                "scenes": [],
                "lights": ["1", "2", "3"],
            },
        }
    )
    data["lights"] = deepcopy(
        {
            "1": {
                "id": "light1",
                "name": "Dimmable light",
                "state": {"on": True, "bri": 255, "reachable": True},
                "type": "Light",
                "uniqueid": "00:00:00:00:00:00:00:01-00",
            },
            "2": {
                "id": "light2",
                "name": "Color light",
                "state": {
                    "on": True,
                    "bri": 100,
                    "colormode": "xy",
                    "effect": "colorloop",
                    "xy": (500, 500),
                    "reachable": True,
                },
                "type": "Extended color light",
                "uniqueid": "00:00:00:00:00:00:00:02-00",
            },
            "3": {
                "ctmax": 454,
                "ctmin": 155,
                "id": "light3",
                "name": "Tunable light",
                "state": {"on": True, "colormode": "ct", "ct": 2500, "reachable": True},
                "type": "Tunable white light",
                "uniqueid": "00:00:00:00:00:00:00:03-00",
            },
        }
    )
    await setup_deconz_integration.opp, aioclient_mock, get_state_response=data)

    assert len.opp.states.async_all()) == 4

    group = opp.states.get("light.group")
    assert group.state == STATE_ON
    assert group.attributes[ATTR_SUPPORTED_FEATURES] == 63
