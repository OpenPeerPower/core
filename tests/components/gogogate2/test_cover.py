"""Tests for the GogoGate2 component."""
from datetime import timedelta
from unittest.mock import MagicMock, patch

from gogogate2_api import GogoGate2Api, ISmartGateApi
from gogogate2_api.common import (
    ApiError,
    DoorMode,
    DoorStatus,
    GogoGate2ActivateResponse,
    GogoGate2Door,
    GogoGate2InfoResponse,
    ISmartGateDoor,
    ISmartGateInfoResponse,
    Network,
    Outputs,
    Wifi,
)

from openpeerpower.components.cover import (
    DEVICE_CLASS_GARAGE,
    DEVICE_CLASS_GATE,
    DOMAIN as COVER_DOMAIN,
)
from openpeerpower.components.gogogate2.const import (
    DEVICE_TYPE_GOGOGATE2,
    DEVICE_TYPE_ISMARTGATE,
    DOMAIN,
    MANUFACTURER,
)
from openpeerpower.components.openpeerpower import DOMAIN as HA_DOMAIN
from openpeerpower.config import async_process_ha_core_config
from openpeerpower.config_entries import SOURCE_USER
from openpeerpower.const import (
    ATTR_DEVICE_CLASS,
    CONF_DEVICE,
    CONF_IP_ADDRESS,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PLATFORM,
    CONF_UNIT_SYSTEM,
    CONF_UNIT_SYSTEM_METRIC,
    CONF_USERNAME,
    STATE_CLOSED,
    STATE_OPEN,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from openpeerpower.core import OpenPeerPower
from openpeerpower.setup import async_setup_component
from openpeerpower.util.dt import utcnow

from tests.common import MockConfigEntry, async_fire_time_changed, mock_device_registry


def _mocked_gogogate_open_door_response():
    return GogoGate2InfoResponse(
        user="user1",
        gogogatename="gogogatename0",
        model="gogogate2",
        apiversion="",
        remoteaccessenabled=False,
        remoteaccess="abc123.blah.blah",
        firmwareversion="222",
        apicode="",
        door1=GogoGate2Door(
            door_id=1,
            permission=True,
            name="Door1",
            gate=False,
            mode=DoorMode.GARAGE,
            status=DoorStatus.OPENED,
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


def _mocked_ismartgate_closed_door_response():
    return ISmartGateInfoResponse(
        user="user1",
        ismartgatename="ismartgatename0",
        model="ismartgatePRO",
        apiversion="",
        remoteaccessenabled=False,
        remoteaccess="abc321.blah.blah",
        firmwareversion="555",
        pin=123,
        lang="en",
        newfirmware=False,
        door1=ISmartGateDoor(
            door_id=1,
            permission=True,
            name="Door1",
            gate=False,
            mode=DoorMode.GARAGE,
            status=DoorStatus.CLOSED,
            sensor=True,
            sensorid=None,
            camera=False,
            events=2,
            temperature=None,
            enabled=True,
            apicode="apicode0",
            customimage=False,
            voltage=40,
        ),
        door2=ISmartGateDoor(
            door_id=2,
            permission=True,
            name="Door2",
            gate=True,
            mode=DoorMode.GARAGE,
            status=DoorStatus.CLOSED,
            sensor=True,
            sensorid=None,
            camera=False,
            events=2,
            temperature=None,
            enabled=True,
            apicode="apicode0",
            customimage=False,
            voltage=40,
        ),
        door3=ISmartGateDoor(
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
            enabled=True,
            apicode="apicode0",
            customimage=False,
            voltage=40,
        ),
        network=Network(ip=""),
        wifi=Wifi(SSID="", linkquality="", signal=""),
    )


@patch("openpeerpower.components.gogogate2.common.GogoGate2Api")
async def test_import_fail(gogogate2api_mock, opp: OpenPeerPower) -> None:
    """Test the failure to import."""
    api = MagicMock(spec=GogoGate2Api)
    api.async_info.side_effect = ApiError(22, "Error")
    gogogate2api_mock.return_value = api

   .opp_config = {
        HA_DOMAIN: {CONF_UNIT_SYSTEM: CONF_UNIT_SYSTEM_METRIC},
        COVER_DOMAIN: [
            {
                CONF_PLATFORM: "gogogate2",
                CONF_NAME: "cover0",
                CONF_DEVICE: DEVICE_TYPE_GOGOGATE2,
                CONF_IP_ADDRESS: "127.0.1.0",
                CONF_USERNAME: "user0",
                CONF_PASSWORD: "password0",
            }
        ],
    }

    await async_process_ha_core_config(opp, opp_config[HA_DOMAIN])
    assert await async_setup_component.opp, HA_DOMAIN, {})
    assert await async_setup_component.opp, COVER_DOMAIN, opp_config)
    await.opp.async_block_till_done()

    entity_ids = opp.states.async_entity_ids(COVER_DOMAIN)
    assert not entity_ids


@patch("openpeerpower.components.gogogate2.common.GogoGate2Api")
@patch("openpeerpower.components.gogogate2.common.ISmartGateApi")
async def test_import(
    ismartgateapi_mock, gogogate2api_mock, opp: OpenPeerPower
) -> None:
    """Test importing of file based config."""
    api0 = MagicMock(spec=GogoGate2Api)
    api0.async_info.return_value = _mocked_gogogate_open_door_response()
    gogogate2api_mock.return_value = api0

    api1 = MagicMock(spec=ISmartGateApi)
    api1.async_info.return_value = _mocked_ismartgate_closed_door_response()
    ismartgateapi_mock.return_value = api1

   .opp_config = {
        HA_DOMAIN: {CONF_UNIT_SYSTEM: CONF_UNIT_SYSTEM_METRIC},
        COVER_DOMAIN: [
            {
                CONF_PLATFORM: "gogogate2",
                CONF_NAME: "cover0",
                CONF_DEVICE: DEVICE_TYPE_GOGOGATE2,
                CONF_IP_ADDRESS: "127.0.1.0",
                CONF_USERNAME: "user0",
                CONF_PASSWORD: "password0",
            },
            {
                CONF_PLATFORM: "gogogate2",
                CONF_NAME: "cover1",
                CONF_DEVICE: DEVICE_TYPE_ISMARTGATE,
                CONF_IP_ADDRESS: "127.0.1.1",
                CONF_USERNAME: "user1",
                CONF_PASSWORD: "password1",
            },
        ],
    }

    await async_process_ha_core_config(opp, opp_config[HA_DOMAIN])
    assert await async_setup_component.opp, HA_DOMAIN, {})
    assert await async_setup_component.opp, COVER_DOMAIN, opp_config)
    await.opp.async_block_till_done()

    entity_ids = opp.states.async_entity_ids(COVER_DOMAIN)
    assert entity_ids is not None
    assert len(entity_ids) == 3
    assert "cover.door1" in entity_ids
    assert "cover.door1_2" in entity_ids
    assert "cover.door2" in entity_ids


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

    api = MagicMock(GogoGate2Api)
    api.async_activate.return_value = GogoGate2ActivateResponse(result=True)
    api.async_info.return_value = info_response(DoorStatus.OPENED)
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
    config_entry.add_to.opp.opp)

    assert.opp.states.get("cover.door1") is None
    assert await.opp.config_entries.async_setup(config_entry.entry_id)
    await.opp.async_block_till_done()
    assert.opp.states.get("cover.door1").state == STATE_OPEN

    api.async_info.return_value = info_response(DoorStatus.CLOSED)
    await.opp.services.async_call(
        COVER_DOMAIN,
        "close_cover",
        service_data={"entity_id": "cover.door1"},
    )
    async_fire_time_changed.opp, utcnow() + timedelta(hours=2))
    await.opp.async_block_till_done()
    assert.opp.states.get("cover.door1").state == STATE_CLOSED
    api.async_close_door.assert_called_with(1)

    api.async_info.return_value = info_response(DoorStatus.OPENED)
    await.opp.services.async_call(
        COVER_DOMAIN,
        "open_cover",
        service_data={"entity_id": "cover.door1"},
    )
    async_fire_time_changed.opp, utcnow() + timedelta(hours=2))
    await.opp.async_block_till_done()
    assert.opp.states.get("cover.door1").state == STATE_OPEN
    api.async_open_door.assert_called_with(1)

    api.async_info.return_value = info_response(DoorStatus.UNDEFINED)
    async_fire_time_changed.opp, utcnow() + timedelta(hours=2))
    await.opp.async_block_till_done()
    assert.opp.states.get("cover.door1").state == STATE_UNKNOWN

    assert await.opp.config_entries.async_unload(config_entry.entry_id)
    assert not.opp.states.async_entity_ids(DOMAIN)


