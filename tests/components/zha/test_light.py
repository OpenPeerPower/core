"""Test zha light."""
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, call, patch, sentinel

import pytest
import zigpy.profiles.zha as zha
import zigpy.types
import zigpy.zcl.clusters.general as general
import zigpy.zcl.clusters.lighting as lighting
import zigpy.zcl.foundation as zcl_f

from openpeerpower.components.light import DOMAIN, FLASH_LONG, FLASH_SHORT
from openpeerpower.components.zha.core.group import GroupMember
from openpeerpower.components.zha.light import FLASH_EFFECTS
from openpeerpower.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE
import openpeerpowerr.util.dt as dt_util

from .common import (
    async_enable_traffic,
    async_find_group_entity_id,
    async_test_rejoin,
    find_entity_id,
    get_zha_gateway,
    send_attributes_report,
)

from tests.common import async_fire_time_changed

ON = 1
OFF = 0
IEEE_GROUPABLE_DEVICE = "01:2d:6f:00:0a:90:69:e8"
IEEE_GROUPABLE_DEVICE2 = "02:2d:6f:00:0a:90:69:e9"
IEEE_GROUPABLE_DEVICE3 = "03:2d:6f:00:0a:90:69:e7"

LIGHT_ON_OFF = {
    1: {
        "device_type": zha.DeviceType.ON_OFF_LIGHT,
        "in_clusters": [
            general.Basic.cluster_id,
            general.Identify.cluster_id,
            general.OnOff.cluster_id,
        ],
        "out_clusters": [general.Ota.cluster_id],
    }
}

LIGHT_LEVEL = {
    1: {
        "device_type": zha.DeviceType.DIMMABLE_LIGHT,
        "in_clusters": [
            general.Basic.cluster_id,
            general.LevelControl.cluster_id,
            general.OnOff.cluster_id,
        ],
        "out_clusters": [general.Ota.cluster_id],
    }
}

LIGHT_COLOR = {
    1: {
        "device_type": zha.DeviceType.COLOR_DIMMABLE_LIGHT,
        "in_clusters": [
            general.Basic.cluster_id,
            general.Identify.cluster_id,
            general.LevelControl.cluster_id,
            general.OnOff.cluster_id,
            lighting.Color.cluster_id,
        ],
        "out_clusters": [general.Ota.cluster_id],
    }
}


@pytest.fixture
async def coordinator.opp, zigpy_device_mock, zha_device_joined):
    """Test zha light platform."""

    zigpy_device = zigpy_device_mock(
        {
            1: {
                "in_clusters": [general.Groups.cluster_id],
                "out_clusters": [],
                "device_type": zha.DeviceType.COLOR_DIMMABLE_LIGHT,
            }
        },
        ieee="00:15:8d:00:02:32:4f:32",
        nwk=0x0000,
        node_descriptor=b"\xf8\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff",
    )
    zha_device = await zha_device_joined(zigpy_device)
    zha_device.available = True
    return zha_device


@pytest.fixture
async def device_light_1.opp, zigpy_device_mock, zha_device_joined):
    """Test zha light platform."""

    zigpy_device = zigpy_device_mock(
        {
            1: {
                "in_clusters": [
                    general.OnOff.cluster_id,
                    general.LevelControl.cluster_id,
                    lighting.Color.cluster_id,
                    general.Groups.cluster_id,
                    general.Identify.cluster_id,
                ],
                "out_clusters": [],
                "device_type": zha.DeviceType.COLOR_DIMMABLE_LIGHT,
            }
        },
        ieee=IEEE_GROUPABLE_DEVICE,
        nwk=0xB79D,
    )
    zha_device = await zha_device_joined(zigpy_device)
    zha_device.available = True
    return zha_device


@pytest.fixture
async def device_light_2.opp, zigpy_device_mock, zha_device_joined):
    """Test zha light platform."""

    zigpy_device = zigpy_device_mock(
        {
            1: {
                "in_clusters": [
                    general.OnOff.cluster_id,
                    general.LevelControl.cluster_id,
                    lighting.Color.cluster_id,
                    general.Groups.cluster_id,
                    general.Identify.cluster_id,
                ],
                "out_clusters": [],
                "device_type": zha.DeviceType.COLOR_DIMMABLE_LIGHT,
            }
        },
        ieee=IEEE_GROUPABLE_DEVICE2,
        nwk=0xC79E,
    )
    zha_device = await zha_device_joined(zigpy_device)
    zha_device.available = True
    return zha_device


