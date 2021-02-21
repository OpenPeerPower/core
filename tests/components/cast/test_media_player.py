"""The tests for the Cast Media player platform."""
# pylint: disable=protected-access
import json
from typing import Optional
from unittest.mock import ANY, AsyncMock, MagicMock, Mock, patch
from uuid import UUID

import attr
import pytest

from openpeerpower.components import tts
from openpeerpower.components.cast import media_player as cast
from openpeerpower.components.cast.media_player import ChromecastInfo
from openpeerpower.components.media_player.const import (
    SUPPORT_NEXT_TRACK,
    SUPPORT_PAUSE,
    SUPPORT_PLAY,
    SUPPORT_PLAY_MEDIA,
    SUPPORT_PREVIOUS_TRACK,
    SUPPORT_SEEK,
    SUPPORT_STOP,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_VOLUME_SET,
)
from openpeerpower.config import async_process_op.core_config
from openpeerpower.const import EVENT_OPENPEERPOWER_STOP
from openpeerpowerr.exceptions import PlatformNotReady
from openpeerpowerr.helpers.dispatcher import async_dispatcher_connect
from openpeerpowerr.helpers.typing import OpenPeerPowerType
from openpeerpowerr.setup import async_setup_component

from tests.common import MockConfigEntry, assert_setup_component
from tests.components.media_player import common


@pytest.fixture()
def dial_mock():
    """Mock pychromecast dial."""
    dial_mock = MagicMock()
    dial_mock.get_device_status.return_value.uuid = "fake_uuid"
    dial_mock.get_device_status.return_value.manufacturer = "fake_manufacturer"
    dial_mock.get_device_status.return_value.model_name = "fake_model_name"
    dial_mock.get_device_status.return_value.friendly_name = "fake_friendly_name"
    dial_mock.get_multizone_status.return_value.dynamic_groups = []
    return dial_mock


@pytest.fixture()
def mz_mock():
    """Mock pychromecast MultizoneManager."""
    return MagicMock()


@pytest.fixture()
def pycast_mock():
    """Mock pychromecast."""
    pycast_mock = MagicMock()
    pycast_mock.start_discovery.return_value = (None, Mock())
    return pycast_mock


@pytest.fixture()
def quick_play_mock():
    """Mock pychromecast quick_play."""
    return MagicMock()


@pytest.fixture(autouse=True)
def cast_mock(dial_mock, mz_mock, pycast_mock, quick_play_mock):
    """Mock pychromecast."""
    with patch(
        "openpeerpower.components.cast.media_player.pychromecast", pycast_mock
    ), patch(
        "openpeerpower.components.cast.discovery.pychromecast", pycast_mock
    ), patch(
        "openpeerpower.components.cast.helpers.dial", dial_mock
    ), patch(
        "openpeerpower.components.cast.media_player.MultizoneManager",
        return_value=mz_mock,
    ), patch(
        "openpeerpower.components.cast.media_player.zeroconf.async_get_instance",
        AsyncMock(),
    ), patch(
        "openpeerpower.components.cast.media_player.quick_play",
        quick_play_mock,
    ):
        yield


# pylint: disable=invalid-name
FakeUUID = UUID("57355bce-9364-4aa6-ac1e-eb849dccf9e2")
FakeUUID2 = UUID("57355bce-9364-4aa6-ac1e-eb849dccf9e4")
FakeGroupUUID = UUID("57355bce-9364-4aa6-ac1e-eb849dccf9e3")


def get_fake_chromecast(info: ChromecastInfo):
    """Generate a Fake Chromecast object with the specified arguments."""
    mock = MagicMock(host=info.host, port=info.port, uuid=info.uuid)
    mock.media_controller.status = None
    return mock


def get_fake_chromecast_info(
    host="192.168.178.42", port=8009, uuid: Optional[UUID] = FakeUUID
):
    """Generate a Fake ChromecastInfo with the specified arguments."""
    return ChromecastInfo(
        host=host,
        port=port,
        uuid=uuid,
        friendly_name="Speaker",
        services={"the-service"},
    )


def get_fake_zconf(host="192.168.178.42", port=8009):
    """Generate a Fake Zeroconf object with the specified arguments."""
    parsed_addresses = MagicMock()
    parsed_addresses.return_value = [host]
    service_info = MagicMock(parsed_addresses=parsed_addresses, port=port)
    zconf = MagicMock()
    zconf.get_service_info.return_value = service_info
    return zconf


async def async_setup_cast.opp, config=None):
    """Set up the cast platform."""
    if config is None:
        config = {}
    with patch(
        "openpeerpowerr.helpers.entity_platform.EntityPlatform._async_schedule_add_entities"
    ) as add_entities:
        MockConfigEntry(domain="cast").add_to_opp.opp)
        await async_setup_component.opp, "cast", {"cast": {"media_player": config}})
        await opp.async_block_till_done()

    return add_entities


async def async_setup_cast_internal_discovery.opp, config=None):
    """Set up the cast platform and the discovery."""
    listener = MagicMock(services={})
    browser = MagicMock(zc={})

    with patch(
        "openpeerpower.components.cast.discovery.pychromecast.CastListener",
        return_value=listener,
    ) as cast_listener, patch(
        "openpeerpower.components.cast.discovery.pychromecast.start_discovery",
        return_value=browser,
    ) as start_discovery:
        add_entities = await async_setup_cast.opp, config)
        await opp.async_block_till_done()
        await opp.async_block_till_done()

        assert start_discovery.call_count == 1

        discovery_callback = cast_listener.call_args[0][0]
        remove_callback = cast_listener.call_args[0][1]

    def discover_chromecast(service_name: str, info: ChromecastInfo) -> None:
        """Discover a chromecast device."""
        listener.services[info.uuid] = (
            {service_name},
            info.uuid,
            info.model_name,
            info.friendly_name,
        )
        discovery_callback(info.uuid, service_name)

    def remove_chromecast(service_name: str, info: ChromecastInfo) -> None:
        """Remove a chromecast device."""
        remove_callback(
            info.uuid,
            service_name,
            (set(), info.uuid, info.model_name, info.friendly_name),
        )

    return discover_chromecast, remove_chromecast, add_entities


