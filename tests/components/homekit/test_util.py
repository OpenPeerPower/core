"""Test HomeKit util module."""
import pytest
import voluptuous as vol

from openpeerpower.components.homekit.const import (
    BRIDGE_NAME,
    CONF_FEATURE,
    CONF_FEATURE_LIST,
    CONF_LINKED_BATTERY_SENSOR,
    CONF_LOW_BATTERY_THRESHOLD,
    DEFAULT_CONFIG_FLOW_PORT,
    DOMAIN,
    FEATURE_ON_OFF,
    FEATURE_PLAY_PAUSE,
    HOMEKIT_PAIRING_QR,
    HOMEKIT_PAIRING_QR_SECRET,
    TYPE_FAUCET,
    TYPE_OUTLET,
    TYPE_SHOWER,
    TYPE_SPRINKLER,
    TYPE_SWITCH,
    TYPE_VALVE,
)
from openpeerpower.components.homekit.util import (
    async_find_next_available_port,
    cleanup_name_for_homekit,
    convert_to_float,
    density_to_air_quality,
    dismiss_setup_message,
    format_sw_version,
    port_is_available,
    show_setup_message,
    temperature_to_homekit,
    temperature_to_states,
    validate_entity_config as vec,
    validate_media_player_features,
)
from openpeerpower.components.persistent_notification import (
    ATTR_MESSAGE,
    ATTR_NOTIFICATION_ID,
    DOMAIN as PERSISTENT_NOTIFICATION_DOMAIN,
)
from openpeerpower.const import (
    ATTR_CODE,
    ATTR_SUPPORTED_FEATURES,
    CONF_NAME,
    CONF_PORT,
    CONF_TYPE,
    STATE_UNKNOWN,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
from openpeerpower.core import State

from .util import async_init_integration

from tests.common import MockConfigEntry, async_mock_service


def test_validate_entity_config():
    """Test validate entities."""
    configs = [
        None,
        [],
        "string",
        12345,
        {"invalid_entity_id": {}},
        {"demo.test": 1},
        {"binary_sensor.demo": {CONF_LINKED_BATTERY_SENSOR: None}},
        {"binary_sensor.demo": {CONF_LINKED_BATTERY_SENSOR: "switch.demo"}},
        {"binary_sensor.demo": {CONF_LOW_BATTERY_THRESHOLD: "switch.demo"}},
        {"binary_sensor.demo": {CONF_LOW_BATTERY_THRESHOLD: -10}},
        {"demo.test": "test"},
        {"demo.test": [1, 2]},
        {"demo.test": None},
        {"demo.test": {CONF_NAME: None}},
        {"media_player.test": {CONF_FEATURE_LIST: [{CONF_FEATURE: "invalid_feature"}]}},
        {
            "media_player.test": {
                CONF_FEATURE_LIST: [
                    {CONF_FEATURE: FEATURE_ON_OFF},
                    {CONF_FEATURE: FEATURE_ON_OFF},
                ]
            }
        },
        {"switch.test": {CONF_TYPE: "invalid_type"}},
    ]

    for conf in configs:
        with pytest.raises(vol.Invalid):
            vec(conf)

    assert vec({}) == {}
    assert vec({"demo.test": {CONF_NAME: "Name"}}) == {
        "demo.test": {CONF_NAME: "Name", CONF_LOW_BATTERY_THRESHOLD: 20}
    }

    assert vec(
        {"binary_sensor.demo": {CONF_LINKED_BATTERY_SENSOR: "sensor.demo_battery"}}
    ) == {
        "binary_sensor.demo": {
            CONF_LINKED_BATTERY_SENSOR: "sensor.demo_battery",
            CONF_LOW_BATTERY_THRESHOLD: 20,
        }
    }
    assert vec({"binary_sensor.demo": {CONF_LOW_BATTERY_THRESHOLD: 50}}) == {
        "binary_sensor.demo": {CONF_LOW_BATTERY_THRESHOLD: 50}
    }

    assert vec({"alarm_control_panel.demo": {}}) == {
        "alarm_control_panel.demo": {ATTR_CODE: None, CONF_LOW_BATTERY_THRESHOLD: 20}
    }
    assert vec({"alarm_control_panel.demo": {ATTR_CODE: "1234"}}) == {
        "alarm_control_panel.demo": {ATTR_CODE: "1234", CONF_LOW_BATTERY_THRESHOLD: 20}
    }

    assert vec({"lock.demo": {}}) == {
        "lock.demo": {ATTR_CODE: None, CONF_LOW_BATTERY_THRESHOLD: 20}
    }
    assert vec({"lock.demo": {ATTR_CODE: "1234"}}) == {
        "lock.demo": {ATTR_CODE: "1234", CONF_LOW_BATTERY_THRESHOLD: 20}
    }

    assert vec({"media_player.demo": {}}) == {
        "media_player.demo": {CONF_FEATURE_LIST: {}, CONF_LOW_BATTERY_THRESHOLD: 20}
    }
    config = {
        CONF_FEATURE_LIST: [
            {CONF_FEATURE: FEATURE_ON_OFF},
            {CONF_FEATURE: FEATURE_PLAY_PAUSE},
        ]
    }
    assert vec({"media_player.demo": config}) == {
        "media_player.demo": {
            CONF_FEATURE_LIST: {FEATURE_ON_OFF: {}, FEATURE_PLAY_PAUSE: {}},
            CONF_LOW_BATTERY_THRESHOLD: 20,
        }
    }

    assert vec({"switch.demo": {CONF_TYPE: TYPE_FAUCET}}) == {
        "switch.demo": {CONF_TYPE: TYPE_FAUCET, CONF_LOW_BATTERY_THRESHOLD: 20}
    }
    assert vec({"switch.demo": {CONF_TYPE: TYPE_OUTLET}}) == {
        "switch.demo": {CONF_TYPE: TYPE_OUTLET, CONF_LOW_BATTERY_THRESHOLD: 20}
    }
    assert vec({"switch.demo": {CONF_TYPE: TYPE_SHOWER}}) == {
        "switch.demo": {CONF_TYPE: TYPE_SHOWER, CONF_LOW_BATTERY_THRESHOLD: 20}
    }
    assert vec({"switch.demo": {CONF_TYPE: TYPE_SPRINKLER}}) == {
        "switch.demo": {CONF_TYPE: TYPE_SPRINKLER, CONF_LOW_BATTERY_THRESHOLD: 20}
    }
    assert vec({"switch.demo": {CONF_TYPE: TYPE_SWITCH}}) == {
        "switch.demo": {CONF_TYPE: TYPE_SWITCH, CONF_LOW_BATTERY_THRESHOLD: 20}
    }
    assert vec({"switch.demo": {CONF_TYPE: TYPE_VALVE}}) == {
        "switch.demo": {CONF_TYPE: TYPE_VALVE, CONF_LOW_BATTERY_THRESHOLD: 20}
    }


def test_validate_media_player_features():
    """Test validate modes for media players."""
    config = {}
    attrs = {ATTR_SUPPORTED_FEATURES: 20873}
    entity_state = State("media_player.demo", "on", attrs)
    assert validate_media_player_features(entity_state, config) is True

    config = {FEATURE_ON_OFF: None}
    assert validate_media_player_features(entity_state, config) is True

    entity_state = State("media_player.demo", "on")
    assert validate_media_player_features(entity_state, config) is False


def test_convert_to_float():
    """Test convert_to_float method."""
    assert convert_to_float(12) == 12
    assert convert_to_float(12.4) == 12.4
    assert convert_to_float(STATE_UNKNOWN) is None
    assert convert_to_float(None) is None


def test_cleanup_name_for_homekit():
    """Ensure name sanitize works as expected."""

    assert cleanup_name_for_homekit("abc") == "abc"
    assert cleanup_name_for_homekit("a b c") == "a b c"
    assert cleanup_name_for_homekit("ab_c") == "ab c"
    assert (
        cleanup_name_for_homekit('ab!@#$%^&*()-=":.,><?//\\ frog')
        == "ab--#---&----- -.,------ frog"
    )
    assert cleanup_name_for_homekit("の日本_語文字セット") == "の日本 語文字セット"


def test_temperature_to_homekit():
    """Test temperature conversion from HA to HomeKit."""
    assert temperature_to_homekit(20.46, TEMP_CELSIUS) == 20.5
    assert temperature_to_homekit(92.1, TEMP_FAHRENHEIT) == 33.4


def test_temperature_to_states():
    """Test temperature conversion from HomeKit to HA."""
    assert temperature_to_states(20, TEMP_CELSIUS) == 20.0
    assert temperature_to_states(20.2, TEMP_FAHRENHEIT) == 68.5


def test_density_to_air_quality():
    """Test map PM2.5 density to HomeKit AirQuality level."""
    assert density_to_air_quality(0) == 1
    assert density_to_air_quality(35) == 1
    assert density_to_air_quality(35.1) == 2
    assert density_to_air_quality(75) == 2
    assert density_to_air_quality(115) == 3
    assert density_to_air_quality(150) == 4
    assert density_to_air_quality(300) == 5


async def test_show_setup_msg.opp, hk_driver):
    """Test show setup message as persistence notification."""
    pincode = b"123-45-678"

    entry = await async_init_integration.opp)
    assert entry

    call_create_notification = async_mock_service(
        opp, PERSISTENT_NOTIFICATION_DOMAIN, "create"
    )

    await opp.async_add_executor_job(
        show_setup_message, opp, entry.entry_id, "bridge_name", pincode, "X-HM://0"
    )
    await opp.async_block_till_done()
    assert.opp.data[DOMAIN][entry.entry_id][HOMEKIT_PAIRING_QR_SECRET]
    assert.opp.data[DOMAIN][entry.entry_id][HOMEKIT_PAIRING_QR]

    assert call_create_notification
    assert call_create_notification[0].data[ATTR_NOTIFICATION_ID] == entry.entry_id
    assert pincode.decode() in call_create_notification[0].data[ATTR_MESSAGE]