@patch("openpeerpower.components.gogogate2.common.ISmartGateApi")
async def test_availability(ismartgateapi_mock, opp: OpenPeerPower) -> None:
    """Test availability."""
    closed_door_response = _mocked_ismartgate_closed_door_response()

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
    config_entry.add_to.opp.opp)

    assert.opp.states.get("cover.door1") is None
    assert await.opp.config_entries.async_setup(config_entry.entry_id)
    await.opp.async_block_till_done()
    assert.opp.states.get("cover.door1")
    assert (
       .opp.states.get("cover.door1").attributes[ATTR_DEVICE_CLASS]
        == DEVICE_CLASS_GARAGE
    )
    assert (
       .opp.states.get("cover.door2").attributes[ATTR_DEVICE_CLASS]
        == DEVICE_CLASS_GATE
    )

    api.async_info.side_effect = Exception("Error")

    async_fire_time_changed.opp, utcnow() + timedelta(hours=2))
    await.opp.async_block_till_done()
    assert.opp.states.get("cover.door1").state == STATE_UNAVAILABLE

    api.async_info.side_effect = None
    api.async_info.return_value = closed_door_response
    async_fire_time_changed.opp, utcnow() + timedelta(hours=2))
    await.opp.async_block_till_done()
    assert.opp.states.get("cover.door1").state == STATE_CLOSED


@patch("openpeerpower.components.gogogate2.common.ISmartGateApi")
async def test_device_info_ismartgate(ismartgateapi_mock, opp: OpenPeerPower) -> None:
    """Test device info."""
    device_registry = mock_device_registry.opp)

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
    config_entry.add_to.opp.opp)
    assert await.opp.config_entries.async_setup(config_entry.entry_id)
    await.opp.async_block_till_done()

    device = device_registry.async_get_device({(DOMAIN, "xyz")})
    assert device
    assert device.manufacturer == MANUFACTURER
    assert device.name == "mycontroller"
    assert device.model == "ismartgatePRO"
    assert device.sw_version == "555"


@patch("openpeerpower.components.gogogate2.common.GogoGate2Api")
async def test_device_info_gogogate2(gogogate2api_mock, opp: OpenPeerPower) -> None:
    """Test device info."""
    device_registry = mock_device_registry.opp)

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
    config_entry.add_to.opp.opp)
    assert await.opp.config_entries.async_setup(config_entry.entry_id)
    await.opp.async_block_till_done()

    device = device_registry.async_get_device({(DOMAIN, "xyz")})
    assert device
    assert device.manufacturer == MANUFACTURER
    assert device.name == "mycontroller"
    assert device.model == "gogogate2"
    assert device.sw_version == "222"
