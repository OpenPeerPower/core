"""Tests for the Risco alarm control panel device."""
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from openpeerpower.components.alarm_control_panel import DOMAIN as ALARM_DOMAIN
from openpeerpower.components.alarm_control_panel.const import (
    SUPPORT_ALARM_ARM_AWAY,
    SUPPORT_ALARM_ARM_CUSTOM_BYPASS,
    SUPPORT_ALARM_ARM_HOME,
    SUPPORT_ALARM_ARM_NIGHT,
)
from openpeerpower.components.risco import CannotConnectError, UnauthorizedError
from openpeerpower.components.risco.const import DOMAIN
from openpeerpower.const import (
    SERVICE_ALARM_ARM_AWAY,
    SERVICE_ALARM_ARM_CUSTOM_BYPASS,
    SERVICE_ALARM_ARM_HOME,
    SERVICE_ALARM_ARM_NIGHT,
    SERVICE_ALARM_DISARM,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_CUSTOM_BYPASS,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMING,
    STATE_ALARM_DISARMED,
    STATE_ALARM_TRIGGERED,
    STATE_UNKNOWN,
)
from openpeerpower.helpers.entity_component import async_update_entity

from .util import TEST_CONFIG, TEST_SITE_UUID, setup_risco

from tests.common import MockConfigEntry

FIRST_ENTITY_ID = "alarm_control_panel.risco_test_site_name_partition_0"
SECOND_ENTITY_ID = "alarm_control_panel.risco_test_site_name_partition_1"

CODES_REQUIRED_OPTIONS = {"code_arm_required": True, "code_disarm_required": True}
TEST_RISCO_TO_HA = {
    "arm": STATE_ALARM_ARMED_AWAY,
    "partial_arm": STATE_ALARM_ARMED_HOME,
    "A": STATE_ALARM_ARMED_HOME,
    "B": STATE_ALARM_ARMED_HOME,
    "C": STATE_ALARM_ARMED_NIGHT,
    "D": STATE_ALARM_ARMED_NIGHT,
}
TEST_FULL_RISCO_TO_HA = {
    **TEST_RISCO_TO_HA,
    "D": STATE_ALARM_ARMED_CUSTOM_BYPASS,
}
TEST_OP_TO_RISCO = {
    STATE_ALARM_ARMED_AWAY: "arm",
    STATE_ALARM_ARMED_HOME: "partial_arm",
    STATE_ALARM_ARMED_NIGHT: "C",
}
TEST_FULL_OP_TO_RISCO = {
    **TEST_OP_TO_RISCO,
    STATE_ALARM_ARMED_CUSTOM_BYPASS: "D",
}
CUSTOM_MAPPING_OPTIONS = {
    "risco_states_to_ha": TEST_RISCO_TO_HA,
    "ha_states_to_risco": TEST_OP_TO_RISCO,
}

FULL_CUSTOM_MAPPING = {
    "risco_states_to_ha": TEST_FULL_RISCO_TO_HA,
    "ha_states_to_risco": TEST_FULL_OP_TO_RISCO,
}

EXPECTED_FEATURES = (
    SUPPORT_ALARM_ARM_AWAY | SUPPORT_ALARM_ARM_HOME | SUPPORT_ALARM_ARM_NIGHT
)


def _partition_mock():
    return MagicMock(
        triggered=False,
        arming=False,
        armed=False,
        disarmed=False,
        partially_armed=False,
    )


@pytest.fixture
def two_part_alarm():
    """Fixture to mock alarm with two partitions."""
    partition_mocks = {0: _partition_mock(), 1: _partition_mock()}
    alarm_mock = MagicMock()
    with patch.object(
        partition_mocks[0], "id", new_callable=PropertyMock(return_value=0)
    ), patch.object(
        partition_mocks[1], "id", new_callable=PropertyMock(return_value=1)
    ), patch.object(
        alarm_mock,
        "partitions",
        new_callable=PropertyMock(return_value=partition_mocks),
    ), patch(
        "openpeerpower.components.risco.RiscoAPI.get_state",
        return_value=alarm_mock,
    ):
        yield alarm_mock