async def async_setup_media_player_cast.opp: OpenPeerPowerType, info: ChromecastInfo):
    """Set up the cast platform with async_setup_component."""
    listener = MagicMock(services={})
    browser = MagicMock(zc={})
    chromecast = get_fake_chromecast(info)
    zconf = get_fake_zconf(host=info.host, port=info.port)

    with patch(
        "openpeerpower.components.cast.discovery.pychromecast.get_chromecast_from_service",
        return_value=chromecast,
    ) as get_chromecast, patch(
        "openpeerpower.components.cast.discovery.pychromecast.CastListener",
        return_value=listener,
    ) as cast_listener, patch(
        "openpeerpower.components.cast.discovery.pychromecast.start_discovery",
        return_value=browser,
    ), patch(
        "openpeerpower.components.cast.discovery.ChromeCastZeroconf.get_zeroconf",
        return_value=zconf,
    ):
        await async_setup_component(
           .opp, "cast", {"cast": {"media_player": {"uuid": info.uuid}}}
        )
        await opp.async_block_till_done()

        discovery_callback = cast_listener.call_args[0][0]

        service_name = "the-service"
        listener.services[info.uuid] = (
            {service_name},
            info.uuid,
            info.model_name,
            info.friendly_name,
        )
        discovery_callback(info.uuid, service_name)

        await opp.async_block_till_done()
        await opp.async_block_till_done()
        assert get_chromecast.call_count == 1

        def discover_chromecast(service_name: str, info: ChromecastInfo) -> None:
            """Discover a chromecast device."""
            listener.services[info.uuid] = (
                {service_name},
                info.uuid,
                info.model_name,
                info.friendly_name,
            )
            discovery_callback(info.uuid, service_name)

        return chromecast, discover_chromecast


def get_status_callbacks(chromecast_mock, mz_mock=None):
    """Get registered status callbacks from the chromecast mock."""
    status_listener = chromecast_mock.register_status_listener.call_args[0][0]
    cast_status_cb = status_listener.new_cast_status

    connection_listener = chromecast_mock.register_connection_listener.call_args[0][0]
    conn_status_cb = connection_listener.new_connection_status

    mc = chromecast_mock.socket_client.media_controller
    media_status_cb = mc.register_status_listener.call_args[0][0].new_media_status

    if not mz_mock:
        return cast_status_cb, conn_status_cb, media_status_cb

    mz_listener = mz_mock.register_listener.call_args[0][1]
    group_media_status_cb = mz_listener.multizone_new_media_status
    return cast_status_cb, conn_status_cb, media_status_cb, group_media_status_cb


async def test_start_discovery_called_once.opp):
    """Test pychromecast.start_discovery called exactly once."""
    with patch(
        "openpeerpower.components.cast.discovery.pychromecast.start_discovery",
        return_value=Mock(),
    ) as start_discovery:
        await async_setup_cast.opp)

        assert start_discovery.call_count == 1

        await async_setup_cast.opp)
        assert start_discovery.call_count == 1


async def test_internal_discovery_callback_fill_out.opp):
    """Test internal discovery automatically filling out information."""
    discover_cast, _, _ = await async_setup_cast_internal_discovery.opp)
    info = get_fake_chromecast_info(host="host1")
    zconf = get_fake_zconf(host="host1", port=8009)
    full_info = attr.evolve(
        info,
        model_name="google home",
        friendly_name="Speaker",
        uuid=FakeUUID,
        manufacturer="Nabu Casa",
    )

    with patch(
        "openpeerpower.components.cast.helpers.dial.get_device_status",
        return_value=full_info,
    ), patch(
        "openpeerpower.components.cast.discovery.ChromeCastZeroconf.get_zeroconf",
        return_value=zconf,
    ):
        signal = MagicMock()

        async_dispatcher_connect.opp, "cast_discovered", signal)
        discover_cast("the-service", info)
        await opp.async_block_till_done()

        # when called with incomplete info, it should use HTTP to get missing
        discover = signal.mock_calls[0][1][0]
        assert discover == full_info


async def test_internal_discovery_callback_fill_out_default_manufacturer.opp):
    """Test internal discovery automatically filling out information."""
    discover_cast, _, _ = await async_setup_cast_internal_discovery.opp)
    info = get_fake_chromecast_info(host="host1")
    zconf = get_fake_zconf(host="host1", port=8009)
    full_info = attr.evolve(
        info, model_name="google home", friendly_name="Speaker", uuid=FakeUUID
    )

    with patch(
        "openpeerpower.components.cast.helpers.dial.get_device_status",
        return_value=full_info,
    ), patch(
        "openpeerpower.components.cast.discovery.ChromeCastZeroconf.get_zeroconf",
        return_value=zconf,
    ):
        signal = MagicMock()

        async_dispatcher_connect.opp, "cast_discovered", signal)
        discover_cast("the-service", info)
        await opp.async_block_till_done()

        # when called with incomplete info, it should use HTTP to get missing
        discover = signal.mock_calls[0][1][0]
        assert discover == attr.evolve(full_info, manufacturer="Google Inc.")


async def test_internal_discovery_callback_fill_out_fail.opp):
    """Test internal discovery automatically filling out information."""
    discover_cast, _, _ = await async_setup_cast_internal_discovery.opp)
    info = get_fake_chromecast_info(host="host1")
    zconf = get_fake_zconf(host="host1", port=8009)
    full_info = (
        info  # attr.evolve(info, model_name="", friendly_name="Speaker", uuid=FakeUUID)
    )

    with patch(
        "openpeerpower.components.cast.helpers.dial.get_device_status",
        return_value=None,
    ), patch(
        "openpeerpower.components.cast.discovery.ChromeCastZeroconf.get_zeroconf",
        return_value=zconf,
    ):
        signal = MagicMock()

        async_dispatcher_connect.opp, "cast_discovered", signal)
        discover_cast("the-service", info)
        await opp.async_block_till_done()

        # when called with incomplete info, it should use HTTP to get missing
        discover = signal.mock_calls[0][1][0]
        assert discover == full_info
        # assert 1 == 2