@pytest.fixture
async def device_light_3.opp, zigpy_device_mock, zha_device_joined):
    """Test zha light platform."""

    zigpy_device = zigpy_device_mock(
        {
            1: {
                "in_clusters": [
                    general.OnOff.cluster_id,
                    general.LevelControl.cluster_id,
                    lighting.Color.cluster_id,
                    general.Groups.cluster_id,
                    general.Identify.cluster_id,
                ],
                "out_clusters": [],
                "device_type": zha.DeviceType.COLOR_DIMMABLE_LIGHT,
            }
        },
        ieee=IEEE_GROUPABLE_DEVICE3,
        nwk=0xB89F,
    )
    zha_device = await zha_device_joined(zigpy_device)
    zha_device.available = True
    return zha_device


@patch("zigpy.zcl.clusters.general.OnOff.read_attributes", new=MagicMock())
async def test_light_refresh.opp, zigpy_device_mock, zha_device_joined_restored):
    """Test zha light platform refresh."""

    # create zigpy devices
    zigpy_device = zigpy_device_mock(LIGHT_ON_OFF)
    zha_device = await zha_device_joined_restored(zigpy_device)
    on_off_cluster = zigpy_device.endpoints[1].on_off
    entity_id = await find_entity_id(DOMAIN, zha_device,.opp)

    # allow traffic to flow through the gateway and device
    await async_enable_traffic.opp, [zha_device])
    on_off_cluster.read_attributes.reset_mock()

    # not enough time passed
    async_fire_time_changed.opp, dt_util.utcnow() + timedelta(minutes=20))
    await.opp.async_block_till_done()
    assert on_off_cluster.read_attributes.call_count == 0
    assert on_off_cluster.read_attributes.await_count == 0
    assert.opp.states.get(entity_id).state == STATE_OFF

    # 1 interval - 1 call
    on_off_cluster.read_attributes.return_value = [{"on_off": 1}, {}]
    async_fire_time_changed.opp, dt_util.utcnow() + timedelta(minutes=80))
    await.opp.async_block_till_done()
    assert on_off_cluster.read_attributes.call_count == 1
    assert on_off_cluster.read_attributes.await_count == 1
    assert.opp.states.get(entity_id).state == STATE_ON

    # 2 intervals - 2 calls
    on_off_cluster.read_attributes.return_value = [{"on_off": 0}, {}]
    async_fire_time_changed.opp, dt_util.utcnow() + timedelta(minutes=80))
    await.opp.async_block_till_done()
    assert on_off_cluster.read_attributes.call_count == 2
    assert on_off_cluster.read_attributes.await_count == 2
    assert.opp.states.get(entity_id).state == STATE_OFF