async def test_cannot_connect.opp):
    """Test connection error."""

    with patch(
        "openpeerpower.components.risco.RiscoAPI.login",
        side_effect=CannotConnectError,
    ):
        config_entry = MockConfigEntry(domain=DOMAIN, data=TEST_CONFIG)
        config_entry.add_to.opp.opp)
        await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()
        registry = await opp.helpers.entity_registry.async_get_registry()
        assert not registry.async_is_registered(FIRST_ENTITY_ID)
        assert not registry.async_is_registered(SECOND_ENTITY_ID)


async def test_unauthorized.opp):
    """Test unauthorized error."""

    with patch(
        "openpeerpower.components.risco.RiscoAPI.login",
        side_effect=UnauthorizedError,
    ):
        config_entry = MockConfigEntry(domain=DOMAIN, data=TEST_CONFIG)
        config_entry.add_to.opp.opp)
        await opp.config_entries.async_setup(config_entry.entry_id)
        await opp.async_block_till_done()
        registry = await opp.helpers.entity_registry.async_get_registry()
        assert not registry.async_is_registered(FIRST_ENTITY_ID)
        assert not registry.async_is_registered(SECOND_ENTITY_ID)


async def test_setup_opp, two_part_alarm):
    """Test entity setup."""
    registry = await opp.helpers.entity_registry.async_get_registry()

    assert not registry.async_is_registered(FIRST_ENTITY_ID)
    assert not registry.async_is_registered(SECOND_ENTITY_ID)

    await setup_risco.opp)

    assert registry.async_is_registered(FIRST_ENTITY_ID)
    assert registry.async_is_registered(SECOND_ENTITY_ID)

    registry = await opp.helpers.device_registry.async_get_registry()
    device = registry.async_get_device({(DOMAIN, TEST_SITE_UUID + "_0")})
    assert device is not None
    assert device.manufacturer == "Risco"

    device = registry.async_get_device({(DOMAIN, TEST_SITE_UUID + "_1")})
    assert device is not None
    assert device.manufacturer == "Risco"


async def _check_state.opp, alarm, property, state, entity_id, partition_id):
    with patch.object(alarm.partitions[partition_id], property, return_value=True):
        await async_update_entity.opp, entity_id)
        await opp.async_block_till_done()

        assert.opp.states.get(entity_id).state == state


async def test_states.opp, two_part_alarm):
    """Test the various alarm states."""
    await setup_risco.opp, [], CUSTOM_MAPPING_OPTIONS)

    assert.opp.states.get(FIRST_ENTITY_ID).state == STATE_UNKNOWN
    for partition_id, entity_id in {0: FIRST_ENTITY_ID, 1: SECOND_ENTITY_ID}.items():
        await _check_state(
            opp,
            two_part_alarm,
            "triggered",
            STATE_ALARM_TRIGGERED,
            entity_id,
            partition_id,
        )
        await _check_state(
            opp, two_part_alarm, "arming", STATE_ALARM_ARMING, entity_id, partition_id
        )
        await _check_state(
            opp,
            two_part_alarm,
            "armed",
            STATE_ALARM_ARMED_AWAY,
            entity_id,
            partition_id,
        )
        await _check_state(
            opp,
            two_part_alarm,
            "partially_armed",
            STATE_ALARM_ARMED_HOME,
            entity_id,
            partition_id,
        )
        await _check_state(
            opp,
            two_part_alarm,
            "disarmed",
            STATE_ALARM_DISARMED,
            entity_id,
            partition_id,
        )

        groups = {"A": False, "B": False, "C": True, "D": False}
        with patch.object(
            two_part_alarm.partitions[partition_id],
            "groups",
            new_callable=PropertyMock(return_value=groups),
        ):
            await _check_state(
                opp,
                two_part_alarm,
                "partially_armed",
                STATE_ALARM_ARMED_NIGHT,
                entity_id,
                partition_id,
            )


