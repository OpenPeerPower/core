"""Basic checks for HomeKitalarm_control_panel."""
from aiohomekit.model.characteristics import CharacteristicsTypes
from aiohomekit.model.services import ServicesTypes

from tests.components.homekit_controller.common import setup_test_component

CURRENT_STATE = ("security-system", "security-system-state.current")
TARGET_STATE = ("security-system", "security-system-state.target")


def create_security_system_service(accessory):
    """Define a security-system characteristics as per page 219 of HAP spec."""
    service = accessory.add_service(ServicesTypes.SECURITY_SYSTEM)

    cur_state = service.add_char(CharacteristicsTypes.SECURITY_SYSTEM_STATE_CURRENT)
    cur_state.value = 0

    targ_state = service.add_char(CharacteristicsTypes.SECURITY_SYSTEM_STATE_TARGET)
    targ_state.value = 0

    # According to the spec, a battery-level characteristic is normally
    # part of a separate service. However as the code was written (which
    # predates this test) the battery level would have to be part of the lock
    # service as it is here.
    targ_state = service.add_char(CharacteristicsTypes.BATTERY_LEVEL)
    targ_state.value = 50


async def test_switch_change_alarm_state.opp, utcnow):
    """Test that we can turn a HomeKit alarm on and off again."""
    helper = await setup_test_component.opp, create_security_system_service)

    await.opp.services.async_call(
        "alarm_control_panel",
        "alarm_arm_home",
        {"entity_id": "alarm_control_panel.testdevice"},
        blocking=True,
    )
    assert helper.characteristics[TARGET_STATE].value == 0

    await.opp.services.async_call(
        "alarm_control_panel",
        "alarm_arm_away",
        {"entity_id": "alarm_control_panel.testdevice"},
        blocking=True,
    )
    assert helper.characteristics[TARGET_STATE].value == 1

    await.opp.services.async_call(
        "alarm_control_panel",
        "alarm_arm_night",
        {"entity_id": "alarm_control_panel.testdevice"},
        blocking=True,
    )
    assert helper.characteristics[TARGET_STATE].value == 2

    await.opp.services.async_call(
        "alarm_control_panel",
        "alarm_disarm",
        {"entity_id": "alarm_control_panel.testdevice"},
        blocking=True,
    )
    assert helper.characteristics[TARGET_STATE].value == 3


async def test_switch_read_alarm_state.opp, utcnow):
    """Test that we can read the state of a HomeKit alarm accessory."""
    helper = await setup_test_component.opp, create_security_system_service)

    helper.characteristics[CURRENT_STATE].value = 0
    state = await helper.poll_and_get_state()
    assert state.state == "armed_home"
    assert state.attributes["battery_level"] == 50

    helper.characteristics[CURRENT_STATE].value = 1
    state = await helper.poll_and_get_state()
    assert state.state == "armed_away"

    helper.characteristics[CURRENT_STATE].value = 2
    state = await helper.poll_and_get_state()
    assert state.state == "armed_night"

    helper.characteristics[CURRENT_STATE].value = 3
    state = await helper.poll_and_get_state()
    assert state.state == "disarmed"

    helper.characteristics[CURRENT_STATE].value = 4
    state = await helper.poll_and_get_state()
    assert state.state == "triggered"