@patch(
    "zigpy.zcl.clusters.lighting.Color.request",
    new=AsyncMock(return_value=[sentinel.data, zcl_f.Status.SUCCESS]),
)
@patch(
    "zigpy.zcl.clusters.general.Identify.request",
    new=AsyncMock(return_value=[sentinel.data, zcl_f.Status.SUCCESS]),
)
@patch(
    "zigpy.zcl.clusters.general.LevelControl.request",
    new=AsyncMock(return_value=[sentinel.data, zcl_f.Status.SUCCESS]),
)
@patch(
    "zigpy.zcl.clusters.general.OnOff.request",
    new=AsyncMock(return_value=[sentinel.data, zcl_f.Status.SUCCESS]),
)
@pytest.mark.parametrize(
    "device, reporting",
    [(LIGHT_ON_OFF, (1, 0, 0)), (LIGHT_LEVEL, (1, 1, 0)), (LIGHT_COLOR, (1, 1, 3))],
)
async def test_light(
   .opp, zigpy_device_mock, zha_device_joined_restored, device, reporting
):
    """Test zha light platform."""

    # create zigpy devices
    zigpy_device = zigpy_device_mock(device)
    zha_device = await zha_device_joined_restored(zigpy_device)
    entity_id = await find_entity_id(DOMAIN, zha_device,.opp)

    assert entity_id is not None

    cluster_on_off = zigpy_device.endpoints[1].on_off
    cluster_level = getattr(zigpy_device.endpoints[1], "level", None)
    cluster_color = getattr(zigpy_device.endpoints[1], "light_color", None)
    cluster_identify = getattr(zigpy_device.endpoints[1], "identify", None)

    assert.opp.states.get(entity_id).state == STATE_OFF
    await async_enable_traffic.opp, [zha_device], enabled=False)
    # test that the lights were created and that they are unavailable
    assert.opp.states.get(entity_id).state == STATE_UNAVAILABLE

    # allow traffic to flow through the gateway and device
    await async_enable_traffic.opp, [zha_device])

    # test that the lights were created and are off
    assert.opp.states.get(entity_id).state == STATE_OFF

    # test turning the lights on and off from the light
    await async_test_on_off_from_light.opp, cluster_on_off, entity_id)

    # test turning the lights on and off from the HA
    await async_test_on_off_from_opp.opp, cluster_on_off, entity_id)

    # test short flashing the lights from the HA
    if cluster_identify:
        await async_test_flash_from_opp.opp, cluster_identify, entity_id, FLASH_SHORT)

    # test turning the lights on and off from the HA
    if cluster_level:
        await async_test_level_on_off_from_opp(
           .opp, cluster_on_off, cluster_level, entity_id
        )

        # test getting a brightness change from the network
        await async_test_on_from_light.opp, cluster_on_off, entity_id)
        await async_test_dimmer_from_light(
           .opp, cluster_level, entity_id, 150, STATE_ON
        )

    # test rejoin
    await async_test_off_from_opp.opp, cluster_on_off, entity_id)
    clusters = [cluster_on_off]
    if cluster_level:
        clusters.append(cluster_level)
    if cluster_color:
        clusters.append(cluster_color)
    await async_test_rejoin.opp, zigpy_device, clusters, reporting)

    # test long flashing the lights from the HA
    if cluster_identify:
        await async_test_flash_from_opp.opp, cluster_identify, entity_id, FLASH_LONG)


async def async_test_on_off_from_light.opp, cluster, entity_id):
    """Test on off functionality from the light."""
    # turn on at light
    await send_attributes_report.opp, cluster, {1: 0, 0: 1, 2: 3})
    await.opp.async_block_till_done()
    assert.opp.states.get(entity_id).state == STATE_ON

    # turn off at light
    await send_attributes_report.opp, cluster, {1: 1, 0: 0, 2: 3})
    await.opp.async_block_till_done()
    assert.opp.states.get(entity_id).state == STATE_OFF


async def async_test_on_from_light.opp, cluster, entity_id):
    """Test on off functionality from the light."""
    # turn on at light
    await send_attributes_report.opp, cluster, {1: -1, 0: 1, 2: 2})
    await.opp.async_block_till_done()
    assert.opp.states.get(entity_id).state == STATE_ON


async def async_test_on_off_from_opp.opp, cluster, entity_id):
    """Test on off functionality from.opp."""
    # turn on via UI
    cluster.request.reset_mock()
    await.opp.services.async_call(
        DOMAIN, "turn_on", {"entity_id": entity_id}, blocking=True
    )
    assert cluster.request.call_count == 1
    assert cluster.request.await_count == 1
    assert cluster.request.call_args == call(
        False, ON, (), expect_reply=True, manufacturer=None, tries=1, tsn=None
    )

    await async_test_off_from_opp.opp, cluster, entity_id)


async def async_test_off_from_opp.opp, cluster, entity_id):
    """Test turning off the light from Open Peer Power."""

    # turn off via UI
    cluster.request.reset_mock()
    await.opp.services.async_call(
        DOMAIN, "turn_off", {"entity_id": entity_id}, blocking=True
    )
    assert cluster.request.call_count == 1
    assert cluster.request.await_count == 1
    assert cluster.request.call_args == call(
        False, OFF, (), expect_reply=True, manufacturer=None, tries=1, tsn=None
    )