async def test_internal_discovery_callback_fill_out_group.opp):
    """Test internal discovery automatically filling out information."""
    discover_cast, _, _ = await async_setup_cast_internal_discovery.opp)
    info = get_fake_chromecast_info(host="host1", port=12345)
    zconf = get_fake_zconf(host="host1", port=12345)
    full_info = attr.evolve(
        info,
        model_name="",
        friendly_name="Speaker",
        uuid=FakeUUID,
        is_dynamic_group=False,
    )

    with patch(
        "openpeerpower.components.cast.helpers.dial.get_device_status",
        return_value=full_info,
    ), patch(
        "openpeerpower.components.cast.discovery.ChromeCastZeroconf.get_zeroconf",
        return_value=zconf,
    ):
        signal = MagicMock()

        async_dispatcher_connect.opp, "cast_discovered", signal)
        discover_cast("the-service", info)
        await opp.async_block_till_done()

        # when called with incomplete info, it should use HTTP to get missing
        discover = signal.mock_calls[0][1][0]
        assert discover == full_info


async def test_stop_discovery_called_on_stop.opp):
    """Test pychromecast.stop_discovery called on shutdown."""
    browser = MagicMock(zc={})

    with patch(
        "openpeerpower.components.cast.discovery.pychromecast.start_discovery",
        return_value=browser,
    ) as start_discovery:
        # start_discovery should be called with empty config
        await async_setup_cast.opp, {})

        assert start_discovery.call_count == 1

    with patch(
        "openpeerpower.components.cast.discovery.pychromecast.discovery.stop_discovery"
    ) as stop_discovery:
        # stop discovery should be called on shutdown
       .opp.bus.async_fire(EVENT_OPENPEERPOWER_STOP)
        await opp.async_block_till_done()

        stop_discovery.assert_called_once_with(browser)


async def test_create_cast_device_without_uuid.opp):
    """Test create a cast device with no UUId does not create an entity."""
    info = get_fake_chromecast_info(uuid=None)
    cast_device = cast._async_create_cast_device.opp, info)
    assert cast_device is None


async def test_create_cast_device_with_uuid.opp):
    """Test create cast devices with UUID creates entities."""
    added_casts = opp.data[cast.ADDED_CAST_DEVICES_KEY] = set()
    info = get_fake_chromecast_info()

    cast_device = cast._async_create_cast_device.opp, info)
    assert cast_device is not None
    assert info.uuid in added_casts

    # Sending second time should not create new entity
    cast_device = cast._async_create_cast_device.opp, info)
    assert cast_device is None


async def test_replay_past_chromecasts.opp):
    """Test cast platform re-playing past chromecasts when adding new one."""
    cast_group1 = get_fake_chromecast_info(host="host1", port=8009, uuid=FakeUUID)
    cast_group2 = get_fake_chromecast_info(
        host="host2", port=8009, uuid=UUID("9462202c-e747-4af5-a66b-7dce0e1ebc09")
    )
    zconf_1 = get_fake_zconf(host="host1", port=8009)
    zconf_2 = get_fake_zconf(host="host2", port=8009)

    discover_cast, _, add_dev1 = await async_setup_cast_internal_discovery(
       .opp, config={"uuid": FakeUUID}
    )

    with patch(
        "openpeerpower.components.cast.discovery.ChromeCastZeroconf.get_zeroconf",
        return_value=zconf_2,
    ):
        discover_cast("service2", cast_group2)
    await opp.async_block_till_done()
    await opp.async_block_till_done()  # having tasks that add jobs
    assert add_dev1.call_count == 0

    with patch(
        "openpeerpower.components.cast.discovery.ChromeCastZeroconf.get_zeroconf",
        return_value=zconf_1,
    ):
        discover_cast("service1", cast_group1)
    await opp.async_block_till_done()
    await opp.async_block_till_done()  # having tasks that add jobs
    assert add_dev1.call_count == 1

    add_dev2 = Mock()
    await cast._async_setup_platform.opp, {"host": "host2"}, add_dev2)
    await opp.async_block_till_done()
    assert add_dev2.call_count == 1


async def test_manual_cast_chromecasts_uuid.opp):
    """Test only wanted casts are added for manual configuration."""
    cast_1 = get_fake_chromecast_info(host="host_1", uuid=FakeUUID)
    cast_2 = get_fake_chromecast_info(host="host_2", uuid=FakeUUID2)
    zconf_1 = get_fake_zconf(host="host_1")
    zconf_2 = get_fake_zconf(host="host_2")

    # Manual configuration of media player with host "configured_host"
    discover_cast, _, add_dev1 = await async_setup_cast_internal_discovery(
       .opp, config={"uuid": FakeUUID}
    )
    with patch(
        "openpeerpower.components.cast.discovery.ChromeCastZeroconf.get_zeroconf",
        return_value=zconf_2,
    ):
        discover_cast("service2", cast_2)
    await opp.async_block_till_done()
    await opp.async_block_till_done()  # having tasks that add jobs
    assert add_dev1.call_count == 0

    with patch(
        "openpeerpower.components.cast.discovery.ChromeCastZeroconf.get_zeroconf",
        return_value=zconf_1,
    ):
        discover_cast("service1", cast_1)
    await opp.async_block_till_done()
    await opp.async_block_till_done()  # having tasks that add jobs
    assert add_dev1.call_count == 1


async def test_auto_cast_chromecasts.opp):
    """Test all discovered casts are added for default configuration."""
    cast_1 = get_fake_chromecast_info(host="some_host")
    cast_2 = get_fake_chromecast_info(host="other_host", uuid=FakeUUID2)
    zconf_1 = get_fake_zconf(host="some_host")
    zconf_2 = get_fake_zconf(host="other_host")

    # Manual configuration of media player with host "configured_host"
    discover_cast, _, add_dev1 = await async_setup_cast_internal_discovery.opp)
    with patch(
        "openpeerpower.components.cast.discovery.ChromeCastZeroconf.get_zeroconf",
        return_value=zconf_1,
    ):
        discover_cast("service2", cast_2)
    await opp.async_block_till_done()
    await opp.async_block_till_done()  # having tasks that add jobs
    assert add_dev1.call_count == 1

    with patch(
        "openpeerpower.components.cast.discovery.ChromeCastZeroconf.get_zeroconf",
        return_value=zconf_2,
    ):
        discover_cast("service1", cast_1)
    await opp.async_block_till_done()
    await opp.async_block_till_done()  # having tasks that add jobs
    assert add_dev1.call_count == 2


