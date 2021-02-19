"""Tests for Vizio config flow."""
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import call, patch

import pytest
from pytest import raises
from pyvizio.api.apps import AppConfig
from pyvizio.const import (
    APPS,
    DEVICE_CLASS_SPEAKER as VIZIO_DEVICE_CLASS_SPEAKER,
    DEVICE_CLASS_TV as VIZIO_DEVICE_CLASS_TV,
    INPUT_APPS,
    MAX_VOLUME,
    UNKNOWN_APP,
)
import voluptuous as vol

from openpeerpower.components.media_player import (
    ATTR_INPUT_SOURCE,
    ATTR_MEDIA_VOLUME_LEVEL,
    ATTR_MEDIA_VOLUME_MUTED,
    ATTR_SOUND_MODE,
    DEVICE_CLASS_SPEAKER,
    DEVICE_CLASS_TV,
    DOMAIN as MP_DOMAIN,
    SERVICE_MEDIA_NEXT_TRACK,
    SERVICE_MEDIA_PREVIOUS_TRACK,
    SERVICE_SELECT_SOUND_MODE,
    SERVICE_SELECT_SOURCE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    SERVICE_VOLUME_DOWN,
    SERVICE_VOLUME_MUTE,
    SERVICE_VOLUME_SET,
    SERVICE_VOLUME_UP,
)
from openpeerpower.components.vizio import validate_apps
from openpeerpower.components.vizio.const import (
    CONF_ADDITIONAL_CONFIGS,
    CONF_APPS,
    CONF_VOLUME_STEP,
    DEFAULT_VOLUME_STEP,
    DOMAIN,
    SERVICE_UPDATE_SETTING,
    VIZIO_SCHEMA,
)
from openpeerpower.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from openpeerpowerr.helpers.typing import OpenPeerPowerType
from openpeerpowerr.util import dt as dt_util

from .const import (
    ADDITIONAL_APP_CONFIG,
    APP_LIST,
    APP_NAME_LIST,
    CURRENT_APP,
    CURRENT_APP_CONFIG,
    CURRENT_EQ,
    CURRENT_INPUT,
    CUSTOM_CONFIG,
    ENTITY_ID,
    EQ_LIST,
    INPUT_LIST,
    INPUT_LIST_WITH_APPS,
    MOCK_SPEAKER_APPS_FAILURE,
    MOCK_SPEAKER_CONFIG,
    MOCK_TV_APPS_FAILURE,
    MOCK_TV_WITH_ADDITIONAL_APPS_CONFIG,
    MOCK_TV_WITH_EXCLUDE_CONFIG,
    MOCK_TV_WITH_INCLUDE_CONFIG,
    MOCK_USER_VALID_TV_CONFIG,
    NAME,
    UNIQUE_ID,
    UNKNOWN_APP_CONFIG,
    VOLUME_STEP,
)

from tests.common import MockConfigEntry, async_fire_time_changed


async def _add_config_entry_to_opp(
   .opp: OpenPeerPowerType, config_entry: MockConfigEntry
) -> None:
    config_entry.add_to_opp.opp)
    assert await.opp.config_entries.async_setup(config_entry.entry_id)
    await.opp.async_block_till_done()


def _get_op.power_state(vizio_power_state: Optional[bool]) -> str:
    """Return HA power state given Vizio power state."""
    if vizio_power_state:
        return STATE_ON

    if vizio_power_state is False:
        return STATE_OFF

    return STATE_UNAVAILABLE


def _assert_sources_and_volume(attr: Dict[str, Any], vizio_device_class: str) -> None:
    """Assert source list, source, and volume level based on attr dict and device class."""
    assert attr["source_list"] == INPUT_LIST
    assert attr["source"] == CURRENT_INPUT
    assert (
        attr["volume_level"]
        == float(int(MAX_VOLUME[vizio_device_class] / 2))
        / MAX_VOLUME[vizio_device_class]
    )


def _get_attr_and_assert_base_attr(
   .opp: OpenPeerPowerType, device_class: str, power_state: str
) -> Dict[str, Any]:
    """Return entity attributes  after asserting name, device class, and power state."""
    attr =.opp.states.get(ENTITY_ID).attributes
    assert attr["friendly_name"] == NAME
    assert attr["device_class"] == device_class

    assert.opp.states.get(ENTITY_ID).state == power_state
    return attr


