"""Tests for the GogoGate2 component."""
from datetime import timedelta
from unittest.mock import MagicMock, patch

from ismartgate import GogoGate2Api, ISmartGateApi
from ismartgate.common import (
    DoorMode,
    DoorStatus,
    GogoGate2ActivateResponse,
    GogoGate2Door,
    GogoGate2InfoResponse,
    Network,
    Outputs,
    TransitionDoorStatus,
    Wifi,
)

from openpeerpower.components.cover import (
    DEVICE_CLASS_GARAGE,
    DEVICE_CLASS_GATE,
    DOMAIN as COVER_DOMAIN,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
)
from openpeerpower.components.gogogate2.const import (
    DEVICE_TYPE_GOGOGATE2,
    DEVICE_TYPE_ISMARTGATE,
    DOMAIN,
    MANUFACTURER,
)
from openpeerpower.config_entries import SOURCE_USER
from openpeerpower.const import (
    ATTR_DEVICE_CLASS,
    CONF_DEVICE,
    CONF_IP_ADDRESS,
    CONF_PASSWORD,
    CONF_USERNAME,
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPEN,
    STATE_OPENING,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from openpeerpower.core import OpenPeerPower
from openpeerpower.util.dt import utcnow

from . import (
    _mocked_gogogate_open_door_response,
    _mocked_ismartgate_closed_door_response,
)

from tests.common import MockConfigEntry, async_fire_time_changed, mock_device_registry


@patch("openpeerpower.components.gogogate2.common.GogoGate2Api")
async def test_open_close_update(gogogate2api_mock, opp: OpenPeerPower) -> None:
    """Test open and close and data update."""

    def info_response(door_status: DoorStatus) -> GogoGate2InfoResponse:
        return GogoGate2InfoResponse(
            user="user1",
            gogogatename="gogogatename0",
            model="",
            apiversion="",
            remoteaccessenabled=False,
            remoteaccess="abc123.blah.blah",
            firmwareversion="",
            apicode="",
            door1=GogoGate2Door(
                door_id=1,
                permission=True,
                name="Door1",
                gate=False,
                mode=DoorMode.GARAGE,
                status=door_status,
                sensor=True,
                sensorid=None,
                camera=False,
                events=2,
                temperature=None,
                voltage=40,
            ),
            door2=GogoGate2Door(
                door_id=2,
                permission=True,
                name=None,
                gate=True,
                mode=DoorMode.GARAGE,
                status=DoorStatus.UNDEFINED,
                sensor=True,
                sensorid=None,
                camera=False,
                events=0,
                temperature=None,
                voltage=40,
            ),
            door3=GogoGate2Door(
                door_id=3,
                permission=True,
                name=None,
                gate=False,
                mode=DoorMode.GARAGE,
                status=DoorStatus.UNDEFINED,
                sensor=True,
                sensorid=None,
                camera=False,
                events=0,
                temperature=None,
                voltage=40,
            ),
            outputs=Outputs(output1=True, output2=False, output3=True),
            network=Network(ip=""),
            wifi=Wifi(SSID="", linkquality="", signal=""),
        )

    expected_attributes = {
        "device_class": "garage",
        "door_id": 1,
        "friendly_name": "Door1",
        "supported_features": SUPPORT_CLOSE | SUPPORT_OPEN,
    }

    api = MagicMock(GogoGate2Api)
    api.async_activate.return_value = GogoGate2ActivateResponse(result=True)
    api.async_info.return_value = info_response(DoorStatus.OPENED)
    api.async_get_door_statuses_from_info.return_value = {
        1: DoorStatus.OPENED,
        2: DoorStatus.OPENED,
    }
    gogogate2api_mock.return_value = api

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data={
            CONF_IP_ADDRESS: "127.0.0.1",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
        },
    )
    config_entry.add_to_opp(opp)

    assert opp.states.get("cover.door1") is None
    assert await opp.config_entries.async_setup(config_entry.entry_id)
    await opp.async_block_till_done()
    assert opp.states.get("cover.door1").state == STATE_OPEN
    assert dict(opp.states.get("cover.door1").attributes) == expected_attributes

    api.async_info.return_value = info_response(DoorStatus.CLOSED)
    api.async_get_door_statuses_from_info.return_value = {
        1: DoorStatus.CLOSED,
        2: DoorStatus.CLOSED,
    }
    await opp.services.async_call(
        COVER_DOMAIN,
        "close_cover",
        service_data={"entity_id": "cover.door1"},
    )
    api.async_get_door_statuses_from_info.return_value = {
        1: TransitionDoorStatus.CLOSING,
        2: TransitionDoorStatus.CLOSING,
    }
    async_fire_time_changed(opp, utcnow() + timedelta(hours=2))
    await opp.async_block_till_done()
    assert opp.states.get("cover.door1").state == STATE_CLOSING
    api.async_close_door.assert_called_with(1)

    async_fire_time_changed(opp, utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert opp.states.get("cover.door1").state == STATE_CLOSING

    api.async_info.return_value = info_response(DoorStatus.CLOSED)
    api.async_get_door_statuses_from_info.return_value = {
        1: DoorStatus.CLOSED,
        2: DoorStatus.CLOSED,
    }
    async_fire_time_changed(opp, utcnow() + timedelta(hours=2))
    await opp.async_block_till_done()
    assert opp.states.get("cover.door1").state == STATE_CLOSED

    api.async_info.return_value = info_response(DoorStatus.OPENED)
    api.async_get_door_statuses_from_info.return_value = {
        1: DoorStatus.OPENED,
        2: DoorStatus.OPENED,
    }
    await opp.services.async_call(
        COVER_DOMAIN,
        "open_cover",
        service_data={"entity_id": "cover.door1"},
    )
    api.async_get_door_statuses_from_info.return_value = {
        1: TransitionDoorStatus.OPENING,
        2: TransitionDoorStatus.OPENING,
    }
    async_fire_time_changed(opp, utcnow() + timedelta(hours=2))
    await opp.async_block_till_done()
    assert opp.states.get("cover.door1").state == STATE_OPENING
    api.async_open_door.assert_called_with(1)

    async_fire_time_changed(opp, utcnow() + timedelta(seconds=10))
    await opp.async_block_till_done()
    assert opp.states.get("cover.door1").state == STATE_OPENING

    api.async_info.return_value = info_response(DoorStatus.OPENED)
    api.async_get_door_statuses_from_info.return_value = {
        1: DoorStatus.OPENED,
        2: DoorStatus.OPENED,
    }
    async_fire_time_changed(opp, utcnow() + timedelta(hours=2))
    await opp.async_block_till_done()
    assert opp.states.get("cover.door1").state == STATE_OPEN

    api.async_info.return_value = info_response(DoorStatus.UNDEFINED)
    api.async_get_door_statuses_from_info.return_value = {
        1: DoorStatus.UNDEFINED,
        2: DoorStatus.UNDEFINED,
    }
    async_fire_time_changed(opp, utcnow() + timedelta(hours=2))
    await opp.async_block_till_done()
    assert opp.states.get("cover.door1").state == STATE_UNKNOWN

    api.async_info.return_value = info_response(DoorStatus.OPENED)
    api.async_get_door_statuses_from_info.return_value = {
        1: DoorStatus.OPENED,
        2: DoorStatus.OPENED,
    }
    await opp.services.async_call(
        COVER_DOMAIN,
        "close_cover",
        service_data={"entity_id": "cover.door1"},
    )
    await opp.services.async_call(
        COVER_DOMAIN,
        "open_cover",
        service_data={"entity_id": "cover.door1"},
    )
    api.async_get_door_statuses_from_info.return_value = {
        1: TransitionDoorStatus.OPENING,
        2: TransitionDoorStatus.OPENING,
    }
    async_fire_time_changed(opp, utcnow() + timedelta(hours=2))
    await opp.async_block_till_done()
    assert opp.states.get("cover.door1").state == STATE_OPENING
    api.async_open_door.assert_called_with(1)

    assert await opp.config_entries.async_unload(config_entry.entry_id)
    assert not opp.states.async_entity_ids(DOMAIN)


@patch("openpeerpower.components.gogogate2.common.ISmartGateApi")
async def test_availability(ismartgateapi_mock, opp: OpenPeerPower) -> None:
    """Test availability."""
    closed_door_response = _mocked_ismartgate_closed_door_response()

    expected_attributes = {
        "device_class": "garage",
        "door_id": 1,
        "friendly_name": "Door1",
        "supported_features": SUPPORT_CLOSE | SUPPORT_OPEN,
    }

    api = MagicMock(ISmartGateApi)
    api.async_info.return_value = closed_door_response
    ismartgateapi_mock.return_value = api

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data={
            CONF_DEVICE: DEVICE_TYPE_ISMARTGATE,
            CONF_IP_ADDRESS: "127.0.0.1",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
        },
    )
    config_entry.add_to_opp(opp)

    assert opp.states.get("cover.door1") is None
    assert await opp.config_entries.async_setup(config_entry.entry_id)
    await opp.async_block_till_done()
    assert opp.states.get("cover.door1")
    assert (
        opp.states.get("cover.door1").attributes[ATTR_DEVICE_CLASS]
        == DEVICE_CLASS_GARAGE
    )
    assert (
        opp.states.get("cover.door2").attributes[ATTR_DEVICE_CLASS] == DEVICE_CLASS_GATE
    )

    api.async_info.side_effect = Exception("Error")

    async_fire_time_changed(opp, utcnow() + timedelta(hours=2))
    await opp.async_block_till_done()
    assert opp.states.get("cover.door1").state == STATE_UNAVAILABLE

    api.async_info.side_effect = None
    api.async_info.return_value = closed_door_response
    api.async_get_door_statuses_from_info.return_value = {
        1: DoorStatus.CLOSED,
        2: DoorStatus.CLOSED,
    }
    async_fire_time_changed(opp, utcnow() + timedelta(hours=2))
    await opp.async_block_till_done()
    assert opp.states.get("cover.door1").state == STATE_CLOSED
    assert dict(opp.states.get("cover.door1").attributes) == expected_attributes


