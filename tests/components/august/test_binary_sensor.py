"""The binary_sensor tests for the august platform."""
import datetime
from unittest.mock import Mock, patch

from yalexs.pubnub_async import AugustPubNub

from openpeerpower.components.lock import DOMAIN as LOCK_DOMAIN
from openpeerpower.const import (
    ATTR_ENTITY_ID,
    SERVICE_LOCK,
    SERVICE_UNLOCK,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from openpeerpower.helpers import device_registry as dr
import openpeerpower.util.dt as dt_util

from tests.common import async_fire_time_changed
from tests.components.august.mocks import (
    _create_august_with_devices,
    _mock_activities_from_fixture,
    _mock_doorbell_from_fixture,
    _mock_doorsense_enabled_august_lock_detail,
    _mock_lock_from_fixture,
)


async def test_doorsense(opp):
    """Test creation of a lock with doorsense and bridge."""
    lock_one = await _mock_lock_from_fixture(
        opp, "get_lock.online_with_doorsense.json"
    )
    await _create_august_with_devices(opp, [lock_one])

    binary_sensor_online_with_doorsense_name = opp.states.get(
        "binary_sensor.online_with_doorsense_name_open"
    )
    assert binary_sensor_online_with_doorsense_name.state == STATE_ON

    data = {ATTR_ENTITY_ID: "lock.online_with_doorsense_name"}
    assert await opp.services.async_call(
        LOCK_DOMAIN, SERVICE_UNLOCK, data, blocking=True
    )
    await opp.async_block_till_done()

    binary_sensor_online_with_doorsense_name = opp.states.get(
        "binary_sensor.online_with_doorsense_name_open"
    )
    assert binary_sensor_online_with_doorsense_name.state == STATE_ON

    assert await opp.services.async_call(
        LOCK_DOMAIN, SERVICE_LOCK, data, blocking=True
    )
    await opp.async_block_till_done()

    binary_sensor_online_with_doorsense_name = opp.states.get(
        "binary_sensor.online_with_doorsense_name_open"
    )
    assert binary_sensor_online_with_doorsense_name.state == STATE_OFF


async def test_lock_bridge_offline(opp):
    """Test creation of a lock with doorsense and bridge that goes offline."""
    lock_one = await _mock_lock_from_fixture(
        opp, "get_lock.online_with_doorsense.json"
    )
    activities = await _mock_activities_from_fixture(
        opp, "get_activity.bridge_offline.json"
    )
    await _create_august_with_devices(opp, [lock_one], activities=activities)

    binary_sensor_online_with_doorsense_name = opp.states.get(
        "binary_sensor.online_with_doorsense_name_open"
    )
    assert binary_sensor_online_with_doorsense_name.state == STATE_UNAVAILABLE


async def test_create_doorbell(opp):
    """Test creation of a doorbell."""
    doorbell_one = await _mock_doorbell_from_fixture(opp, "get_doorbell.json")
    await _create_august_with_devices(opp, [doorbell_one])

    binary_sensor_k98gidt45gul_name_motion = opp.states.get(
        "binary_sensor.k98gidt45gul_name_motion"
    )
    assert binary_sensor_k98gidt45gul_name_motion.state == STATE_OFF
    binary_sensor_k98gidt45gul_name_online = opp.states.get(
        "binary_sensor.k98gidt45gul_name_online"
    )
    assert binary_sensor_k98gidt45gul_name_online.state == STATE_ON
    binary_sensor_k98gidt45gul_name_ding = opp.states.get(
        "binary_sensor.k98gidt45gul_name_ding"
    )
    assert binary_sensor_k98gidt45gul_name_ding.state == STATE_OFF
    binary_sensor_k98gidt45gul_name_motion = opp.states.get(
        "binary_sensor.k98gidt45gul_name_motion"
    )
    assert binary_sensor_k98gidt45gul_name_motion.state == STATE_OFF


async def test_create_doorbell_offline(opp):
    """Test creation of a doorbell that is offline."""
    doorbell_one = await _mock_doorbell_from_fixture(opp, "get_doorbell.offline.json")
    await _create_august_with_devices(opp, [doorbell_one])

    binary_sensor_tmt100_name_motion = opp.states.get(
        "binary_sensor.tmt100_name_motion"
    )
    assert binary_sensor_tmt100_name_motion.state == STATE_UNAVAILABLE
    binary_sensor_tmt100_name_online = opp.states.get(
        "binary_sensor.tmt100_name_online"
    )
    assert binary_sensor_tmt100_name_online.state == STATE_OFF
    binary_sensor_tmt100_name_ding = opp.states.get("binary_sensor.tmt100_name_ding")
    assert binary_sensor_tmt100_name_ding.state == STATE_UNAVAILABLE


async def test_create_doorbell_with_motion(opp):
    """Test creation of a doorbell."""
    doorbell_one = await _mock_doorbell_from_fixture(opp, "get_doorbell.json")
    activities = await _mock_activities_from_fixture(
        opp, "get_activity.doorbell_motion.json"
    )
    await _create_august_with_devices(opp, [doorbell_one], activities=activities)

    binary_sensor_k98gidt45gul_name_motion = opp.states.get(
        "binary_sensor.k98gidt45gul_name_motion"
    )
    assert binary_sensor_k98gidt45gul_name_motion.state == STATE_ON
    binary_sensor_k98gidt45gul_name_online = opp.states.get(
        "binary_sensor.k98gidt45gul_name_online"
    )
    assert binary_sensor_k98gidt45gul_name_online.state == STATE_ON
    binary_sensor_k98gidt45gul_name_ding = opp.states.get(
        "binary_sensor.k98gidt45gul_name_ding"
    )
    assert binary_sensor_k98gidt45gul_name_ding.state == STATE_OFF
    new_time = dt_util.utcnow() + datetime.timedelta(seconds=40)
    native_time = datetime.datetime.now() + datetime.timedelta(seconds=40)
    with patch(
        "openpeerpower.components.august.binary_sensor._native_datetime",
        return_value=native_time,
    ):
        async_fire_time_changed(opp, new_time)
        await opp.async_block_till_done()
    binary_sensor_k98gidt45gul_name_motion = opp.states.get(
        "binary_sensor.k98gidt45gul_name_motion"
    )
    assert binary_sensor_k98gidt45gul_name_motion.state == STATE_OFF


async def test_doorbell_update_via_pubnub(opp):
    """Test creation of a doorbell that can be updated via pubnub."""
    doorbell_one = await _mock_doorbell_from_fixture(opp, "get_doorbell.json")
    pubnub = AugustPubNub()

    await _create_august_with_devices(opp, [doorbell_one], pubnub=pubnub)
    assert doorbell_one.pubsub_channel == "7c7a6672-59c8-3333-ffff-dcd98705cccc"

    binary_sensor_k98gidt45gul_name_motion = opp.states.get(
        "binary_sensor.k98gidt45gul_name_motion"
    )
    assert binary_sensor_k98gidt45gul_name_motion.state == STATE_OFF
    binary_sensor_k98gidt45gul_name_ding = opp.states.get(
        "binary_sensor.k98gidt45gul_name_ding"
    )
    assert binary_sensor_k98gidt45gul_name_ding.state == STATE_OFF

    pubnub.message(
        pubnub,
        Mock(
            channel=doorbell_one.pubsub_channel,
            timetoken=dt_util.utcnow().timestamp() * 10000000,
            message={
                "status": "imagecapture",
                "data": {
                    "result": {
                        "created_at": "2021-03-16T01:07:08.817Z",
                        "secure_url": "https://dyu7azbnaoi74.cloudfront.net/zip/images/zip.jpeg",
                    },
                },
            },
        ),
    )

    await opp.async_block_till_done()

    binary_sensor_k98gidt45gul_name_motion = opp.states.get(
        "binary_sensor.k98gidt45gul_name_motion"
    )
    assert binary_sensor_k98gidt45gul_name_motion.state == STATE_ON
    binary_sensor_k98gidt45gul_name_ding = opp.states.get(
        "binary_sensor.k98gidt45gul_name_ding"
    )
    assert binary_sensor_k98gidt45gul_name_ding.state == STATE_OFF

    new_time = dt_util.utcnow() + datetime.timedelta(seconds=40)
    native_time = datetime.datetime.now() + datetime.timedelta(seconds=40)
    with patch(
        "openpeerpower.components.august.binary_sensor._native_datetime",
        return_value=native_time,
    ):
        async_fire_time_changed(opp, new_time)
        await opp.async_block_till_done()

    binary_sensor_k98gidt45gul_name_motion = opp.states.get(
        "binary_sensor.k98gidt45gul_name_motion"
    )
    assert binary_sensor_k98gidt45gul_name_motion.state == STATE_OFF

    pubnub.message(
        pubnub,
        Mock(
            channel=doorbell_one.pubsub_channel,
            timetoken=dt_util.utcnow().timestamp() * 10000000,
            message={
                "status": "buttonpush",
            },
        ),
    )
    await opp.async_block_till_done()

    binary_sensor_k98gidt45gul_name_ding = opp.states.get(
        "binary_sensor.k98gidt45gul_name_ding"
    )
    assert binary_sensor_k98gidt45gul_name_ding.state == STATE_ON
    new_time = dt_util.utcnow() + datetime.timedelta(seconds=40)
    native_time = datetime.datetime.now() + datetime.timedelta(seconds=40)
    with patch(
        "openpeerpower.components.august.binary_sensor._native_datetime",
        return_value=native_time,
    ):
        async_fire_time_changed(opp, new_time)
        await opp.async_block_till_done()

    binary_sensor_k98gidt45gul_name_ding = opp.states.get(
        "binary_sensor.k98gidt45gul_name_ding"
    )
    assert binary_sensor_k98gidt45gul_name_ding.state == STATE_OFF


async def test_doorbell_device_registry(opp):
    """Test creation of a lock with doorsense and bridge ands up in the registry."""
    doorbell_one = await _mock_doorbell_from_fixture(opp, "get_doorbell.offline.json")
    await _create_august_with_devices(opp, [doorbell_one])

    device_registry = dr.async_get(opp)

    reg_device = device_registry.async_get_device(identifiers={("august", "tmt100")})
    assert reg_device.model == "hydra1"
    assert reg_device.name == "tmt100 Name"
    assert reg_device.manufacturer == "August Home Inc."
    assert reg_device.sw_version == "3.1.0-HYDRC75+201909251139"


async def test_door_sense_update_via_pubnub(opp):
    """Test creation of a lock with doorsense and bridge."""
    lock_one = await _mock_doorsense_enabled_august_lock_detail(opp)
    assert lock_one.pubsub_channel == "pubsub"
    pubnub = AugustPubNub()

    activities = await _mock_activities_from_fixture(opp, "get_activity.lock.json")
    config_entry = await _create_august_with_devices(
        opp, [lock_one], activities=activities, pubnub=pubnub
    )

    binary_sensor_online_with_doorsense_name = opp.states.get(
        "binary_sensor.online_with_doorsense_name_open"
    )
    assert binary_sensor_online_with_doorsense_name.state == STATE_ON

    pubnub.message(
        pubnub,
        Mock(
            channel=lock_one.pubsub_channel,
            timetoken=dt_util.utcnow().timestamp() * 10000000,
            message={"status": "kAugLockState_Unlocking", "doorState": "closed"},
        ),
    )

    await opp.async_block_till_done()
    binary_sensor_online_with_doorsense_name = opp.states.get(
        "binary_sensor.online_with_doorsense_name_open"
    )
    assert binary_sensor_online_with_doorsense_name.state == STATE_OFF

    pubnub.message(
        pubnub,
        Mock(
            channel=lock_one.pubsub_channel,
            timetoken=dt_util.utcnow().timestamp() * 10000000,
            message={"status": "kAugLockState_Locking", "doorState": "open"},
        ),
    )

    await opp.async_block_till_done()
    binary_sensor_online_with_doorsense_name = opp.states.get(
        "binary_sensor.online_with_doorsense_name_open"
    )
    assert binary_sensor_online_with_doorsense_name.state == STATE_ON

    async_fire_time_changed(opp, dt_util.utcnow() + datetime.timedelta(seconds=30))
    await opp.async_block_till_done()
    binary_sensor_online_with_doorsense_name = opp.states.get(
        "binary_sensor.online_with_doorsense_name_open"
    )
    assert binary_sensor_online_with_doorsense_name.state == STATE_ON

    pubnub.connected = True
    async_fire_time_changed(opp, dt_util.utcnow() + datetime.timedelta(seconds=30))
    await opp.async_block_till_done()
    binary_sensor_online_with_doorsense_name = opp.states.get(
        "binary_sensor.online_with_doorsense_name_open"
    )
    assert binary_sensor_online_with_doorsense_name.state == STATE_ON

    # Ensure pubnub status is always preserved
    async_fire_time_changed(opp, dt_util.utcnow() + datetime.timedelta(hours=2))
    await opp.async_block_till_done()
    binary_sensor_online_with_doorsense_name = opp.states.get(
        "binary_sensor.online_with_doorsense_name_open"
    )
    assert binary_sensor_online_with_doorsense_name.state == STATE_ON

    pubnub.message(
        pubnub,
        Mock(
            channel=lock_one.pubsub_channel,
            timetoken=dt_util.utcnow().timestamp() * 10000000,
            message={"status": "kAugLockState_Unlocking", "doorState": "open"},
        ),
    )
    await opp.async_block_till_done()
    binary_sensor_online_with_doorsense_name = opp.states.get(
        "binary_sensor.online_with_doorsense_name_open"
    )
    assert binary_sensor_online_with_doorsense_name.state == STATE_ON

    async_fire_time_changed(opp, dt_util.utcnow() + datetime.timedelta(hours=4))
    await opp.async_block_till_done()
    binary_sensor_online_with_doorsense_name = opp.states.get(
        "binary_sensor.online_with_doorsense_name_open"
    )
    assert binary_sensor_online_with_doorsense_name.state == STATE_ON

    await opp.config_entries.async_unload(config_entry.entry_id)
    await opp.async_block_till_done()