@asynccontextmanager
async def _cm_for_test_setup_without_apps(
    all_settings: Dict[str, Any], vizio_power_state: Optional[bool]
) -> None:
    """Context manager to setup test for Vizio devices without including app specific patches."""
    with patch(
        "openpeerpower.components.vizio.media_player.VizioAsync.get_all_settings",
        return_value=all_settings,
    ), patch(
        "openpeerpower.components.vizio.media_player.VizioAsync.get_setting_options",
        return_value=EQ_LIST,
    ), patch(
        "openpeerpower.components.vizio.media_player.VizioAsync.get_power_state",
        return_value=vizio_power_state,
    ):
        yield


async def _test_setup_tv(
   .opp: OpenPeerPowerType, vizio_power_state: Optional[bool]
) -> None:
    """Test Vizio TV entity setup."""
    ha_power_state = _get_op.power_state(vizio_power_state)

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=vol.Schema(VIZIO_SCHEMA)(MOCK_USER_VALID_TV_CONFIG),
        unique_id=UNIQUE_ID,
    )

    async with _cm_for_test_setup_without_apps(
        {"volume": int(MAX_VOLUME[VIZIO_DEVICE_CLASS_TV] / 2), "mute": "Off"},
        vizio_power_state,
    ):
        await _add_config_entry_to_opp.opp, config_entry)

        attr = _get_attr_and_assert_base_attr.opp, DEVICE_CLASS_TV, ha_power_state)
        if ha_power_state == STATE_ON:
            _assert_sources_and_volume(attr, VIZIO_DEVICE_CLASS_TV)
            assert "sound_mode" not in attr


async def _test_setup_speaker(
   .opp: OpenPeerPowerType, vizio_power_state: Optional[bool]
) -> None:
    """Test Vizio Speaker entity setup."""
    ha_power_state = _get_op.power_state(vizio_power_state)

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=vol.Schema(VIZIO_SCHEMA)(MOCK_SPEAKER_CONFIG),
        unique_id=UNIQUE_ID,
    )

    audio_settings = {
        "volume": int(MAX_VOLUME[VIZIO_DEVICE_CLASS_SPEAKER] / 2),
        "mute": "Off",
        "eq": CURRENT_EQ,
    }

    async with _cm_for_test_setup_without_apps(
        audio_settings,
        vizio_power_state,
    ):
        with patch(
            "openpeerpower.components.vizio.media_player.VizioAsync.get_current_app_config",
        ) as service_call:
            await _add_config_entry_to_opp.opp, config_entry)

            attr = _get_attr_and_assert_base_attr(
               .opp, DEVICE_CLASS_SPEAKER, ha_power_state
            )
            if ha_power_state == STATE_ON:
                _assert_sources_and_volume(attr, VIZIO_DEVICE_CLASS_SPEAKER)
                assert not service_call.called
                assert "sound_mode" in attr