async def test_discover_dynamic_group.opp, dial_mock, pycast_mock, caplog):
    """Test dynamic group does not create device or entity."""
    cast_1 = get_fake_chromecast_info(host="host_1", port=23456, uuid=FakeUUID)
    cast_2 = get_fake_chromecast_info(host="host_2", port=34567, uuid=FakeUUID2)
    zconf_1 = get_fake_zconf(host="host_1", port=23456)
    zconf_2 = get_fake_zconf(host="host_2", port=34567)

    reg = await.opp.helpers.entity_registry.async_get_registry()

    # Fake dynamic group info
    tmp1 = MagicMock()
    tmp1.uuid = FakeUUID
    tmp2 = MagicMock()
    tmp2.uuid = FakeUUID2
    dial_mock.get_multizone_status.return_value.dynamic_groups = [tmp1, tmp2]

    pycast_mock.get_chromecast_from_service.assert_not_called()
    discover_cast, remove_cast, add_dev1 = await async_setup_cast_internal_discovery(
       .opp
    )

    # Discover cast service
    with patch(
        "openpeerpower.components.cast.discovery.ChromeCastZeroconf.get_zeroconf",
        return_value=zconf_1,
    ):
        discover_cast("service", cast_1)
        await opp.async_block_till_done()
        await opp.async_block_till_done()  # having tasks that add jobs
    pycast_mock.get_chromecast_from_service.assert_called()
    pycast_mock.get_chromecast_from_service.reset_mock()
    assert add_dev1.call_count == 0
    assert reg.async_get_entity_id("media_player", "cast", cast_1.uuid) is None

    # Discover other dynamic group cast service
    with patch(
        "openpeerpower.components.cast.discovery.ChromeCastZeroconf.get_zeroconf",
        return_value=zconf_2,
    ):
        discover_cast("service", cast_2)
        await opp.async_block_till_done()
        await opp.async_block_till_done()  # having tasks that add jobs
    pycast_mock.get_chromecast_from_service.assert_called()
    pycast_mock.get_chromecast_from_service.reset_mock()
    assert add_dev1.call_count == 0
    assert reg.async_get_entity_id("media_player", "cast", cast_1.uuid) is None

    # Get update for cast service
    with patch(
        "openpeerpower.components.cast.discovery.ChromeCastZeroconf.get_zeroconf",
        return_value=zconf_1,
    ):
        discover_cast("service", cast_1)
        await opp.async_block_till_done()
        await opp.async_block_till_done()  # having tasks that add jobs
    pycast_mock.get_chromecast_from_service.assert_not_called()
    assert add_dev1.call_count == 0
    assert reg.async_get_entity_id("media_player", "cast", cast_1.uuid) is None

    # Remove cast service
    assert "Disconnecting from chromecast" not in caplog.text

    with patch(
        "openpeerpower.components.cast.discovery.ChromeCastZeroconf.get_zeroconf",
        return_value=zconf_1,
    ):
        remove_cast("service", cast_1)
        await opp.async_block_till_done()
        await opp.async_block_till_done()  # having tasks that add jobs

    assert "Disconnecting from chromecast" in caplog.text


async def test_update_cast_chromecasts.opp):
    """Test discovery of same UUID twice only adds one cast."""
    cast_1 = get_fake_chromecast_info(host="old_host")
    cast_2 = get_fake_chromecast_info(host="new_host")
    zconf_1 = get_fake_zconf(host="old_host")
    zconf_2 = get_fake_zconf(host="new_host")

    # Manual configuration of media player with host "configured_host"
    discover_cast, _, add_dev1 = await async_setup_cast_internal_discovery.opp)

    with patch(
        "openpeerpower.components.cast.discovery.ChromeCastZeroconf.get_zeroconf",
        return_value=zconf_1,
    ):
        discover_cast("service1", cast_1)
    await opp.async_block_till_done()
    await opp.async_block_till_done()  # having tasks that add jobs
    assert add_dev1.call_count == 1

    with patch(
        "openpeerpower.components.cast.discovery.ChromeCastZeroconf.get_zeroconf",
        return_value=zconf_2,
    ):
        discover_cast("service2", cast_2)
    await opp.async_block_till_done()
    await opp.async_block_till_done()  # having tasks that add jobs
    assert add_dev1.call_count == 1


async def test_entity_availability.opp: OpenPeerPowerType):
    """Test handling of connection status."""
    entity_id = "media_player.speaker"
    info = get_fake_chromecast_info()

    chromecast, _ = await async_setup_media_player_cast.opp, info)
    _, conn_status_cb, _ = get_status_callbacks(chromecast)

    state = opp.states.get(entity_id)
    assert state.state == "unavailable"

    connection_status = MagicMock()
    connection_status.status = "CONNECTED"
    conn_status_cb(connection_status)
    await opp.async_block_till_done()
    state = opp.states.get(entity_id)
    assert state.state == "unknown"

    connection_status = MagicMock()
    connection_status.status = "DISCONNECTED"
    conn_status_cb(connection_status)
    await opp.async_block_till_done()
    state = opp.states.get(entity_id)
    assert state.state == "unavailable"


async def test_entity_cast_status.opp: OpenPeerPowerType):
    """Test handling of cast status."""
    entity_id = "media_player.speaker"
    reg = await.opp.helpers.entity_registry.async_get_registry()

    info = get_fake_chromecast_info()
    full_info = attr.evolve(
        info, model_name="google home", friendly_name="Speaker", uuid=FakeUUID
    )

    chromecast, _ = await async_setup_media_player_cast.opp, info)
    cast_status_cb, conn_status_cb, _ = get_status_callbacks(chromecast)

    connection_status = MagicMock()
    connection_status.status = "CONNECTED"
    conn_status_cb(connection_status)
    await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state is not None
    assert state.name == "Speaker"
    assert state.state == "unknown"
    assert entity_id == reg.async_get_entity_id("media_player", "cast", full_info.uuid)

    assert state.attributes.get("supported_features") == (
        SUPPORT_PAUSE
        | SUPPORT_PLAY
        | SUPPORT_PLAY_MEDIA
        | SUPPORT_STOP
        | SUPPORT_TURN_OFF
        | SUPPORT_TURN_ON
        | SUPPORT_VOLUME_MUTE
        | SUPPORT_VOLUME_SET
    )

    cast_status = MagicMock()
    cast_status.volume_level = 0.5
    cast_status.volume_muted = False
    cast_status_cb(cast_status)
    await opp.async_block_till_done()
    state = opp.states.get(entity_id)
    assert state.attributes.get("volume_level") == 0.5
    assert not state.attributes.get("is_volume_muted")

    cast_status = MagicMock()
    cast_status.volume_level = 0.2
    cast_status.volume_muted = True
    cast_status_cb(cast_status)
    await opp.async_block_till_done()
    state = opp.states.get(entity_id)
    assert state.attributes.get("volume_level") == 0.2
    assert state.attributes.get("is_volume_muted")

    # Disable support for volume control
    cast_status = MagicMock()
    cast_status.volume_control_type = "fixed"
    cast_status_cb(cast_status)
    await opp.async_block_till_done()
    state = opp.states.get(entity_id)
    assert state.attributes.get("supported_features") == (
        SUPPORT_PAUSE
        | SUPPORT_PLAY
        | SUPPORT_PLAY_MEDIA
        | SUPPORT_STOP
        | SUPPORT_TURN_OFF
        | SUPPORT_TURN_ON
    )