async def _test_service_call(
    opp, service, method, entity_id, partition_id, *args, **kwargs
):
    with patch(f"openpeerpower.components.risco.RiscoAPI.{method}") as set_mock:
        await _call_alarm_service.opp, service, entity_id, **kwargs)
        set_mock.assert_awaited_once_with(partition_id, *args)


async def _test_no_service_call(
    opp, service, method, entity_id, partition_id, **kwargs
):
    with patch(f"openpeerpower.components.risco.RiscoAPI.{method}") as set_mock:
        await _call_alarm_service.opp, service, entity_id, **kwargs)
        set_mock.assert_not_awaited()


async def _call_alarm_service.opp, service, entity_id, **kwargs):
    data = {"entity_id": entity_id, **kwargs}

    await opp.services.async_call(
        ALARM_DOMAIN, service, service_data=data, blocking=True
    )


async def test_sets_custom_mapping.opp, two_part_alarm):
    """Test settings the various modes when mapping some states."""
    await setup_risco.opp, [], CUSTOM_MAPPING_OPTIONS)

    registry = await opp.helpers.entity_registry.async_get_registry()
    entity = registry.async_get(FIRST_ENTITY_ID)
    assert entity.supported_features == EXPECTED_FEATURES

    await _test_service_call.opp, SERVICE_ALARM_DISARM, "disarm", FIRST_ENTITY_ID, 0)
    await _test_service_call.opp, SERVICE_ALARM_DISARM, "disarm", SECOND_ENTITY_ID, 1)
    await _test_service_call.opp, SERVICE_ALARM_ARM_AWAY, "arm", FIRST_ENTITY_ID, 0)
    await _test_service_call.opp, SERVICE_ALARM_ARM_AWAY, "arm", SECOND_ENTITY_ID, 1)
    await _test_service_call(
        opp, SERVICE_ALARM_ARM_HOME, "partial_arm", FIRST_ENTITY_ID, 0
    )
    await _test_service_call(
        opp, SERVICE_ALARM_ARM_HOME, "partial_arm", SECOND_ENTITY_ID, 1
    )
    await _test_service_call(
        opp, SERVICE_ALARM_ARM_NIGHT, "group_arm", FIRST_ENTITY_ID, 0, "C"
    )
    await _test_service_call(
        opp, SERVICE_ALARM_ARM_NIGHT, "group_arm", SECOND_ENTITY_ID, 1, "C"
    )


async def test_sets_full_custom_mapping.opp, two_part_alarm):
    """Test settings the various modes when mapping all states."""
    await setup_risco.opp, [], FULL_CUSTOM_MAPPING)

    registry = await opp.helpers.entity_registry.async_get_registry()
    entity = registry.async_get(FIRST_ENTITY_ID)
    assert (
        entity.supported_features == EXPECTED_FEATURES | SUPPORT_ALARM_ARM_CUSTOM_BYPASS
    )

    await _test_service_call.opp, SERVICE_ALARM_DISARM, "disarm", FIRST_ENTITY_ID, 0)
    await _test_service_call.opp, SERVICE_ALARM_DISARM, "disarm", SECOND_ENTITY_ID, 1)
    await _test_service_call.opp, SERVICE_ALARM_ARM_AWAY, "arm", FIRST_ENTITY_ID, 0)
    await _test_service_call.opp, SERVICE_ALARM_ARM_AWAY, "arm", SECOND_ENTITY_ID, 1)
    await _test_service_call(
        opp, SERVICE_ALARM_ARM_HOME, "partial_arm", FIRST_ENTITY_ID, 0
    )
    await _test_service_call(
        opp, SERVICE_ALARM_ARM_HOME, "partial_arm", SECOND_ENTITY_ID, 1
    )
    await _test_service_call(
        opp, SERVICE_ALARM_ARM_NIGHT, "group_arm", FIRST_ENTITY_ID, 0, "C"
    )
    await _test_service_call(
        opp, SERVICE_ALARM_ARM_NIGHT, "group_arm", SECOND_ENTITY_ID, 1, "C"
    )
    await _test_service_call(
        opp, SERVICE_ALARM_ARM_CUSTOM_BYPASS, "group_arm", FIRST_ENTITY_ID, 0, "D"
    )
    await _test_service_call(
        opp, SERVICE_ALARM_ARM_CUSTOM_BYPASS, "group_arm", SECOND_ENTITY_ID, 1, "D"
    )