@asynccontextmanager
async def _cm_for_test_setup_tv_with_apps(
   .opp: OpenPeerPowerType, device_config: Dict[str, Any], app_config: Dict[str, Any]
) -> None:
    """Context manager to setup test for Vizio TV with support for apps."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=vol.Schema(VIZIO_SCHEMA)(device_config), unique_id=UNIQUE_ID
    )

    async with _cm_for_test_setup_without_apps(
        {"volume": int(MAX_VOLUME[VIZIO_DEVICE_CLASS_TV] / 2), "mute": "Off"},
        True,
    ):
        with patch(
            "openpeerpower.components.vizio.media_player.VizioAsync.get_current_app_config",
            return_value=AppConfig(**app_config),
        ):
            await _add_config_entry_to_opp.opp, config_entry)

            attr = _get_attr_and_assert_base_attr.opp, DEVICE_CLASS_TV, STATE_ON)
            assert (
                attr["volume_level"]
                == float(int(MAX_VOLUME[VIZIO_DEVICE_CLASS_TV] / 2))
                / MAX_VOLUME[VIZIO_DEVICE_CLASS_TV]
            )

            yield


def _assert_source_list_with_apps(
    list_to_test: List[str], attr: Dict[str, Any]
) -> None:
    """Assert source list matches list_to_test after removing INPUT_APPS from list."""
    for app_to_remove in INPUT_APPS:
        if app_to_remove in list_to_test:
            list_to_test.remove(app_to_remove)

    assert attr["source_list"] == list_to_test


async def _test_setup_failure.opp: OpenPeerPowerType, config: str) -> None:
    """Test generic Vizio entity setup failure."""
    with patch(
        "openpeerpower.components.vizio.media_player.VizioAsync.can_connect_with_auth_check",
        return_value=False,
    ):
        config_entry = MockConfigEntry(domain=DOMAIN, data=config, unique_id=UNIQUE_ID)
        await _add_config_entry_to_opp.opp, config_entry)
        assert len.opp.states.async_entity_ids(MP_DOMAIN)) == 0


async def _test_service(
   .opp: OpenPeerPowerType,
    domain: str,
    vizio_func_name: str,
    ha_service_name: str,
    additional_service_data: Optional[Dict[str, Any]],
    *args,
    **kwargs,
) -> None:
    """Test generic Vizio media player entity service."""
    kwargs["log_api_exception"] = False
    service_data = {ATTR_ENTITY_ID: ENTITY_ID}
    if additional_service_data:
        service_data.update(additional_service_data)

    with patch(
        f"openpeerpower.components.vizio.media_player.VizioAsync.{vizio_func_name}"
    ) as service_call:
        await.opp.services.async_call(
            domain,
            ha_service_name,
            service_data=service_data,
            blocking=True,
        )
        assert service_call.called

        if args or kwargs:
            assert service_call.call_args == call(*args, **kwargs)


async def test_speaker_on(
   .opp: OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_update: pytest.fixture,
) -> None:
    """Test Vizio Speaker entity setup when on."""
    await _test_setup_speaker.opp, True)


async def test_speaker_off(
   .opp: OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_update: pytest.fixture,
) -> None:
    """Test Vizio Speaker entity setup when off."""
    await _test_setup_speaker.opp, False)


async def test_speaker_unavailable(
   .opp: OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_update: pytest.fixture,
) -> None:
    """Test Vizio Speaker entity setup when unavailable."""
    await _test_setup_speaker.opp, None)


async def test_init_tv_on(
   .opp: OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_update: pytest.fixture,
) -> None:
    """Test Vizio TV entity setup when on."""
    await _test_setup_tv.opp, True)


async def test_init_tv_off(
   .opp: OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_update: pytest.fixture,
) -> None:
    """Test Vizio TV entity setup when off."""
    await _test_setup_tv.opp, False)


async def test_init_tv_unavailable(
   .opp: OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_update: pytest.fixture,
) -> None:
    """Test Vizio TV entity setup when unavailable."""
    await _test_setup_tv.opp, None)


async def test_setup_failure_speaker(
   .opp: OpenPeerPowerType, vizio_connect: pytest.fixture
) -> None:
    """Test speaker entity setup failure."""
    await _test_setup_failure.opp, MOCK_SPEAKER_CONFIG)


async def test_setup_failure_tv(
   .opp: OpenPeerPowerType, vizio_connect: pytest.fixture
) -> None:
    """Test TV entity setup failure."""
    await _test_setup_failure.opp, MOCK_USER_VALID_TV_CONFIG)


async def test_services(
   .opp: OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_update: pytest.fixture,
) -> None:
    """Test all Vizio media player entity services."""
    await _test_setup_tv.opp, True)

    await _test_service.opp, MP_DOMAIN, "pow_on", SERVICE_TURN_ON, None)
    await _test_service.opp, MP_DOMAIN, "pow_off", SERVICE_TURN_OFF, None)
    await _test_service(
       .opp,
        MP_DOMAIN,
        "mute_on",
        SERVICE_VOLUME_MUTE,
        {ATTR_MEDIA_VOLUME_MUTED: True},
    )
    await _test_service(
       .opp,
        MP_DOMAIN,
        "mute_off",
        SERVICE_VOLUME_MUTE,
        {ATTR_MEDIA_VOLUME_MUTED: False},
    )
    await _test_service(
       .opp,
        MP_DOMAIN,
        "set_input",
        SERVICE_SELECT_SOURCE,
        {ATTR_INPUT_SOURCE: "USB"},
        "USB",
    )
    await _test_service(
       .opp, MP_DOMAIN, "vol_up", SERVICE_VOLUME_UP, None, num=DEFAULT_VOLUME_STEP
    )
    await _test_service(
       .opp, MP_DOMAIN, "vol_down", SERVICE_VOLUME_DOWN, None, num=DEFAULT_VOLUME_STEP
    )
    await _test_service(
       .opp,
        MP_DOMAIN,
        "vol_up",
        SERVICE_VOLUME_SET,
        {ATTR_MEDIA_VOLUME_LEVEL: 1},
        num=(100 - 15),
    )
    await _test_service(
       .opp,
        MP_DOMAIN,
        "vol_down",
        SERVICE_VOLUME_SET,
        {ATTR_MEDIA_VOLUME_LEVEL: 0},
        num=(15 - 0),
    )
    await _test_service.opp, MP_DOMAIN, "ch_up", SERVICE_MEDIA_NEXT_TRACK, None)
    await _test_service.opp, MP_DOMAIN, "ch_down", SERVICE_MEDIA_PREVIOUS_TRACK, None)
    await _test_service(
       .opp,
        MP_DOMAIN,
        "set_setting",
        SERVICE_SELECT_SOUND_MODE,
        {ATTR_SOUND_MODE: "Music"},
        "audio",
        "eq",
        "Music",
    )
    # Test that the update_setting service does config validation/transformation correctly
    await _test_service(
       .opp,
        DOMAIN,
        "set_setting",
        SERVICE_UPDATE_SETTING,
        {"setting_type": "Audio", "setting_name": "AV Delay", "new_value": "0"},
        "audio",
        "av_delay",
        0,
    )
    await _test_service(
       .opp,
        DOMAIN,
        "set_setting",
        SERVICE_UPDATE_SETTING,
        {"setting_type": "Audio", "setting_name": "EQ", "new_value": "Music"},
        "audio",
        "eq",
        "Music",
    )


async def test_options_update(
   .opp: OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_update: pytest.fixture,
) -> None:
    """Test when config entry update event fires."""
    await _test_setup_speaker.opp, True)
    config_entry =.opp.config_entries.async_entries(DOMAIN)[0]
    assert config_entry.options
    new_options = config_entry.options.copy()
    updated_options = {CONF_VOLUME_STEP: VOLUME_STEP}
    new_options.update(updated_options)
   .opp.config_entries.async_update_entry(
        entry=config_entry,
        options=new_options,
    )
    assert config_entry.options == updated_options
    await _test_service(
       .opp, MP_DOMAIN, "vol_up", SERVICE_VOLUME_UP, None, num=VOLUME_STEP
    )


async def _test_update_availability_switch(
   .opp: OpenPeerPowerType,
    initial_power_state: Optional[bool],
    final_power_state: Optional[bool],
    caplog: pytest.fixture,
) -> None:
    now = dt_util.utcnow()
    future_interval = timedelta(minutes=1)

    # Setup device as if time is right now
    with patch("openpeerpowerr.util.dt.utcnow", return_value=now):
        await _test_setup_speaker.opp, initial_power_state)

    # Clear captured logs so that only availability state changes are captured for
    # future assertion
    caplog.clear()

    # Fast forward time to future twice to trigger update and assert vizio log message
    for i in range(1, 3):
        future = now + (future_interval * i)
        with patch(
            "openpeerpower.components.vizio.media_player.VizioAsync.get_power_state",
            return_value=final_power_state,
        ), patch("openpeerpowerr.util.dt.utcnow", return_value=future), patch(
            "openpeerpowerr.util.utcnow", return_value=future
        ):
            async_fire_time_changed.opp, future)
            await.opp.async_block_till_done()
            if final_power_state is None:
                assert.opp.states.get(ENTITY_ID).state == STATE_UNAVAILABLE
            else:
                assert.opp.states.get(ENTITY_ID).state != STATE_UNAVAILABLE

    # Ensure connection status messages from vizio.media_player appear exactly once
    # (on availability state change)
    vizio_log_list = [
        log
        for log in caplog.records
        if log.name == "openpeerpower.components.vizio.media_player"
    ]
    assert len(vizio_log_list) == 1


async def test_update_unavailable_to_available(
   .opp: OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_update: pytest.fixture,
    caplog: pytest.fixture,
) -> None:
    """Test device becomes available after being unavailable."""
    await _test_update_availability_switch.opp, None, True, caplog)


async def test_update_available_to_unavailable(
   .opp: OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_update: pytest.fixture,
    caplog: pytest.fixture,
) -> None:
    """Test device becomes unavailable after being available."""
    await _test_update_availability_switch.opp, True, None, caplog)


async def test_setup_with_apps(
   .opp: OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_update_with_apps: pytest.fixture,
    caplog: pytest.fixture,
) -> None:
    """Test device setup with apps."""
    async with _cm_for_test_setup_tv_with_apps(
       .opp, MOCK_USER_VALID_TV_CONFIG, CURRENT_APP_CONFIG
    ):
        attr =.opp.states.get(ENTITY_ID).attributes
        _assert_source_list_with_apps(list(INPUT_LIST_WITH_APPS + APP_NAME_LIST), attr)
        assert CURRENT_APP in attr["source_list"]
        assert attr["source"] == CURRENT_APP
        assert attr["app_name"] == CURRENT_APP
        assert "app_id" not in attr

    await _test_service(
       .opp,
        MP_DOMAIN,
        "launch_app",
        SERVICE_SELECT_SOURCE,
        {ATTR_INPUT_SOURCE: CURRENT_APP},
        CURRENT_APP,
        APP_LIST,
    )


async def test_setup_with_apps_include(
   .opp: OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_update_with_apps: pytest.fixture,
    caplog: pytest.fixture,
) -> None:
    """Test device setup with apps and apps["include"] in config."""
    async with _cm_for_test_setup_tv_with_apps(
       .opp, MOCK_TV_WITH_INCLUDE_CONFIG, CURRENT_APP_CONFIG
    ):
        attr =.opp.states.get(ENTITY_ID).attributes
        _assert_source_list_with_apps(list(INPUT_LIST_WITH_APPS + [CURRENT_APP]), attr)
        assert CURRENT_APP in attr["source_list"]
        assert attr["source"] == CURRENT_APP
        assert attr["app_name"] == CURRENT_APP
        assert "app_id" not in attr


async def test_setup_with_apps_exclude(
   .opp: OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_update_with_apps: pytest.fixture,
    caplog: pytest.fixture,
) -> None:
    """Test device setup with apps and apps["exclude"] in config."""
    async with _cm_for_test_setup_tv_with_apps(
       .opp, MOCK_TV_WITH_EXCLUDE_CONFIG, CURRENT_APP_CONFIG
    ):
        attr =.opp.states.get(ENTITY_ID).attributes
        _assert_source_list_with_apps(list(INPUT_LIST_WITH_APPS + [CURRENT_APP]), attr)
        assert CURRENT_APP in attr["source_list"]
        assert attr["source"] == CURRENT_APP
        assert attr["app_name"] == CURRENT_APP
        assert "app_id" not in attr


async def test_setup_with_apps_additional_apps_config(
   .opp: OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_update_with_apps: pytest.fixture,
    caplog: pytest.fixture,
) -> None:
    """Test device setup with apps and apps["additional_configs"] in config."""
    async with _cm_for_test_setup_tv_with_apps(
       .opp,
        MOCK_TV_WITH_ADDITIONAL_APPS_CONFIG,
        ADDITIONAL_APP_CONFIG["config"],
    ):
        attr =.opp.states.get(ENTITY_ID).attributes
        assert attr["source_list"].count(CURRENT_APP) == 1
        _assert_source_list_with_apps(
            list(
                INPUT_LIST_WITH_APPS
                + APP_NAME_LIST
                + [
                    app["name"]
                    for app in MOCK_TV_WITH_ADDITIONAL_APPS_CONFIG[CONF_APPS][
                        CONF_ADDITIONAL_CONFIGS
                    ]
                    if app["name"] not in APP_NAME_LIST
                ]
            ),
            attr,
        )
        assert ADDITIONAL_APP_CONFIG["name"] in attr["source_list"]
        assert attr["source"] == ADDITIONAL_APP_CONFIG["name"]
        assert attr["app_name"] == ADDITIONAL_APP_CONFIG["name"]
        assert "app_id" not in attr

    await _test_service(
       .opp,
        MP_DOMAIN,
        "launch_app",
        SERVICE_SELECT_SOURCE,
        {ATTR_INPUT_SOURCE: "Netflix"},
        "Netflix",
        APP_LIST,
    )
    await _test_service(
       .opp,
        MP_DOMAIN,
        "launch_app_config",
        SERVICE_SELECT_SOURCE,
        {ATTR_INPUT_SOURCE: CURRENT_APP},
        **CUSTOM_CONFIG,
    )

    # Test that invalid app does nothing
    with patch(
        "openpeerpower.components.vizio.media_player.VizioAsync.launch_app"
    ) as service_call1, patch(
        "openpeerpower.components.vizio.media_player.VizioAsync.launch_app_config"
    ) as service_call2:
        await.opp.services.async_call(
            MP_DOMAIN,
            SERVICE_SELECT_SOURCE,
            service_data={ATTR_ENTITY_ID: ENTITY_ID, ATTR_INPUT_SOURCE: "_"},
            blocking=True,
        )
        assert not service_call1.called
        assert not service_call2.called


def test_invalid_apps_config.opp: OpenPeerPowerType):
    """Test that schema validation fails on certain conditions."""
    with raises(vol.Invalid):
        vol.Schema(vol.All(VIZIO_SCHEMA, validate_apps))(MOCK_TV_APPS_FAILURE)

    with raises(vol.Invalid):
        vol.Schema(vol.All(VIZIO_SCHEMA, validate_apps))(MOCK_SPEAKER_APPS_FAILURE)


async def test_setup_with_unknown_app_config(
   .opp: OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_update_with_apps: pytest.fixture,
    caplog: pytest.fixture,
) -> None:
    """Test device setup with apps where app config returned is unknown."""
    async with _cm_for_test_setup_tv_with_apps(
       .opp, MOCK_USER_VALID_TV_CONFIG, UNKNOWN_APP_CONFIG
    ):
        attr =.opp.states.get(ENTITY_ID).attributes
        _assert_source_list_with_apps(list(INPUT_LIST_WITH_APPS + APP_NAME_LIST), attr)
        assert attr["source"] == UNKNOWN_APP
        assert attr["app_name"] == UNKNOWN_APP
        assert attr["app_id"] == UNKNOWN_APP_CONFIG


async def test_setup_with_no_running_app(
   .opp: OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_update_with_apps: pytest.fixture,
    caplog: pytest.fixture,
) -> None:
    """Test device setup with apps where no app is running."""
    async with _cm_for_test_setup_tv_with_apps(
       .opp, MOCK_USER_VALID_TV_CONFIG, vars(AppConfig())
    ):
        attr =.opp.states.get(ENTITY_ID).attributes
        _assert_source_list_with_apps(list(INPUT_LIST_WITH_APPS + APP_NAME_LIST), attr)
        assert attr["source"] == "CAST"
        assert "app_id" not in attr
        assert "app_name" not in attr


async def test_setup_tv_without_mute(
   .opp: OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_update: pytest.fixture,
) -> None:
    """Test Vizio TV entity setup when mute property isn't returned by Vizio API."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=vol.Schema(VIZIO_SCHEMA)(MOCK_USER_VALID_TV_CONFIG),
        unique_id=UNIQUE_ID,
    )

    async with _cm_for_test_setup_without_apps(
        {"volume": int(MAX_VOLUME[VIZIO_DEVICE_CLASS_TV] / 2)},
        STATE_ON,
    ):
        await _add_config_entry_to_opp.opp, config_entry)

        attr = _get_attr_and_assert_base_attr.opp, DEVICE_CLASS_TV, STATE_ON)
        _assert_sources_and_volume(attr, VIZIO_DEVICE_CLASS_TV)
        assert "sound_mode" not in attr
        assert "is_volume_muted" not in attr