async def test_entity_play_media.opp: OpenPeerPowerType):
    """Test playing media."""
    entity_id = "media_player.speaker"
    reg = await.opp.helpers.entity_registry.async_get_registry()

    info = get_fake_chromecast_info()
    full_info = attr.evolve(
        info, model_name="google home", friendly_name="Speaker", uuid=FakeUUID
    )

    chromecast, _ = await async_setup_media_player_cast.opp, info)
    _, conn_status_cb, _ = get_status_callbacks(chromecast)

    connection_status = MagicMock()
    connection_status.status = "CONNECTED"
    conn_status_cb(connection_status)
    await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state is not None
    assert state.name == "Speaker"
    assert state.state == "unknown"
    assert entity_id == reg.async_get_entity_id("media_player", "cast", full_info.uuid)

    # Play_media
    await common.async_play_media.opp, "audio", "best.mp3", entity_id)
    chromecast.media_controller.play_media.assert_called_once_with("best.mp3", "audio")


async def test_entity_play_media_cast.opp: OpenPeerPowerType, quick_play_mock):
    """Test playing media with cast special features."""
    entity_id = "media_player.speaker"
    reg = await.opp.helpers.entity_registry.async_get_registry()

    info = get_fake_chromecast_info()
    full_info = attr.evolve(
        info, model_name="google home", friendly_name="Speaker", uuid=FakeUUID
    )

    chromecast, _ = await async_setup_media_player_cast.opp, info)
    _, conn_status_cb, _ = get_status_callbacks(chromecast)

    connection_status = MagicMock()
    connection_status.status = "CONNECTED"
    conn_status_cb(connection_status)
    await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state is not None
    assert state.name == "Speaker"
    assert state.state == "unknown"
    assert entity_id == reg.async_get_entity_id("media_player", "cast", full_info.uuid)

    # Play_media - cast with app ID
    await common.async_play_media.opp, "cast", '{"app_id": "abc123"}', entity_id)
    chromecast.start_app.assert_called_once_with("abc123")

    # Play_media - cast with app name (quick play)
    await common.async_play_media.opp, "cast", '{"app_name": "youtube"}', entity_id)
    quick_play_mock.assert_called_once_with(ANY, "youtube", {})


async def test_entity_play_media_cast_invalid.opp, caplog, quick_play_mock):
    """Test playing media."""
    entity_id = "media_player.speaker"
    reg = await.opp.helpers.entity_registry.async_get_registry()

    info = get_fake_chromecast_info()
    full_info = attr.evolve(
        info, model_name="google home", friendly_name="Speaker", uuid=FakeUUID
    )

    chromecast, _ = await async_setup_media_player_cast.opp, info)
    _, conn_status_cb, _ = get_status_callbacks(chromecast)

    connection_status = MagicMock()
    connection_status.status = "CONNECTED"
    conn_status_cb(connection_status)
    await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state is not None
    assert state.name == "Speaker"
    assert state.state == "unknown"
    assert entity_id == reg.async_get_entity_id("media_player", "cast", full_info.uuid)

    # play_media - media_type cast with invalid JSON
    with pytest.raises(json.decoder.JSONDecodeError):
        await common.async_play_media.opp, "cast", '{"app_id": "abc123"', entity_id)
    assert "Invalid JSON in media_content_id" in caplog.text
    chromecast.start_app.assert_not_called()
    quick_play_mock.assert_not_called()

    # Play_media - media_type cast with extra keys
    await common.async_play_media(
       .opp, "cast", '{"app_id": "abc123", "extra": "data"}', entity_id
    )
    assert "Extra keys dict_keys(['extra']) were ignored" in caplog.text
    chromecast.start_app.assert_called_once_with("abc123")
    quick_play_mock.assert_not_called()

    # Play_media - media_type cast with unsupported app
    quick_play_mock.side_effect = NotImplementedError()
    await common.async_play_media.opp, "cast", '{"app_name": "unknown"}', entity_id)
    quick_play_mock.assert_called_once_with(ANY, "unknown", {})
    assert "App unknown not supported" in caplog.text


async def test_entity_play_media_sign_URL.opp: OpenPeerPowerType):
    """Test playing media."""
    entity_id = "media_player.speaker"

    await async_process_op.core_config(
       .opp,
        {"external_url": "http://example.com:8123"},
    )

    info = get_fake_chromecast_info()

    chromecast, _ = await async_setup_media_player_cast.opp, info)
    _, conn_status_cb, _ = get_status_callbacks(chromecast)

    connection_status = MagicMock()
    connection_status.status = "CONNECTED"
    conn_status_cb(connection_status)
    await opp.async_block_till_done()

    # Play_media
    await common.async_play_media.opp, "audio", "/best.mp3", entity_id)
    chromecast.media_controller.play_media.assert_called_once_with(ANY, "audio")
    assert chromecast.media_controller.play_media.call_args[0][0].startswith(
        "http://example.com:8123/best.mp3?authSig="
    )