async def async_test_level_on_off_from_opp(
   .opp, on_off_cluster, level_cluster, entity_id
):
    """Test on off functionality from.opp."""

    on_off_cluster.request.reset_mock()
    level_cluster.request.reset_mock()
    # turn on via UI
    await.opp.services.async_call(
        DOMAIN, "turn_on", {"entity_id": entity_id}, blocking=True
    )
    assert on_off_cluster.request.call_count == 1
    assert on_off_cluster.request.await_count == 1
    assert level_cluster.request.call_count == 0
    assert level_cluster.request.await_count == 0
    assert on_off_cluster.request.call_args == call(
        False, ON, (), expect_reply=True, manufacturer=None, tries=1, tsn=None
    )
    on_off_cluster.request.reset_mock()
    level_cluster.request.reset_mock()

    await.opp.services.async_call(
        DOMAIN, "turn_on", {"entity_id": entity_id, "transition": 10}, blocking=True
    )
    assert on_off_cluster.request.call_count == 1
    assert on_off_cluster.request.await_count == 1
    assert level_cluster.request.call_count == 1
    assert level_cluster.request.await_count == 1
    assert on_off_cluster.request.call_args == call(
        False, ON, (), expect_reply=True, manufacturer=None, tries=1, tsn=None
    )
    assert level_cluster.request.call_args == call(
        False,
        4,
        (zigpy.types.uint8_t, zigpy.types.uint16_t),
        254,
        100.0,
        expect_reply=True,
        manufacturer=None,
        tries=1,
        tsn=None,
    )
    on_off_cluster.request.reset_mock()
    level_cluster.request.reset_mock()

    await.opp.services.async_call(
        DOMAIN, "turn_on", {"entity_id": entity_id, "brightness": 10}, blocking=True
    )
    assert on_off_cluster.request.call_count == 1
    assert on_off_cluster.request.await_count == 1
    assert level_cluster.request.call_count == 1
    assert level_cluster.request.await_count == 1
    assert on_off_cluster.request.call_args == call(
        False, ON, (), expect_reply=True, manufacturer=None, tries=1, tsn=None
    )
    assert level_cluster.request.call_args == call(
        False,
        4,
        (zigpy.types.uint8_t, zigpy.types.uint16_t),
        10,
        1,
        expect_reply=True,
        manufacturer=None,
        tries=1,
        tsn=None,
    )
    on_off_cluster.request.reset_mock()
    level_cluster.request.reset_mock()

    await async_test_off_from_opp.opp, on_off_cluster, entity_id)


async def async_test_dimmer_from_light.opp, cluster, entity_id, level, expected_state):
    """Test dimmer functionality from the light."""

    await send_attributes_report(
       .opp, cluster, {1: level + 10, 0: level, 2: level - 10 or 22}
    )
    await.opp.async_block_till_done()
    assert.opp.states.get(entity_id).state == expected_state
    # opp uses None for brightness of 0 in state attributes
    if level == 0:
        level = None
    assert.opp.states.get(entity_id).attributes.get("brightness") == level


async def async_test_flash_from_opp.opp, cluster, entity_id, flash):
    """Test flash functionality from.opp."""
    # turn on via UI
    cluster.request.reset_mock()
    await.opp.services.async_call(
        DOMAIN, "turn_on", {"entity_id": entity_id, "flash": flash}, blocking=True
    )
    assert cluster.request.call_count == 1
    assert cluster.request.await_count == 1
    assert cluster.request.call_args == call(
        False,
        64,
        (zigpy.types.uint8_t, zigpy.types.uint8_t),
        FLASH_EFFECTS[flash],
        0,
        expect_reply=True,
        manufacturer=None,
        tries=1,
        tsn=None,
    )


