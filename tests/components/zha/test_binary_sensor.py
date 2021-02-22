"""Test zha binary sensor."""
import pytest
import zigpy.profiles.zha
import zigpy.zcl.clusters.measurement as measurement
import zigpy.zcl.clusters.security as security

from openpeerpower.components.binary_sensor import DOMAIN
from openpeerpower.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE

from .common import (
    async_enable_traffic,
    async_test_rejoin,
    find_entity_id,
    send_attributes_report,
)

DEVICE_IAS = {
    1: {
        "device_type": zigpy.profiles.zha.DeviceType.IAS_ZONE,
        "in_clusters": [security.IasZone.cluster_id],
        "out_clusters": [],
    }
}


DEVICE_OCCUPANCY = {
    1: {
        "device_type": zigpy.profiles.zha.DeviceType.OCCUPANCY_SENSOR,
        "in_clusters": [measurement.OccupancySensing.cluster_id],
        "out_clusters": [],
    }
}


async def async_test_binary_sensor_on_off.opp, cluster, entity_id):
    """Test getting on and off messages for binary sensors."""
    # binary sensor on
    await send_attributes_report.opp, cluster, {1: 0, 0: 1, 2: 2})
    assert.opp.states.get(entity_id).state == STATE_ON

    # binary sensor off
    await send_attributes_report.opp, cluster, {1: 1, 0: 0, 2: 2})
    assert.opp.states.get(entity_id).state == STATE_OFF


async def async_test_iaszone_on_off.opp, cluster, entity_id):
    """Test getting on and off messages for iaszone binary sensors."""
    # binary sensor on
    cluster.listener_event("cluster_command", 1, 0, [1])
    await.opp.async_block_till_done()
    assert.opp.states.get(entity_id).state == STATE_ON

    # binary sensor off
    cluster.listener_event("cluster_command", 1, 0, [0])
    await.opp.async_block_till_done()
    assert.opp.states.get(entity_id).state == STATE_OFF


@pytest.mark.parametrize(
    "device, on_off_test, cluster_name, reporting",
    [
        (DEVICE_IAS, async_test_iaszone_on_off, "ias_zone", (0,)),
        # (DEVICE_OCCUPANCY, async_test_binary_sensor_on_off, "occupancy", (1,)),
    ],
)
async def test_binary_sensor(
   .opp,
    zigpy_device_mock,
    zha_device_joined_restored,
    device,
    on_off_test,
    cluster_name,
    reporting,
):
    """Test ZHA binary_sensor platform."""
    zigpy_device = zigpy_device_mock(device)
    zha_device = await zha_device_joined_restored(zigpy_device)
    entity_id = await find_entity_id(DOMAIN, zha_device, opp)
    assert entity_id is not None

    assert.opp.states.get(entity_id).state == STATE_OFF
    await async_enable_traffic.opp, [zha_device], enabled=False)
    # test that the sensors exist and are in the unavailable state
    assert.opp.states.get(entity_id).state == STATE_UNAVAILABLE

    await async_enable_traffic.opp, [zha_device])

    # test that the sensors exist and are in the off state
    assert.opp.states.get(entity_id).state == STATE_OFF

    # test getting messages that trigger and reset the sensors
    cluster = getattr(zigpy_device.endpoints[1], cluster_name)
    await on_off_test.opp, cluster, entity_id)

    # test rejoin
    await async_test_rejoin.opp, zigpy_device, [cluster], reporting)
    assert.opp.states.get(entity_id).state == STATE_OFF