async def test_entity_media_content_type.opp: OpenPeerPowerType):
    """Test various content types."""
    entity_id = "media_player.speaker"
    reg = await.opp.helpers.entity_registry.async_get_registry()

    info = get_fake_chromecast_info()
    full_info = attr.evolve(
        info, model_name="google home", friendly_name="Speaker", uuid=FakeUUID
    )

    chromecast, _ = await async_setup_media_player_cast.opp, info)
    _, conn_status_cb, media_status_cb = get_status_callbacks(chromecast)

    connection_status = MagicMock()
    connection_status.status = "CONNECTED"
    conn_status_cb(connection_status)
    await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state is not None
    assert state.name == "Speaker"
    assert state.state == "unknown"
    assert entity_id == reg.async_get_entity_id("media_player", "cast", full_info.uuid)

    media_status = MagicMock(images=None)
    media_status.media_is_movie = False
    media_status.media_is_musictrack = False
    media_status.media_is_tvshow = False
    media_status_cb(media_status)
    await opp.async_block_till_done()
    state = opp.states.get(entity_id)
    assert state.attributes.get("media_content_type") is None

    media_status.media_is_tvshow = True
    media_status_cb(media_status)
    await opp.async_block_till_done()
    state = opp.states.get(entity_id)
    assert state.attributes.get("media_content_type") == "tvshow"

    media_status.media_is_tvshow = False
    media_status.media_is_musictrack = True
    media_status_cb(media_status)
    await opp.async_block_till_done()
    state = opp.states.get(entity_id)
    assert state.attributes.get("media_content_type") == "music"

    media_status.media_is_musictrack = True
    media_status.media_is_movie = True
    media_status_cb(media_status)
    await opp.async_block_till_done()
    state = opp.states.get(entity_id)
    assert state.attributes.get("media_content_type") == "movie"


async def test_entity_control.opp: OpenPeerPowerType):
    """Test various device and media controls."""
    entity_id = "media_player.speaker"
    reg = await.opp.helpers.entity_registry.async_get_registry()

    info = get_fake_chromecast_info()
    full_info = attr.evolve(
        info, model_name="google home", friendly_name="Speaker", uuid=FakeUUID
    )

    chromecast, _ = await async_setup_media_player_cast.opp, info)
    _, conn_status_cb, media_status_cb = get_status_callbacks(chromecast)

    connection_status = MagicMock()
    connection_status.status = "CONNECTED"
    conn_status_cb(connection_status)
    await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state is not None
    assert state.name == "Speaker"
    assert state.state == "unknown"
    assert entity_id == reg.async_get_entity_id("media_player", "cast", full_info.uuid)

    assert state.attributes.get("supported_features") == (
        SUPPORT_PAUSE
        | SUPPORT_PLAY
        | SUPPORT_PLAY_MEDIA
        | SUPPORT_STOP
        | SUPPORT_TURN_OFF
        | SUPPORT_TURN_ON
        | SUPPORT_VOLUME_MUTE
        | SUPPORT_VOLUME_SET
    )

    # Turn on
    await common.async_turn_on.opp, entity_id)
    chromecast.play_media.assert_called_once_with(
        "https://www.openpeerpower.io/images/cast/splash.png", ANY
    )
    chromecast.quit_app.reset_mock()

    # Turn off
    await common.async_turn_off.opp, entity_id)
    chromecast.quit_app.assert_called_once_with()

    # Mute
    await common.async_mute_volume.opp, True, entity_id)
    chromecast.set_volume_muted.assert_called_once_with(True)

    # Volume
    await common.async_set_volume_level.opp, 0.33, entity_id)
    chromecast.set_volume.assert_called_once_with(0.33)

    # Media play
    await common.async_media_play.opp, entity_id)
    chromecast.media_controller.play.assert_called_once_with()

    # Media pause
    await common.async_media_pause.opp, entity_id)
    chromecast.media_controller.pause.assert_called_once_with()

    # Media previous
    await common.async_media_previous_track.opp, entity_id)
    chromecast.media_controller.queue_prev.assert_not_called()

    # Media next
    await common.async_media_next_track.opp, entity_id)
    chromecast.media_controller.queue_next.assert_not_called()

    # Media seek
    await common.async_media_seek.opp, 123, entity_id)
    chromecast.media_controller.seek.assert_not_called()

    # Enable support for queue and seek
    media_status = MagicMock(images=None)
    media_status.supports_queue_next = True
    media_status.supports_seek = True
    media_status_cb(media_status)
    await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state.attributes.get("supported_features") == (
        SUPPORT_PAUSE
        | SUPPORT_PLAY
        | SUPPORT_PLAY_MEDIA
        | SUPPORT_STOP
        | SUPPORT_TURN_OFF
        | SUPPORT_TURN_ON
        | SUPPORT_PREVIOUS_TRACK
        | SUPPORT_NEXT_TRACK
        | SUPPORT_SEEK
        | SUPPORT_VOLUME_MUTE
        | SUPPORT_VOLUME_SET
    )

    # Media previous
    await common.async_media_previous_track.opp, entity_id)
    chromecast.media_controller.queue_prev.assert_called_once_with()

    # Media next
    await common.async_media_next_track.opp, entity_id)
    chromecast.media_controller.queue_next.assert_called_once_with()

    # Media seek
    await common.async_media_seek.opp, 123, entity_id)
    chromecast.media_controller.seek.assert_called_once_with(123)


async def test_entity_media_states.opp: OpenPeerPowerType):
    """Test various entity media states."""
    entity_id = "media_player.speaker"
    reg = await.opp.helpers.entity_registry.async_get_registry()

    info = get_fake_chromecast_info()
    full_info = attr.evolve(
        info, model_name="google home", friendly_name="Speaker", uuid=FakeUUID
    )

    chromecast, _ = await async_setup_media_player_cast.opp, info)
    _, conn_status_cb, media_status_cb = get_status_callbacks(chromecast)

    connection_status = MagicMock()
    connection_status.status = "CONNECTED"
    conn_status_cb(connection_status)
    await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state is not None
    assert state.name == "Speaker"
    assert state.state == "unknown"
    assert entity_id == reg.async_get_entity_id("media_player", "cast", full_info.uuid)

    media_status = MagicMock(images=None)
    media_status.player_is_playing = True
    media_status_cb(media_status)
    await opp.async_block_till_done()
    state = opp.states.get(entity_id)
    assert state.state == "playing"

    media_status.player_is_playing = False
    media_status.player_is_paused = True
    media_status_cb(media_status)
    await opp.async_block_till_done()
    state = opp.states.get(entity_id)
    assert state.state == "paused"

    media_status.player_is_paused = False
    media_status.player_is_idle = True
    media_status_cb(media_status)
    await opp.async_block_till_done()
    state = opp.states.get(entity_id)
    assert state.state == "idle"

    media_status.player_is_idle = False
    chromecast.is_idle = True
    media_status_cb(media_status)
    await opp.async_block_till_done()
    state = opp.states.get(entity_id)
    assert state.state == "off"

    chromecast.is_idle = False
    media_status_cb(media_status)
    await opp.async_block_till_done()
    state = opp.states.get(entity_id)
    assert state.state == "unknown"