@patch(
    "zigpy.zcl.clusters.lighting.Color.request",
    new=AsyncMock(return_value=[sentinel.data, zcl_f.Status.SUCCESS]),
)
@patch(
    "zigpy.zcl.clusters.general.Identify.request",
    new=AsyncMock(return_value=[sentinel.data, zcl_f.Status.SUCCESS]),
)
@patch(
    "zigpy.zcl.clusters.general.LevelControl.request",
    new=AsyncMock(return_value=[sentinel.data, zcl_f.Status.SUCCESS]),
)
@patch(
    "zigpy.zcl.clusters.general.OnOff.request",
    new=AsyncMock(return_value=[sentinel.data, zcl_f.Status.SUCCESS]),
)
async def test_zha_group_light_entity(
   .opp, device_light_1, device_light_2, device_light_3, coordinator
):
    """Test the light entity for a ZHA group."""
    zha_gateway = get_zha_gateway.opp)
    assert zha_gateway is not None
    zha_gateway.coordinator_zha_device = coordinator
    coordinator._zha_gateway = zha_gateway
    device_light_1._zha_gateway = zha_gateway
    device_light_2._zha_gateway = zha_gateway
    member_ieee_addresses = [device_light_1.ieee, device_light_2.ieee]
    members = [GroupMember(device_light_1.ieee, 1), GroupMember(device_light_2.ieee, 1)]

    assert coordinator.is_coordinator

    # test creating a group with 2 members
    zha_group = await zha_gateway.async_create_zigpy_group("Test Group", members)
    await.opp.async_block_till_done()

    assert zha_group is not None
    assert len(zha_group.members) == 2
    for member in zha_group.members:
        assert member.device.ieee in member_ieee_addresses
        assert member.group == zha_group
        assert member.endpoint is not None

    device_1_entity_id = await find_entity_id(DOMAIN, device_light_1,.opp)
    device_2_entity_id = await find_entity_id(DOMAIN, device_light_2,.opp)
    device_3_entity_id = await find_entity_id(DOMAIN, device_light_3,.opp)

    assert (
        device_1_entity_id != device_2_entity_id
        and device_1_entity_id != device_3_entity_id
    )
    assert device_2_entity_id != device_3_entity_id

    group_entity_id = async_find_group_entity_id.opp, DOMAIN, zha_group)
    assert.opp.states.get(group_entity_id) is not None

    assert device_1_entity_id in zha_group.member_entity_ids
    assert device_2_entity_id in zha_group.member_entity_ids
    assert device_3_entity_id not in zha_group.member_entity_ids

    group_cluster_on_off = zha_group.endpoint[general.OnOff.cluster_id]
    group_cluster_level = zha_group.endpoint[general.LevelControl.cluster_id]
    group_cluster_identify = zha_group.endpoint[general.Identify.cluster_id]

    dev1_cluster_on_off = device_light_1.device.endpoints[1].on_off
    dev2_cluster_on_off = device_light_2.device.endpoints[1].on_off
    dev3_cluster_on_off = device_light_3.device.endpoints[1].on_off

    dev1_cluster_level = device_light_1.device.endpoints[1].level

    await async_enable_traffic(
       .opp, [device_light_1, device_light_2, device_light_3], enabled=False
    )
    await.opp.async_block_till_done()
    # test that the lights were created and that they are unavailable
    assert.opp.states.get(group_entity_id).state == STATE_UNAVAILABLE

    # allow traffic to flow through the gateway and device
    await async_enable_traffic.opp, [device_light_1, device_light_2, device_light_3])
    await.opp.async_block_till_done()

    # test that the lights were created and are off
    assert.opp.states.get(group_entity_id).state == STATE_OFF

    # test turning the lights on and off from the HA
    await async_test_on_off_from_opp.opp, group_cluster_on_off, group_entity_id)

    # test short flashing the lights from the HA
    await async_test_flash_from_opp(
       .opp, group_cluster_identify, group_entity_id, FLASH_SHORT
    )

    # test turning the lights on and off from the light
    await async_test_on_off_from_light.opp, dev1_cluster_on_off, group_entity_id)

    # test turning the lights on and off from the HA
    await async_test_level_on_off_from_opp(
       .opp, group_cluster_on_off, group_cluster_level, group_entity_id
    )

    # test getting a brightness change from the network
    await async_test_on_from_light.opp, dev1_cluster_on_off, group_entity_id)
    await async_test_dimmer_from_light(
       .opp, dev1_cluster_level, group_entity_id, 150, STATE_ON
    )

    # test long flashing the lights from the HA
    await async_test_flash_from_opp(
       .opp, group_cluster_identify, group_entity_id, FLASH_LONG
    )

    assert len(zha_group.members) == 2
    # test some of the group logic to make sure we key off states correctly
    await send_attributes_report.opp, dev1_cluster_on_off, {0: 1})
    await send_attributes_report.opp, dev2_cluster_on_off, {0: 1})
    await.opp.async_block_till_done()

    # test that group light is on
    assert.opp.states.get(device_1_entity_id).state == STATE_ON
    assert.opp.states.get(device_2_entity_id).state == STATE_ON
    assert.opp.states.get(group_entity_id).state == STATE_ON

    await send_attributes_report.opp, dev1_cluster_on_off, {0: 0})
    await.opp.async_block_till_done()

    # test that group light is still on
    assert.opp.states.get(device_1_entity_id).state == STATE_OFF
    assert.opp.states.get(device_2_entity_id).state == STATE_ON
    assert.opp.states.get(group_entity_id).state == STATE_ON

    await send_attributes_report.opp, dev2_cluster_on_off, {0: 0})
    await.opp.async_block_till_done()

    # test that group light is now off
    assert.opp.states.get(device_1_entity_id).state == STATE_OFF
    assert.opp.states.get(device_2_entity_id).state == STATE_OFF
    assert.opp.states.get(group_entity_id).state == STATE_OFF

    await send_attributes_report.opp, dev1_cluster_on_off, {0: 1})
    await.opp.async_block_till_done()

    # test that group light is now back on
    assert.opp.states.get(device_1_entity_id).state == STATE_ON
    assert.opp.states.get(device_2_entity_id).state == STATE_OFF
    assert.opp.states.get(group_entity_id).state == STATE_ON

    # turn it off to test a new member add being tracked
    await send_attributes_report.opp, dev1_cluster_on_off, {0: 0})
    await.opp.async_block_till_done()
    assert.opp.states.get(device_1_entity_id).state == STATE_OFF
    assert.opp.states.get(device_2_entity_id).state == STATE_OFF
    assert.opp.states.get(group_entity_id).state == STATE_OFF

    # add a new member and test that his state is also tracked
    await zha_group.async_add_members([GroupMember(device_light_3.ieee, 1)])
    await send_attributes_report.opp, dev3_cluster_on_off, {0: 1})
    await.opp.async_block_till_done()
    assert device_3_entity_id in zha_group.member_entity_ids
    assert len(zha_group.members) == 3

    assert.opp.states.get(device_1_entity_id).state == STATE_OFF
    assert.opp.states.get(device_2_entity_id).state == STATE_OFF
    assert.opp.states.get(device_3_entity_id).state == STATE_ON
    assert.opp.states.get(group_entity_id).state == STATE_ON

    # make the group have only 1 member and now there should be no entity
    await zha_group.async_remove_members(
        [GroupMember(device_light_2.ieee, 1), GroupMember(device_light_3.ieee, 1)]
    )
    assert len(zha_group.members) == 1
    assert.opp.states.get(group_entity_id) is None
    assert device_2_entity_id not in zha_group.member_entity_ids
    assert device_3_entity_id not in zha_group.member_entity_ids

    # make sure the entity registry entry is still there
    assert zha_gateway.ha_entity_registry.async_get(group_entity_id) is not None

    # add a member back and ensure that the group entity was created again
    await zha_group.async_add_members([GroupMember(device_light_3.ieee, 1)])
    await send_attributes_report.opp, dev3_cluster_on_off, {0: 1})
    await.opp.async_block_till_done()
    assert len(zha_group.members) == 2
    assert.opp.states.get(group_entity_id).state == STATE_ON

    # add a 3rd member and ensure we still have an entity and we track the new one
    await send_attributes_report.opp, dev1_cluster_on_off, {0: 0})
    await send_attributes_report.opp, dev3_cluster_on_off, {0: 0})
    await.opp.async_block_till_done()
    assert.opp.states.get(group_entity_id).state == STATE_OFF

    # this will test that _reprobe_group is used correctly
    await zha_group.async_add_members(
        [GroupMember(device_light_2.ieee, 1), GroupMember(coordinator.ieee, 1)]
    )
    await send_attributes_report.opp, dev2_cluster_on_off, {0: 1})
    await.opp.async_block_till_done()
    assert len(zha_group.members) == 4
    assert.opp.states.get(group_entity_id).state == STATE_ON

    await zha_group.async_remove_members([GroupMember(coordinator.ieee, 1)])
    await.opp.async_block_till_done()
    assert.opp.states.get(group_entity_id).state == STATE_ON
    assert len(zha_group.members) == 3

    # remove the group and ensure that there is no entity and that the entity registry is cleaned up
    assert zha_gateway.ha_entity_registry.async_get(group_entity_id) is not None
    await zha_gateway.async_remove_zigpy_group(zha_group.group_id)
    assert.opp.states.get(group_entity_id) is None
    assert zha_gateway.ha_entity_registry.async_get(group_entity_id) is None