@patch("openpeerpower.components.gogogate2.common.ISmartGateApi")
async def test_device_info_ismartgate(ismartgateapi_mock, opp: OpenPeerPower) -> None:
    """Test device info."""
    device_registry = mock_device_registry(opp)

    closed_door_response = _mocked_ismartgate_closed_door_response()

    api = MagicMock(ISmartGateApi)
    api.async_info.return_value = closed_door_response
    ismartgateapi_mock.return_value = api

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        title="mycontroller",
        unique_id="xyz",
        data={
            CONF_DEVICE: DEVICE_TYPE_ISMARTGATE,
            CONF_IP_ADDRESS: "127.0.0.1",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
        },
    )
    config_entry.add_to_opp(opp)
    assert await opp.config_entries.async_setup(config_entry.entry_id)
    await opp.async_block_till_done()

    device = device_registry.async_get_device({(DOMAIN, "xyz")})
    assert device
    assert device.manufacturer == MANUFACTURER
    assert device.name == "mycontroller"
    assert device.model == "ismartgatePRO"
    assert device.sw_version == "555"


@patch("openpeerpower.components.gogogate2.common.GogoGate2Api")
async def test_device_info_gogogate2(gogogate2api_mock, opp: OpenPeerPower) -> None:
    """Test device info."""
    device_registry = mock_device_registry(opp)

    closed_door_response = _mocked_gogogate_open_door_response()

    api = MagicMock(GogoGate2Api)
    api.async_info.return_value = closed_door_response
    gogogate2api_mock.return_value = api

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        title="mycontroller",
        unique_id="xyz",
        data={
            CONF_DEVICE: DEVICE_TYPE_GOGOGATE2,
            CONF_IP_ADDRESS: "127.0.0.1",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
        },
    )
    config_entry.add_to_opp(opp)
    assert await opp.config_entries.async_setup(config_entry.entry_id)
    await opp.async_block_till_done()

    device = device_registry.async_get_device({(DOMAIN, "xyz")})
    assert device
    assert device.manufacturer == MANUFACTURER
    assert device.name == "mycontroller"
    assert device.model == "gogogate2"
    assert device.sw_version == "222"