async def test_group_media_states.opp, mz_mock):
    """Test media states are read from group if entity has no state."""
    entity_id = "media_player.speaker"
    reg = await.opp.helpers.entity_registry.async_get_registry()

    info = get_fake_chromecast_info()
    full_info = attr.evolve(
        info, model_name="google home", friendly_name="Speaker", uuid=FakeUUID
    )

    chromecast, _ = await async_setup_media_player_cast.opp, info)
    _, conn_status_cb, media_status_cb, group_media_status_cb = get_status_callbacks(
        chromecast, mz_mock
    )

    connection_status = MagicMock()
    connection_status.status = "CONNECTED"
    conn_status_cb(connection_status)
    await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state is not None
    assert state.name == "Speaker"
    assert state.state == "unknown"
    assert entity_id == reg.async_get_entity_id("media_player", "cast", full_info.uuid)

    group_media_status = MagicMock(images=None)
    player_media_status = MagicMock(images=None)

    # Player has no state, group is playing -> Should report 'playing'
    group_media_status.player_is_playing = True
    group_media_status_cb(str(FakeGroupUUID), group_media_status)
    await opp.async_block_till_done()
    state = opp.states.get(entity_id)
    assert state.state == "playing"

    # Player is paused, group is playing -> Should report 'paused'
    player_media_status.player_is_playing = False
    player_media_status.player_is_paused = True
    media_status_cb(player_media_status)
    await opp.async_block_till_done()
    await opp.async_block_till_done()
    state = opp.states.get(entity_id)
    assert state.state == "paused"

    # Player is in unknown state, group is playing -> Should report 'playing'
    player_media_status.player_state = "UNKNOWN"
    media_status_cb(player_media_status)
    await opp.async_block_till_done()
    state = opp.states.get(entity_id)
    assert state.state == "playing"


async def test_group_media_control.opp, mz_mock):
    """Test media controls are handled by group if entity has no state."""
    entity_id = "media_player.speaker"
    reg = await.opp.helpers.entity_registry.async_get_registry()

    info = get_fake_chromecast_info()
    full_info = attr.evolve(
        info, model_name="google home", friendly_name="Speaker", uuid=FakeUUID
    )

    chromecast, _ = await async_setup_media_player_cast.opp, info)

    _, conn_status_cb, media_status_cb, group_media_status_cb = get_status_callbacks(
        chromecast, mz_mock
    )

    connection_status = MagicMock()
    connection_status.status = "CONNECTED"
    conn_status_cb(connection_status)
    await opp.async_block_till_done()

    state = opp.states.get(entity_id)
    assert state is not None
    assert state.name == "Speaker"
    assert state.state == "unknown"
    assert entity_id == reg.async_get_entity_id("media_player", "cast", full_info.uuid)

    group_media_status = MagicMock(images=None)
    player_media_status = MagicMock(images=None)

    # Player has no state, group is playing -> Should forward calls to group
    group_media_status.player_is_playing = True
    group_media_status_cb(str(FakeGroupUUID), group_media_status)
    await common.async_media_play.opp, entity_id)
    grp_media = mz_mock.get_multizone_mediacontroller(str(FakeGroupUUID))
    assert grp_media.play.called
    assert not chromecast.media_controller.play.called

    # Player is paused, group is playing -> Should not forward
    player_media_status.player_is_playing = False
    player_media_status.player_is_paused = True
    media_status_cb(player_media_status)
    await common.async_media_pause.opp, entity_id)
    grp_media = mz_mock.get_multizone_mediacontroller(str(FakeGroupUUID))
    assert not grp_media.pause.called
    assert chromecast.media_controller.pause.called

    # Player is in unknown state, group is playing -> Should forward to group
    player_media_status.player_state = "UNKNOWN"
    media_status_cb(player_media_status)
    await common.async_media_stop.opp, entity_id)
    grp_media = mz_mock.get_multizone_mediacontroller(str(FakeGroupUUID))
    assert grp_media.stop.called
    assert not chromecast.media_controller.stop.called

    # Verify play_media is not forwarded
    await common.async_play_media.opp, "music", "best.mp3", entity_id)
    assert not grp_media.play_media.called
    assert chromecast.media_controller.play_media.called


async def test_failed_cast_on_idle.opp, caplog):
    """Test no warning when unless player went idle with reason "ERROR"."""
    info = get_fake_chromecast_info()
    chromecast, _ = await async_setup_media_player_cast.opp, info)
    _, _, media_status_cb = get_status_callbacks(chromecast)

    media_status = MagicMock(images=None)
    media_status.player_is_idle = False
    media_status.idle_reason = "ERROR"
    media_status.content_id = "http://example.com:8123/tts.mp3"
    media_status_cb(media_status)
    assert "Failed to cast media" not in caplog.text

    media_status = MagicMock(images=None)
    media_status.player_is_idle = True
    media_status.idle_reason = "Other"
    media_status.content_id = "http://example.com:8123/tts.mp3"
    media_status_cb(media_status)
    assert "Failed to cast media" not in caplog.text

    media_status = MagicMock(images=None)
    media_status.player_is_idle = True
    media_status.idle_reason = "ERROR"
    media_status.content_id = "http://example.com:8123/tts.mp3"
    media_status_cb(media_status)
    assert "Failed to cast media http://example.com:8123/tts.mp3." in caplog.text