async def test_dismiss_setup_msg.opp):
    """Test dismiss setup message."""
    call_dismiss_notification = async_mock_service(
        opp, PERSISTENT_NOTIFICATION_DOMAIN, "dismiss"
    )

    await opp.async_add_executor_job(dismiss_setup_message, opp, "entry_id")
    await opp.async_block_till_done()

    assert call_dismiss_notification
    assert call_dismiss_notification[0].data[ATTR_NOTIFICATION_ID] == "entry_id"


async def test_port_is_available.opp):
    """Test we can get an available port and it is actually available."""
    next_port = await async_find_next_available_port.opp, DEFAULT_CONFIG_FLOW_PORT)

    assert next_port

    assert await opp.async_add_executor_job(port_is_available, next_port)


async def test_port_is_available_skips_existing_entries.opp):
    """Test we can get an available port and it is actually available."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_NAME: BRIDGE_NAME, CONF_PORT: DEFAULT_CONFIG_FLOW_PORT},
        options={},
    )
    entry.add_to.opp.opp)

    next_port = await async_find_next_available_port.opp, DEFAULT_CONFIG_FLOW_PORT)

    assert next_port
    assert next_port != DEFAULT_CONFIG_FLOW_PORT

    assert await opp.async_add_executor_job(port_is_available, next_port)


async def test_format_sw_version():
    """Test format_sw_version method."""
    assert format_sw_version("soho+3.6.8+soho-release-rt120+10") == "3.6.8"
    assert format_sw_version("undefined-undefined-1.6.8") == "1.6.8"
    assert format_sw_version("56.0-76060") == "56.0.76060"
    assert format_sw_version(3.6) == "3.6"
    assert format_sw_version("unknown") is None