async def test_apps_update(
   .opp: OpenPeerPowerType,
    vizio_connect: pytest.fixture,
    vizio_update_with_apps: pytest.fixture,
    caplog: pytest.fixture,
) -> None:
    """Test device setup with apps where no app is running."""
    with patch(
        "openpeerpower.components.vizio.gen_apps_list_from_url",
        return_value=None,
    ):
        async with _cm_for_test_setup_tv_with_apps(
           .opp, MOCK_USER_VALID_TV_CONFIG, vars(AppConfig())
        ):
            # Check source list, remove TV inputs, and verify that the integration is
            # using the default APPS list
            sources =.opp.states.get(ENTITY_ID).attributes["source_list"]
            apps = list(set(sources) - set(INPUT_LIST))
            assert len(apps) == len(APPS)

            with patch(
                "openpeerpower.components.vizio.gen_apps_list_from_url",
                return_value=APP_LIST,
            ):
                async_fire_time_changed.opp, dt_util.now() + timedelta(days=2))
                await.opp.async_block_till_done()
                # Check source list, remove TV inputs, and verify that the integration is
                # now using the APP_LIST list
                sources =.opp.states.get(ENTITY_ID).attributes["source_list"]
                apps = list(set(sources) - set(INPUT_LIST))
                assert len(apps) == len(APP_LIST)