async def test_failed_cast_other_url.opp, caplog):
    """Test warning when casting from internal_url fails."""
    with assert_setup_component(1, tts.DOMAIN):
        assert await async_setup_component(
           .opp,
            tts.DOMAIN,
            {tts.DOMAIN: {"platform": "demo", "base_url": "http://example.local:8123"}},
        )

    info = get_fake_chromecast_info()
    chromecast, _ = await async_setup_media_player_cast.opp, info)
    _, _, media_status_cb = get_status_callbacks(chromecast)

    media_status = MagicMock(images=None)
    media_status.player_is_idle = True
    media_status.idle_reason = "ERROR"
    media_status.content_id = "http://example.com:8123/tts.mp3"
    media_status_cb(media_status)
    assert "Failed to cast media http://example.com:8123/tts.mp3." in caplog.text


async def test_failed_cast_internal_url.opp, caplog):
    """Test warning when casting from internal_url fails."""
    await async_process_op.core_config(
       .opp,
        {"internal_url": "http://example.local:8123"},
    )
    with assert_setup_component(1, tts.DOMAIN):
        assert await async_setup_component(
           .opp, tts.DOMAIN, {tts.DOMAIN: {"platform": "demo"}}
        )

    info = get_fake_chromecast_info()
    chromecast, _ = await async_setup_media_player_cast.opp, info)
    _, _, media_status_cb = get_status_callbacks(chromecast)

    media_status = MagicMock(images=None)
    media_status.player_is_idle = True
    media_status.idle_reason = "ERROR"
    media_status.content_id = "http://example.local:8123/tts.mp3"
    media_status_cb(media_status)
    assert (
        "Failed to cast media http://example.local:8123/tts.mp3 from internal_url"
        in caplog.text
    )


async def test_failed_cast_external_url.opp, caplog):
    """Test warning when casting from external_url fails."""
    await async_process_op.core_config(
       .opp,
        {"external_url": "http://example.com:8123"},
    )
    with assert_setup_component(1, tts.DOMAIN):
        assert await async_setup_component(
           .opp,
            tts.DOMAIN,
            {tts.DOMAIN: {"platform": "demo", "base_url": "http://example.com:8123"}},
        )

    info = get_fake_chromecast_info()
    chromecast, _ = await async_setup_media_player_cast.opp, info)
    _, _, media_status_cb = get_status_callbacks(chromecast)

    media_status = MagicMock(images=None)
    media_status.player_is_idle = True
    media_status.idle_reason = "ERROR"
    media_status.content_id = "http://example.com:8123/tts.mp3"
    media_status_cb(media_status)
    assert (
        "Failed to cast media http://example.com:8123/tts.mp3 from external_url"
        in caplog.text
    )


async def test_failed_cast_tts_base_url.opp, caplog):
    """Test warning when casting from tts.base_url fails."""
    with assert_setup_component(1, tts.DOMAIN):
        assert await async_setup_component(
           .opp,
            tts.DOMAIN,
            {tts.DOMAIN: {"platform": "demo", "base_url": "http://example.local:8123"}},
        )

    info = get_fake_chromecast_info()
    chromecast, _ = await async_setup_media_player_cast.opp, info)
    _, _, media_status_cb = get_status_callbacks(chromecast)

    media_status = MagicMock(images=None)
    media_status.player_is_idle = True
    media_status.idle_reason = "ERROR"
    media_status.content_id = "http://example.local:8123/tts.mp3"
    media_status_cb(media_status)
    assert (
        "Failed to cast media http://example.local:8123/tts.mp3 from tts.base_url"
        in caplog.text
    )


async def test_disconnect_on_stop.opp: OpenPeerPowerType):
    """Test cast device disconnects socket on stop."""
    info = get_fake_chromecast_info()

    chromecast, _ = await async_setup_media_player_cast.opp, info)

   .opp.bus.async_fire(EVENT_OPENPEERPOWER_STOP)
    await opp.async_block_till_done()
    assert chromecast.disconnect.call_count == 1


async def test_entry_setup_no_config.opp: OpenPeerPowerType):
    """Test setting up entry with no config.."""
    await async_setup_component.opp, "cast", {})
    await opp.async_block_till_done()

    with patch(
        "openpeerpower.components.cast.media_player._async_setup_platform",
    ) as mock_setup:
        await cast.async_setup_entry.opp, MockConfigEntry(), None)

    assert len(mock_setup.mock_calls) == 1
    assert mock_setup.mock_calls[0][1][1] == {}


async def test_entry_setup_single_config.opp: OpenPeerPowerType):
    """Test setting up entry and having a single config option."""
    await async_setup_component(
       .opp, "cast", {"cast": {"media_player": {"uuid": "bla"}}}
    )
    await opp.async_block_till_done()

    with patch(
        "openpeerpower.components.cast.media_player._async_setup_platform",
    ) as mock_setup:
        await cast.async_setup_entry.opp, MockConfigEntry(), None)

    assert len(mock_setup.mock_calls) == 1
    assert mock_setup.mock_calls[0][1][1] == {"uuid": "bla"}


async def test_entry_setup_list_config.opp: OpenPeerPowerType):
    """Test setting up entry and having multiple config options."""
    await async_setup_component(
       .opp, "cast", {"cast": {"media_player": [{"uuid": "bla"}, {"uuid": "blu"}]}}
    )
    await opp.async_block_till_done()

    with patch(
        "openpeerpower.components.cast.media_player._async_setup_platform",
    ) as mock_setup:
        await cast.async_setup_entry.opp, MockConfigEntry(), None)

    assert len(mock_setup.mock_calls) == 2
    assert mock_setup.mock_calls[0][1][1] == {"uuid": "bla"}
    assert mock_setup.mock_calls[1][1][1] == {"uuid": "blu"}


async def test_entry_setup_platform_not_ready.opp: OpenPeerPowerType):
    """Test failed setting up entry will raise PlatformNotReady."""
    await async_setup_component(
       .opp, "cast", {"cast": {"media_player": {"uuid": "bla"}}}
    )
    await opp.async_block_till_done()

    with patch(
        "openpeerpower.components.cast.media_player._async_setup_platform",
        side_effect=Exception,
    ) as mock_setup:
        with pytest.raises(PlatformNotReady):
            await cast.async_setup_entry.opp, MockConfigEntry(), None)

    assert len(mock_setup.mock_calls) == 1
    assert mock_setup.mock_calls[0][1][1] == {"uuid": "bla"}