async def test_sets_with_correct_code.opp, two_part_alarm):
    """Test settings the various modes when code is required."""
    await setup_risco.opp, [], {**CUSTOM_MAPPING_OPTIONS, **CODES_REQUIRED_OPTIONS})

    code = {"code": 1234}
    await _test_service_call(
        opp, SERVICE_ALARM_DISARM, "disarm", FIRST_ENTITY_ID, 0, **code
    )
    await _test_service_call(
        opp, SERVICE_ALARM_DISARM, "disarm", SECOND_ENTITY_ID, 1, **code
    )
    await _test_service_call(
        opp, SERVICE_ALARM_ARM_AWAY, "arm", FIRST_ENTITY_ID, 0, **code
    )
    await _test_service_call(
        opp, SERVICE_ALARM_ARM_AWAY, "arm", SECOND_ENTITY_ID, 1, **code
    )
    await _test_service_call(
        opp, SERVICE_ALARM_ARM_HOME, "partial_arm", FIRST_ENTITY_ID, 0, **code
    )
    await _test_service_call(
        opp, SERVICE_ALARM_ARM_HOME, "partial_arm", SECOND_ENTITY_ID, 1, **code
    )
    await _test_service_call(
        opp, SERVICE_ALARM_ARM_NIGHT, "group_arm", FIRST_ENTITY_ID, 0, "C", **code
    )
    await _test_service_call(
        opp, SERVICE_ALARM_ARM_NIGHT, "group_arm", SECOND_ENTITY_ID, 1, "C", **code
    )
    await _test_no_service_call(
        opp, SERVICE_ALARM_ARM_CUSTOM_BYPASS, "partial_arm", FIRST_ENTITY_ID, 0, **code
    )
    await _test_no_service_call(
        opp,
        SERVICE_ALARM_ARM_CUSTOM_BYPASS,
        "partial_arm",
        SECOND_ENTITY_ID,
        1,
        **code,
    )


async def test_sets_with_incorrect_code.opp, two_part_alarm):
    """Test settings the various modes when code is required and incorrect."""
    await setup_risco.opp, [], {**CUSTOM_MAPPING_OPTIONS, **CODES_REQUIRED_OPTIONS})

    code = {"code": 4321}
    await _test_no_service_call(
        opp, SERVICE_ALARM_DISARM, "disarm", FIRST_ENTITY_ID, 0, **code
    )
    await _test_no_service_call(
        opp, SERVICE_ALARM_DISARM, "disarm", SECOND_ENTITY_ID, 1, **code
    )
    await _test_no_service_call(
        opp, SERVICE_ALARM_ARM_AWAY, "arm", FIRST_ENTITY_ID, 0, **code
    )
    await _test_no_service_call(
        opp, SERVICE_ALARM_ARM_AWAY, "arm", SECOND_ENTITY_ID, 1, **code
    )
    await _test_no_service_call(
        opp, SERVICE_ALARM_ARM_HOME, "partial_arm", FIRST_ENTITY_ID, 0, **code
    )
    await _test_no_service_call(
        opp, SERVICE_ALARM_ARM_HOME, "partial_arm", SECOND_ENTITY_ID, 1, **code
    )
    await _test_no_service_call(
        opp, SERVICE_ALARM_ARM_NIGHT, "group_arm", FIRST_ENTITY_ID, 0, **code
    )
    await _test_no_service_call(
        opp, SERVICE_ALARM_ARM_NIGHT, "group_arm", SECOND_ENTITY_ID, 1, **code
    )
    await _test_no_service_call(
        opp, SERVICE_ALARM_ARM_CUSTOM_BYPASS, "partial_arm", FIRST_ENTITY_ID, 0, **code
    )
    await _test_no_service_call(
        opp,
        SERVICE_ALARM_ARM_CUSTOM_BYPASS,
        "partial_arm",
        SECOND_ENTITY_ID,
        1,
        **code,
    )
